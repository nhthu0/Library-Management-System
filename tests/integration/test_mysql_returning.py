import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier

import mysql.connector
import pytest

from app.controllers.borrowing_controller import BorrowingController
from app.services.borrowing_service import BorrowingService
from tests.integration.test_mysql_borrowing import mysql_case


pytestmark = pytest.mark.skipif(
    os.environ.get("TV4_MYSQL_TESTS") != "1",
    reason="Start the isolated MySQL container and set TV4_MYSQL_TESTS=1.",
)


def saved_record(case, borrowing_id):
    return case["sql"](
        "SELECT status, return_date FROM borrowing_records WHERE borrowingID=%s",
        (borrowing_id,),
    )[0]


def test_real_return_preserves_stock_and_unreturned_details(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 2)
    result = case["controller"].request_return(borrowing_id)
    assert result["success"], result
    assert result["data"]["reader_id"] == case["readers"][0]
    assert result["data"]["quantity"] == 2
    assert saved_record(case, borrowing_id) == ("ReturnRequested", None)
    assert case["sql"](
        "SELECT return_date FROM borrowing_details WHERE borrowingID=%s",
        (borrowing_id,),
    ) == [(None,), (None,)]
    assert case["sql"](
        "SELECT quantity FROM books WHERE bookID=%s", (case["book_id"],)
    ) == [(3,)]
    assert case["repository"].count_active_books(case["readers"][0]) == 2
    assert case["repository"].count_active_copies_for_book(case["book_id"]) == 2


def test_real_return_cannot_target_another_reader(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][1], "Borrowed", 1)
    result = case["controller"].request_return(borrowing_id)
    assert result["success"] is False and result["data"] is None
    assert saved_record(case, borrowing_id) == ("Borrowed", None)


def test_real_return_rejects_missing_record(mysql_case):
    result = mysql_case["controller"].request_return(2147483647)
    assert result["success"] is False and result["data"] is None


@pytest.mark.parametrize("status", ["Pending", "ReturnRequested", "Returned"])
def test_real_return_rejects_invalid_states(mysql_case, status):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], status, 1)
    before = saved_record(case, borrowing_id)
    assert case["controller"].request_return(borrowing_id)["success"] is False
    assert saved_record(case, borrowing_id) == before


def test_real_return_reports_overdue_days(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 1)
    case["sql"]("UPDATE borrowing_records SET due_date=%s WHERE borrowingID=%s",
                ("2026-11-15", borrowing_id))
    result = case["controller"].request_return(borrowing_id)
    assert result["success"], result
    assert result["data"]["days_overdue"] == 3
    assert "overdue" in result["message"]


def test_duplicate_requests_are_serialized_on_real_mysql(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 1)
    barrier = Barrier(2)

    def send():
        barrier.wait(timeout=5)
        return case["controller"].request_return(borrowing_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert sum(result["success"] for result in results) == 1, results
    assert saved_record(case, borrowing_id) == ("ReturnRequested", None)


def test_real_transaction_rolls_back_if_commit_fails(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 1)
    factory = case["repository"]._get_connection

    class FailingCommit:
        def __init__(self):
            self.connection = factory()

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def commit(self):
            raise mysql.connector.OperationalError("Simulated commit failure")

    service = BorrowingService(
        borrowing_repository=case["repository"],
        connection_factory=FailingCommit,
        today_provider=lambda: date(2026, 11, 18),
    )
    controller = BorrowingController(
        current_user={"user_id": case["users"][0], "role": "READER"},
        service=service,
    )
    result = controller.request_return(borrowing_id)
    assert result["success"] is False and result["data"] is None
    assert saved_record(case, borrowing_id) == ("Borrowed", None)


@pytest.mark.parametrize("borrowing_id", [0, True, "20"])
def test_real_return_rejects_invalid_ids(mysql_case, borrowing_id):
    result = mysql_case["controller"].request_return(borrowing_id)
    assert result["success"] is False and result["data"] is None
    assert mysql_case["request_count"]() == 0


def test_real_return_rejects_admin_session(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 1)
    case["controller"].current_user["role"] = "ADMIN"
    assert case["controller"].request_return(borrowing_id)["success"] is False
    assert saved_record(case, borrowing_id) == ("Borrowed", None)


def test_real_return_rechecks_locked_account(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 1)
    case["sql"]("UPDATE users SET account_status=%s WHERE userID=%s",
                ("Locked", case["users"][0]))
    assert case["controller"].request_return(borrowing_id)["success"] is False
    assert saved_record(case, borrowing_id) == ("Borrowed", None)


def test_real_return_allows_expired_membership(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 1)
    case["sql"]("UPDATE readers SET expiration_date=%s WHERE readerID=%s",
                ("2026-11-17", case["readers"][0]))
    result = case["controller"].request_return(borrowing_id)
    assert result["success"], result


def test_real_return_rejects_invalid_due_date(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 1)
    case["sql"]("UPDATE borrowing_records SET due_date=%s WHERE borrowingID=%s",
                ("bad-date", borrowing_id))
    result = case["controller"].request_return(borrowing_id)
    assert result["success"] is False and result["data"] is None
    assert saved_record(case, borrowing_id) == ("Borrowed", None)

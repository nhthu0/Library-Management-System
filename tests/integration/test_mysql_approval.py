import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from uuid import uuid4

import mysql.connector
import pytest

from app.controllers.borrowing_controller import BorrowingController
from app.services.borrowing_service import BorrowingService
from tests.integration.test_mysql_borrowing import mysql_case


pytestmark = pytest.mark.skipif(
    os.environ.get("TV4_MYSQL_TESTS") != "1",
    reason="Start the isolated MySQL container and set TV4_MYSQL_TESTS=1.",
)


@pytest.fixture
def approval_case(mysql_case):
    case = mysql_case
    name = "admin_" + uuid4().hex[:12]
    user_id = case["sql"](
        """INSERT INTO users (username, full_name, email, password, role, account_status)
           VALUES (%s,%s,%s,%s,%s,%s)""",
        (name, "Approval Test", name + "@example.invalid", "test-only", "Admin", "Active"),
    )
    admin_id = None
    try:
        admin_id = case["sql"]("INSERT INTO admins (userID) VALUES (%s)", (user_id,))
        case["admin_user_id"], case["admin_id"] = user_id, admin_id
        case["controller"].current_user = {"user_id": user_id, "role": "ADMIN", "admin_id": -1}
        yield case
    finally:
        if admin_id is not None:
            case["sql"]("UPDATE borrowing_records SET adminID=NULL WHERE adminID=%s", (admin_id,))
            case["sql"]("DELETE FROM admins WHERE adminID=%s", (admin_id,))
        case["sql"]("DELETE FROM users WHERE userID=%s", (user_id,))


def stored(case, borrowing_id):
    return case["sql"](
        "SELECT status, adminID, borrow_date, due_date FROM borrowing_records WHERE borrowingID=%s",
        (borrowing_id,),
    )[0]


def test_pending_queue_returns_empty_list_and_only_pending_requests(approval_case):
    case = approval_case
    empty = case["controller"].get_pending_borrow_requests()
    assert empty["success"] and empty["data"] == []
    first = case["seed_loan"](case["readers"][0], "Pending", 2)
    second = case["seed_loan"](case["readers"][1], "Pending", 1)
    case["seed_loan"](case["readers"][0], "Borrowed", 1)
    result = case["controller"].get_pending_borrow_requests()
    assert result["success"], result
    assert [row["borrowing_id"] for row in result["data"]] == [first, second]
    assert [row["quantity"] for row in result["data"]] == [2, 1]
    assert all(row["reader_name"] and row["status"] == "Pending" for row in result["data"])


def test_approval_records_admin_and_actual_dates_and_reduces_available_copies(approval_case):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 2)
    result = case["controller"].approve_borrow(borrowing_id)
    assert result["success"], result
    assert stored(case, borrowing_id) == ("Borrowed", case["admin_id"], "2026-11-18", "2026-11-28")
    assert result["data"]["admin_id"] == case["admin_id"]
    assert case["repository"].count_active_copies_for_book(case["book_id"]) == 2
    assert case["repository"].count_active_books(case["readers"][0]) == 2
    assert case["sql"]("SELECT quantity FROM books WHERE bookID=%s", (case["book_id"],)) == [(3,)]


def test_rejection_does_not_require_loan_policy_or_reserve_stock(approval_case):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 2)
    case["controller"].service.loan_period_days = None
    result = case["controller"].reject_borrow(borrowing_id)
    assert result["success"], result
    assert stored(case, borrowing_id) == ("Rejected", case["admin_id"], "2026-11-01", "2026-11-20")
    assert case["repository"].count_active_copies_for_book(case["book_id"]) == 0


def test_approving_last_copies_marks_book_unavailable(approval_case):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 3)
    result = case["controller"].approve_borrow(borrowing_id)
    assert result["success"], result
    assert case["sql"]("SELECT quantity, status FROM books WHERE bookID=%s",
                       (case["book_id"],)) == [(3, "Unavailable")]


@pytest.mark.parametrize("action", ["approve_borrow", "reject_borrow", "get_pending_borrow_requests"])
def test_reader_cannot_use_admin_actions(approval_case, action):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 1)
    case["controller"].current_user = {"user_id": case["users"][0], "role": "READER"}
    method = getattr(case["controller"], action)
    result = method() if action.startswith("get_") else method(borrowing_id)
    assert result["success"] is False and result["data"] is None
    assert stored(case, borrowing_id)[0] == "Pending"


@pytest.mark.parametrize("field, value", [("role", "Reader"), ("account_status", "Locked")])
def test_admin_database_permissions_are_rechecked(approval_case, field, value):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 1)
    if field == "role":
        case["sql"]("UPDATE users SET role=%s WHERE userID=%s", (value, case["admin_user_id"]))
    else:
        case["sql"]("UPDATE users SET account_status=%s WHERE userID=%s", (value, case["admin_user_id"]))
    result = case["controller"].approve_borrow(borrowing_id)
    assert result["success"] is False and result["data"] is None
    assert stored(case, borrowing_id)[0] == "Pending"


@pytest.mark.parametrize("borrowing_id", [0, True, "1 OR 1=1", 2147483647])
def test_invalid_or_missing_requests_are_rejected(approval_case, borrowing_id):
    result = approval_case["controller"].approve_borrow(borrowing_id)
    assert result["success"] is False and result["data"] is None


@pytest.mark.parametrize("status", ["Borrowed", "ReturnRequested", "Returned", "Rejected"])
def test_processed_requests_cannot_be_approved_or_rejected_again(approval_case, status):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], status, 1)
    before = stored(case, borrowing_id)
    assert case["controller"].approve_borrow(borrowing_id)["success"] is False
    assert case["controller"].reject_borrow(borrowing_id)["success"] is False
    assert stored(case, borrowing_id) == before


@pytest.mark.parametrize("failure", ["expired", "locked", "limit", "unavailable", "stock", "policy", "empty"])
def test_failed_approval_keeps_the_request_pending(approval_case, failure):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 2)
    if failure == "expired":
        case["sql"]("UPDATE readers SET expiration_date=%s WHERE readerID=%s",
                    ("2026-11-17", case["readers"][0]))
    elif failure == "locked":
        case["sql"]("UPDATE users SET account_status=%s WHERE userID=%s", ("Locked", case["users"][0]))
    elif failure == "limit":
        case["seed_loan"](case["readers"][0], "Borrowed", 2)
    elif failure == "unavailable":
        case["sql"]("UPDATE books SET status=%s WHERE bookID=%s", ("Unavailable", case["book_id"]))
    elif failure == "stock":
        case["seed_loan"](case["readers"][1], "ReturnRequested", 2)
    elif failure == "policy":
        case["controller"].service.loan_period_days = None
    else:
        case["sql"]("DELETE FROM borrowing_details WHERE borrowingID=%s", (borrowing_id,))
    result = case["controller"].approve_borrow(borrowing_id)
    assert result["success"] is False and result["data"] is None
    assert stored(case, borrowing_id) == ("Pending", None, "2026-11-01", "2026-11-20")


def test_approval_rolls_back_on_commit_failure(approval_case):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 3)
    factory = case["repository"]._get_connection

    class FailCommit:
        def __init__(self):
            self.connection = factory()

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def commit(self):
            raise mysql.connector.OperationalError("private commit failure")

    service = BorrowingService(
        borrowing_repository=case["repository"], connection_factory=FailCommit,
        loan_period_days=10, today_provider=lambda: date(2026, 11, 18),
    )
    controller = BorrowingController(current_user=case["controller"].current_user, service=service)
    result = controller.approve_borrow(borrowing_id)
    assert result["success"] is False and result["data"] is None
    assert "private" not in result["message"]
    assert stored(case, borrowing_id) == ("Pending", None, "2026-11-01", "2026-11-20")
    assert case["repository"].count_active_copies_for_book(case["book_id"]) == 0
    assert case["sql"]("SELECT status FROM books WHERE bookID=%s",
                       (case["book_id"],)) == [("Available",)]


@pytest.mark.parametrize("second_action", ["approve_borrow", "reject_borrow"])
def test_concurrent_decisions_process_a_request_once(approval_case, second_action):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 1)
    barrier = Barrier(2)

    def send(action):
        barrier.wait(timeout=5)
        return getattr(case["controller"], action)(borrowing_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, action) for action in ("approve_borrow", second_action)]
        results = [future.result(timeout=15) for future in futures]
    assert sum(item["success"] for item in results) == 1, results
    status = stored(case, borrowing_id)[0]
    assert status in {"Borrowed", "Rejected"}
    assert case["repository"].count_active_books(case["readers"][0]) == (1 if status == "Borrowed" else 0)


def test_concurrent_readers_cannot_exceed_available_copies(approval_case, monkeypatch):
    case = approval_case
    ids = [case["seed_loan"](reader, "Pending", 2) for reader in case["readers"]]
    barrier = Barrier(2)
    original = case["repository"].get_request_books

    def read_before_lock(borrowing_id, connection):
        rows = original(borrowing_id, connection)
        barrier.wait(timeout=5)
        return rows

    monkeypatch.setattr(case["repository"], "get_request_books", read_before_lock)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(case["controller"].approve_borrow, borrowing_id) for borrowing_id in ids]
        results = [future.result(timeout=15) for future in futures]
    assert sum(item["success"] for item in results) == 1, results
    assert case["repository"].count_active_copies_for_book(case["book_id"]) == 2
    assert sorted(stored(case, item)[0] for item in ids) == ["Borrowed", "Pending"]


def test_concurrent_approvals_cannot_exceed_reader_limit(approval_case):
    case = approval_case
    case["sql"]("UPDATE books SET quantity=10 WHERE bookID=%s", (case["book_id"],))
    case["seed_loan"](case["readers"][0], "Borrowed", 2)
    ids = [case["seed_loan"](case["readers"][0], "Pending", 1) for _ in range(2)]
    barrier = Barrier(2)

    def send(borrowing_id):
        barrier.wait(timeout=5)
        return case["controller"].approve_borrow(borrowing_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result(timeout=15) for future in [pool.submit(send, item) for item in ids]]
    assert sum(item["success"] for item in results) == 1, results
    assert case["repository"].count_active_books(case["readers"][0]) == 3

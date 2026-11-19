"""Admin returns, shared inventory, and overdue charges on isolated MySQL 8."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier

import mysql.connector
import pytest

from app.controllers.borrowing_controller import BorrowingController
from app.services.book_service import BookService
from app.services.borrowing_service import BorrowingService
from tests.integration.test_mysql_approval import approval_case
from tests.integration.test_mysql_borrowing import mysql_case


pytestmark = pytest.mark.skipif(
    os.environ.get("TV4_MYSQL_TESTS") != "1",
    reason="Start the isolated MySQL container and set TV4_MYSQL_TESTS=1.",
)


@pytest.fixture
def completion_case(approval_case):
    case = approval_case
    try:
        yield case
    finally:
        for reader_id in case["readers"]:
            case["sql"](
                """DELETE f FROM fines AS f JOIN borrowing_records AS r
                   ON r.borrowingID = f.borrowingID WHERE r.readerID = %s""",
                (reader_id,),
            )


def fine_rows(case, borrowing_id):
    return case["sql"](
        """SELECT amount, payment_status, reason FROM fines
           WHERE borrowingID=%s ORDER BY fineID""", (borrowing_id,),
    )


def record_state(case, borrowing_id):
    return case["sql"](
        "SELECT status, return_date FROM borrowing_records WHERE borrowingID=%s",
        (borrowing_id,),
    )[0]


def add_charge(case, borrowing_id, amount, status="Unpaid", reason="Overdue return"):
    return case["sql"](
        """INSERT INTO fines
           (borrowingID, amount, reason, fine_date, payment_status, payment_date)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (borrowing_id, amount, reason, "2026-11-16", status,
         "2026-11-16" if status == "Paid" else None),
    )


def test_reader_and_admin_borrow_and_return_workflows(completion_case):
    case = completion_case
    admin = case["controller"]
    reader = BorrowingController(
        current_user={"user_id": case["users"][0], "role": "READER"}, service=admin.service,
    )
    request = reader.request_borrow(case["book_id"], 2)
    assert request["success"], request
    borrowing_id = request["data"]["borrowing_id"]
    assert admin.get_pending_borrow_requests()["data"][0]["borrowing_id"] == borrowing_id
    assert admin.approve_borrow(borrowing_id)["success"]
    assert reader.get_my_borrowing_history()["data"][0]["status"] == "Borrowed"
    assert reader.request_return(borrowing_id)["success"]
    assert admin.get_pending_return_requests()["data"][0]["borrowing_id"] == borrowing_id
    assert admin.confirm_return(borrowing_id)["success"]
    assert reader.get_my_borrowing_history()["data"][0]["returned_quantity"] == 2
    other = reader.request_borrow(case["book_id"], 1)
    assert other["success"]
    assert admin.reject_borrow(other["data"]["borrowing_id"])["success"]
    assert BookService().check_book_availability(case["book_id"])["available_quantity"] == 3


def test_return_updates_header_details_and_availability_without_changing_total(completion_case):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "ReturnRequested", 2)
    case["sql"]("UPDATE books SET status='Unavailable' WHERE bookID=%s", (case["book_id"],))
    result = case["controller"].confirm_return(borrowing_id)
    assert result["success"], result
    assert record_state(case, borrowing_id) == ("Returned", "2026-11-18")
    assert case["sql"]("SELECT return_date FROM borrowing_details WHERE borrowingID=%s",
                       (borrowing_id,)) == [("2026-11-18",)] * 2
    assert case["sql"]("SELECT quantity, status FROM books WHERE bookID=%s",
                       (case["book_id"],)) == [(3, "Available")]
    assert result["data"]["quantity"] == 2 and result["data"]["fine_amount"] == 0
    assert result["data"]["admin_id"] == case["admin_id"]
    assert case["repository"].count_active_books(case["readers"][0]) == 0
    assert not fine_rows(case, borrowing_id)
    assert not case["controller"].confirm_return(borrowing_id)["success"]


def test_estimate_and_final_fine_use_request_and_actual_receipt_dates(completion_case):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 2)
    case["sql"]("UPDATE borrowing_records SET due_date='2026-11-15' WHERE borrowingID=%s",
                (borrowing_id,))
    service = BorrowingService(
        borrowing_repository=case["repository"],
        connection_factory=case["repository"]._get_connection,
        today_provider=lambda: date(2026, 11, 16),
    )
    reader = BorrowingController(
        current_user={"user_id": case["users"][0], "role": "READER"}, service=service,
    )
    requested = reader.request_return(borrowing_id)
    assert requested["success"] and requested["data"]["estimated_fine"] == 4000
    assert not fine_rows(case, borrowing_id)
    result = case["controller"].confirm_return(borrowing_id)
    assert result["success"], result
    assert result["data"]["days_overdue"] == 3
    assert result["data"]["fine_amount"] == result["data"]["unpaid_amount"] == 12000
    assert fine_rows(case, borrowing_id) == [(12000, "Unpaid", "Overdue return")]
    assert json.loads(json.dumps(result))["data"]["fine_amount"] == 12000


def test_partial_returns_keep_their_dates_and_paid_charges(completion_case):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "ReturnRequested", 3)
    case["sql"]("UPDATE borrowing_records SET due_date='2026-11-15' WHERE borrowingID=%s",
                (borrowing_id,))
    case["sql"]("""UPDATE borrowing_details SET return_date='2026-11-16'
                  WHERE borrowingID=%s ORDER BY detailID LIMIT 1""", (borrowing_id,))
    paid_id = add_charge(case, borrowing_id, 2000, "Paid")
    add_charge(case, borrowing_id, 4000)
    add_charge(case, borrowing_id, 5000, reason="Damaged cover")
    result = case["controller"].confirm_return(borrowing_id)
    assert result["success"], result
    assert result["data"]["quantity"] == 2 and result["data"]["fine_amount"] == 14000
    assert result["data"]["unpaid_amount"] == 12000
    assert case["sql"]("SELECT amount, payment_status, payment_date FROM fines WHERE fineID=%s",
                       (paid_id,)) == [(2000, "Paid", "2026-11-16")]
    assert fine_rows(case, borrowing_id) == [
        (2000, "Paid", "Overdue return"), (12000, "Unpaid", "Overdue return"),
        (5000, "Unpaid", "Damaged cover"),
    ]
    assert case["sql"]("SELECT return_date FROM borrowing_details WHERE borrowingID=%s ORDER BY detailID",
                       (borrowing_id,)) == [("2026-11-16",), ("2026-11-18",), ("2026-11-18",)]


@pytest.mark.parametrize("failure", ["fine", "inventory", "commit"])
def test_return_failure_rolls_back_dates_fines_and_stock(completion_case, monkeypatch, failure):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "ReturnRequested", 3)
    case["sql"]("UPDATE borrowing_records SET due_date='2026-11-15' WHERE borrowingID=%s", (borrowing_id,))
    case["sql"]("UPDATE books SET status='Unavailable' WHERE bookID=%s", (case["book_id"],))
    if failure == "commit":
        factory = case["repository"]._get_connection

        class FailCommit:
            def __init__(self):
                self.connection = factory()

            def __getattr__(self, name):
                return getattr(self.connection, name)

            def commit(self):
                raise mysql.connector.OperationalError("private commit failure")

        case["controller"].service._get_connection = FailCommit
    else:
        method = "save_overdue_fine" if failure == "fine" else "refresh_book_statuses"
        original = getattr(case["repository"], method)

        def fail_after_write(*args):
            original(*args)
            raise mysql.connector.OperationalError("private write failure")

        monkeypatch.setattr(case["repository"], method, fail_after_write)
    result = case["controller"].confirm_return(borrowing_id)
    assert not result["success"] and result["data"] is None
    assert "private" not in result["message"]
    assert record_state(case, borrowing_id) == ("ReturnRequested", None)
    assert not fine_rows(case, borrowing_id)
    assert case["sql"]("SELECT return_date FROM borrowing_details WHERE borrowingID=%s",
                       (borrowing_id,)) == [(None,)] * 3
    assert case["sql"]("SELECT quantity, status FROM books WHERE bookID=%s",
                       (case["book_id"],)) == [(3, "Unavailable")]
    assert case["repository"].count_active_copies_for_book(case["book_id"]) == 3


def test_concurrent_confirmation_creates_one_fine_and_one_return(completion_case):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "ReturnRequested", 2)
    case["sql"]("UPDATE borrowing_records SET due_date='2026-11-15' WHERE borrowingID=%s", (borrowing_id,))
    barrier = Barrier(2)

    def send():
        barrier.wait(timeout=5)
        return case["controller"].confirm_return(borrowing_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result(timeout=15) for future in [pool.submit(send) for _ in range(2)]]
    assert sum(item["success"] for item in results) == 1, results
    assert fine_rows(case, borrowing_id) == [(12000, "Unpaid", "Overdue return")]
    assert record_state(case, borrowing_id) == ("Returned", "2026-11-18")


@pytest.mark.parametrize("status", ["Pending", "Borrowed", "Returned", "Rejected"])
def test_confirmation_rejects_non_pending_returns(completion_case, status):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], status, 1)
    before = record_state(case, borrowing_id)
    assert not case["controller"].confirm_return(borrowing_id)["success"]
    assert record_state(case, borrowing_id) == before and not fine_rows(case, borrowing_id)


@pytest.mark.parametrize("borrowing_id", [0, True, "1 OR 1=1", 2147483647])
def test_confirmation_rejects_invalid_or_missing_ids(completion_case, borrowing_id):
    result = completion_case["controller"].confirm_return(borrowing_id)
    assert not result["success"] and result["data"] is None


@pytest.mark.parametrize("action", ["confirm_return", "get_pending_return_requests"])
def test_reader_cannot_use_remaining_admin_operations(completion_case, action):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "ReturnRequested", 1)
    case["controller"].current_user = {"user_id": case["users"][0], "role": "READER"}
    method = getattr(case["controller"], action)
    result = method(borrowing_id) if action == "confirm_return" else method()
    assert not result["success"] and result["data"] is None
    assert record_state(case, borrowing_id) == ("ReturnRequested", None)


def test_stale_admin_session_is_denied_but_locked_reader_can_return(completion_case):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "ReturnRequested", 1)
    case["sql"]("UPDATE users SET account_status='Locked' WHERE userID=%s", (case["admin_user_id"],))
    for result in (case["controller"].confirm_return(borrowing_id),
                   case["controller"].get_pending_return_requests()):
        assert not result["success"] and result["data"] is None
    case["sql"]("UPDATE users SET account_status='Active' WHERE userID=%s", (case["admin_user_id"],))
    case["sql"]("UPDATE users SET account_status='Locked' WHERE userID=%s", (case["users"][0],))
    assert case["controller"].confirm_return(borrowing_id)["success"]


def test_return_makes_copies_available_to_another_pending_reader(completion_case):
    case = completion_case
    case["sql"]("UPDATE books SET quantity=1, status='Unavailable' WHERE bookID=%s", (case["book_id"],))
    returning = case["seed_loan"](case["readers"][0], "ReturnRequested", 1)
    waiting = case["seed_loan"](case["readers"][1], "Pending", 1)
    assert not case["controller"].approve_borrow(waiting)["success"]
    assert BookService().check_book_availability(case["book_id"])["available_quantity"] == 0
    assert case["controller"].confirm_return(returning)["success"]
    assert BookService().check_book_availability(case["book_id"])["available_quantity"] == 1
    assert case["controller"].approve_borrow(waiting)["success"]
    assert BookService().check_book_availability(case["book_id"])["available_quantity"] == 0
    assert case["sql"]("SELECT quantity FROM books WHERE bookID=%s", (case["book_id"],)) == [(1,)]


@pytest.mark.parametrize("bad_date", ["invalid", "2026-10-31", "2026-11-19"])
def test_invalid_return_dates_leave_request_unchanged(completion_case, bad_date):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "ReturnRequested", 2)
    case["sql"]("""UPDATE borrowing_details SET return_date=%s
                  WHERE borrowingID=%s ORDER BY detailID LIMIT 1""", (bad_date, borrowing_id))
    assert not case["controller"].confirm_return(borrowing_id)["success"]
    assert record_state(case, borrowing_id) == ("ReturnRequested", None)
    assert not fine_rows(case, borrowing_id)


def test_fully_paid_overdue_charge_is_not_charged_again(completion_case):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "ReturnRequested", 1)
    case["sql"]("UPDATE borrowing_records SET due_date='2026-11-15' WHERE borrowingID=%s", (borrowing_id,))
    fine_id = add_charge(case, borrowing_id, 6000, "Paid")
    result = case["controller"].confirm_return(borrowing_id)
    assert result["success"], result
    assert result["data"]["fine_id"] == fine_id and result["data"]["unpaid_amount"] == 0
    assert fine_rows(case, borrowing_id) == [(6000, "Paid", "Overdue return")]


def test_multi_book_return_preserves_other_readers_copies(completion_case):
    case = completion_case
    returning = case["seed_loan"](case["readers"][0], "ReturnRequested", 2)
    case["seed_loan"](case["readers"][1], "Borrowed", 1)
    extra_book = case["sql"](
        """INSERT INTO books (title, author, category, status, quantity)
           VALUES ('Second return title', 'Test', 'Test', 'Unavailable', 1)"""
    )
    try:
        case["sql"]("INSERT INTO borrowing_details (borrowingID, bookID) VALUES (%s, %s)",
                    (returning, extra_book))
        result = case["controller"].confirm_return(returning)
        assert result["success"] and result["data"]["quantity"] == 3, result
        assert case["sql"]("SELECT quantity, status FROM books WHERE bookID=%s",
                           (case["book_id"],)) == [(3, "Available")]
        assert case["sql"]("SELECT quantity, status FROM books WHERE bookID=%s",
                           (extra_book,)) == [(1, "Available")]
        assert case["repository"].count_active_copies_for_book(case["book_id"]) == 1
        assert case["repository"].count_active_copies_for_book(extra_book) == 0
        assert case["repository"].count_active_books(case["readers"][1]) == 1
    finally:
        case["sql"]("DELETE FROM borrowing_details WHERE bookID=%s", (extra_book,))
        case["sql"]("DELETE FROM books WHERE bookID=%s", (extra_book,))


def test_pending_return_queue_excludes_other_states_and_groups_copies(completion_case):
    case = completion_case
    assert case["controller"].get_pending_return_requests()["data"] == []
    states = ["Pending", "Borrowed", "ReturnRequested", "Returned", "Rejected"]
    ids = [case["seed_loan"](case["readers"][index % 2], status, 2)
           for index, status in enumerate(states)]
    second = case["seed_loan"](case["readers"][1], "ReturnRequested", 1)
    result = case["controller"].get_pending_return_requests()
    assert result["success"], result
    assert [row["borrowing_id"] for row in result["data"]] == [ids[2], second]
    assert [row["quantity"] for row in result["data"]] == [2, 1]
    assert all(row["reader_name"] and row["status"] == "ReturnRequested"
               and len(row["books"]) == 1 for row in result["data"])
    serialized = json.dumps(result)
    assert "password" not in serialized and "test-only" not in serialized

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import mysql.connector
import pytest

import app.repositories.book_repository as book_module
from app.controllers.borrowing_controller import BorrowingController
from app.services.book_service import BookService
from tests.integration.test_mysql_borrowing import mysql_case
from tests.integration.test_mysql_approval import approval_case
from tests.integration.test_mysql_return_confirmation import completion_case


pytestmark = pytest.mark.skipif(
    os.environ.get("TV4_MYSQL_TESTS") != "1",
    reason="Start the isolated MySQL container and set TV4_MYSQL_TESTS=1.",
)


@pytest.mark.parametrize("status", ["Borrowed", "ReturnRequested"])
def test_book_views_show_remaining_copies_consistently(completion_case, status):
    case = completion_case
    case["seed_loan"](case["readers"][0], status, 2)
    books = BookService()
    detail = books.get_book_by_id(case["book_id"])
    listed = next(row for row in books.get_all_books() if row["book_id"] == case["book_id"])
    searched = next(row for row in books.search_books(detail["title"]) if row["book_id"] == case["book_id"])
    for row in (detail, listed, searched):
        assert row["quantity"] == row["total_quantity"] == 3
        assert row["available_quantity"] == 1 and row["status"] == "Available"
    assert books.check_book_availability(case["book_id"])["available_quantity"] == 1


@pytest.mark.parametrize("status", ["Pending", "Rejected", "Returned"])
def test_non_active_records_do_not_reduce_availability(completion_case, status):
    case = completion_case
    case["seed_loan"](case["readers"][0], status, 2)
    assert BookService().get_book_by_id(case["book_id"])["available_quantity"] == 3


def test_full_borrow_return_and_reject_flow_preserves_physical_total(completion_case):
    case = completion_case
    books, admin = BookService(), case["controller"]
    reader = BorrowingController(
        current_user={"user_id": case["users"][0], "role": "READER"}, service=admin.service,
    )
    other = BorrowingController(
        current_user={"user_id": case["users"][1], "role": "READER"}, service=admin.service,
    )

    def available(expected):
        data = books.get_book_by_id(case["book_id"])
        assert data["total_quantity"] == data["quantity"] == 3
        assert data["available_quantity"] == expected

    pending = reader.request_borrow(case["book_id"], 2)
    assert pending["success"], pending
    borrowing_id = pending["data"]["borrowing_id"]
    available(3)
    assert admin.approve_borrow(borrowing_id)["success"]
    available(1)
    rejected = other.request_borrow(case["book_id"], 2)
    assert not rejected["success"] and "Only 1" in rejected["message"]
    assert reader.request_return(borrowing_id)["success"]
    available(1)
    assert admin.confirm_return(borrowing_id)["success"]
    available(3)
    pending = other.request_borrow(case["book_id"], 2)
    assert pending["success"]
    available(3)
    assert admin.reject_borrow(pending["data"]["borrowing_id"])["success"]
    available(3)


def test_partial_returns_release_only_received_copies(completion_case):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 3)
    case["sql"]("""UPDATE borrowing_details SET return_date='2026-11-18'
                  WHERE borrowingID=%s ORDER BY detailID LIMIT 1""", (borrowing_id,))
    data = BookService().get_book_by_id(case["book_id"])
    assert data["total_quantity"] == 3 and data["available_quantity"] == 1


def test_inconsistent_legacy_stock_never_displays_negative_availability(completion_case):
    case = completion_case
    case["seed_loan"](case["readers"][0], "Borrowed", 4)
    books = BookService()
    data = books.get_book_by_id(case["book_id"])
    assert data["total_quantity"] == 3 and data["available_quantity"] == 0
    assert data["status"] == "Unavailable"
    assert not books.check_book_availability(case["book_id"])["is_available"]


def test_stock_edits_preserve_held_copies_and_return_current_availability(completion_case):
    case = completion_case
    case["seed_loan"](case["readers"][0], "ReturnRequested", 2)
    books, admin = BookService(), case["controller"].current_user
    with pytest.raises(ValueError, match="unreturned copies"):
        books.update_book(case["book_id"], {"quantity": 1}, admin)
    assert books.get_book_by_id(case["book_id"])["total_quantity"] == 3
    updated = books.update_book(case["book_id"], {"quantity": 6}, admin)
    assert updated["total_quantity"] == 6 and updated["available_quantity"] == 4


@pytest.mark.parametrize("explicit_unavailable", [False, True])
def test_restock_reopens_exhausted_title_unless_admin_keeps_it_closed(completion_case, explicit_unavailable):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 3)
    assert case["controller"].approve_borrow(borrowing_id)["success"]
    books = BookService()
    assert books.get_book_by_id(case["book_id"])["available_quantity"] == 0
    changes = {"quantity": 5}
    if explicit_unavailable:
        changes["status"] = "Unavailable"
    updated = books.update_book(case["book_id"], changes, case["controller"].current_user)
    assert updated["total_quantity"] == 5
    assert updated["available_quantity"] == (0 if explicit_unavailable else 2)
    assert updated["status"] == ("Unavailable" if explicit_unavailable else "Available")


def test_stock_increase_preserves_manual_closure_with_spare_copies(completion_case):
    case = completion_case
    case["seed_loan"](case["readers"][0], "Borrowed", 1)
    case["sql"]("UPDATE books SET status='Unavailable' WHERE bookID=%s", (case["book_id"],))
    updated = BookService().update_book(
        case["book_id"], {"quantity": 5}, case["controller"].current_user,
    )
    assert updated["total_quantity"] == 5 and updated["available_quantity"] == 0
    assert updated["status"] == "Unavailable"


def test_stock_update_rolls_back_on_commit_failure(completion_case, monkeypatch):
    case = completion_case
    case["seed_loan"](case["readers"][0], "Borrowed", 2)
    factory = case["repository"]._get_connection

    class FailCommit:
        def __init__(self):
            self.connection = factory()

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def commit(self):
            raise mysql.connector.OperationalError("Simulated commit failure")

    monkeypatch.setattr(book_module, "get_connection", FailCommit)
    with pytest.raises(mysql.connector.OperationalError):
        BookService().update_book(case["book_id"], {"quantity": 6}, case["controller"].current_user)
    assert case["sql"]("SELECT quantity, status FROM books WHERE bookID=%s",
                       (case["book_id"],)) == [(3, "Available")]


def test_concurrent_stock_reduction_and_approval_cannot_overlend(completion_case):
    case = completion_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Pending", 3)
    barrier = Barrier(2)

    def approve():
        barrier.wait(timeout=5)
        return case["controller"].approve_borrow(borrowing_id)["success"]

    def reduce_stock():
        barrier.wait(timeout=5)
        try:
            BookService().update_book(case["book_id"], {"quantity": 1}, case["controller"].current_user)
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result(timeout=15) for future in [pool.submit(approve), pool.submit(reduce_stock)]]
    assert sum(results) == 1, results
    total = case["sql"]("SELECT quantity FROM books WHERE bookID=%s", (case["book_id"],))[0][0]
    held = case["repository"].count_active_copies_for_book(case["book_id"])
    assert held <= total
    assert BookService().get_book_by_id(case["book_id"])["available_quantity"] == total - held

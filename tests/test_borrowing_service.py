
from datetime import date

import pytest

from app.models.book import Book
from app.services.borrowing_service import BorrowingService


class FakeConnection:
    def __init__(self):
        self.started = False
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.fail_commit = False

    def start_transaction(self, isolation_level=None, readonly=None):
        self.started = True

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("Simulated commit failure")
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class FakeBookRepository:
    def __init__(self):
        self.book = Book(book_id=4, quantity=3)
        self.lookups = []

    def get_by_id(self, book_id):
        self.lookups.append(book_id)
        return self.book


class FakeBorrowingRepository:
    def __init__(self, conn):
        self.conn = conn
        self.reader = {
            "reader_id": 7,
            "role": "Reader",
            "account_status": "Active",
            "expiration_date": None,
        }
        self.active_quantity = 0
        self.borrowed_copies = 0
        self.lookups = []
        self.counted_readers = []
        self.requests = []
        self.fail_save = False
        self.book_repository = None

    def get_reader_for_update(self, user_id, connection):
        assert connection is self.conn
        assert connection.started
        self.lookups.append(user_id)
        return self.reader

    def count_active_books(self, reader_id, connection):
        assert connection is self.conn
        self.counted_readers.append(reader_id)
        return self.active_quantity

    def count_active_copies_for_book(self, book_id, connection):
        assert connection is self.conn
        return self.borrowed_copies

    def lock_requested_books(self, book_ids, connection):
        assert connection is self.conn
        assert connection.started

        result = {}

        for book_id in sorted(set(book_ids)):
            book = (
                self.book_repository.book
                if self.book_repository is not None
                else None
            )

            if book is None or book.book_id != book_id:
                result[book_id] = None
            else:
                result[book_id] = {
                    "bookID": book_id,
                    "quantity": book.quantity,
                    "status": book.status,
                }

        return result

    def create_pending_request(
        self,
        reader_id,
        book_id,
        quantity,
        borrow_date,
        due_date,
        connection=None,
    ):
        assert connection is self.conn

        if self.fail_save:
            raise RuntimeError("Simulated database failure")

        self.requests.append(
            (reader_id, book_id, quantity, borrow_date, due_date)
        )
        return 20


@pytest.fixture
def setup():
    conn = FakeConnection()
    books = FakeBookRepository()
    borrowing = FakeBorrowingRepository(conn)
    borrowing.book_repository = books
    opened = []

    def factory():
        opened.append(conn)
        return conn

    service = BorrowingService(
        book_repository=books,
        borrowing_repository=borrowing,
        connection_factory=factory,
        loan_period_days=10,  # Test data, not the production lending policy.
        today_provider=lambda: date(2026, 11, 18),
    )

    return service, conn, books, borrowing, opened


@pytest.mark.parametrize(
    "active, requested",
    [(0, 3), (1, 2), (2, 1)],
)
def test_valid_request_uses_session_user_and_preserves_inventory(
    setup, active, requested
):
    service, conn, books, borrowing, opened = setup
    borrowing.active_quantity = active

    result = service.request_borrow(
        4,
        requested,
        {"user_id": 2, "role": "READER", "reader_id": 999},
    )

    assert borrowing.lookups == [2]
    assert borrowing.counted_readers == [7]
    assert borrowing.requests == [
        (7, 4, requested, "2026-11-18", "2026-11-28")
    ]
    assert result == {
        "borrowing_id": 20,
        "reader_id": 7,
        "book_id": 4,
        "quantity": requested,
        "borrow_date": "2026-11-18",
        "due_date": "2026-11-28",
        "status": "Pending",
    }
    assert books.book.quantity == 3
    assert opened == [conn]
    assert conn.committed
    assert conn.closed
    assert not conn.rolled_back


@pytest.mark.parametrize(
    "active, requested",
    [(3, 1), (2, 2), (1, 3)],
)
def test_rejects_request_exceeding_three_books(
    setup, active, requested
):
    service, conn, books, borrowing, opened = setup
    borrowing.active_quantity = active

    with pytest.raises(ValueError, match="borrowing limit is 3 books"):
        service.request_borrow(
            4, requested, {"user_id": 2, "role": "READER"}
        )

    assert not borrowing.requests
    assert not books.lookups
    assert conn.rolled_back
    assert conn.closed
    assert not conn.committed


@pytest.mark.parametrize(
    "current_user",
    [
        None,
        {},
        {"user_id": 2, "role": "ADMIN"},
        {"user_id": 2, "role": "OTHER"},
        {"role": "READER"},
        {"user_id": True, "role": "READER"},
        {"user_id": 0, "role": "READER"},
        {"user_id": "2", "role": "READER"},
    ],
)
def test_rejects_unauthorized_sessions_before_database_access(
    setup, current_user
):
    service, conn, books, borrowing, opened = setup

    with pytest.raises(PermissionError):
        service.request_borrow(4, 1, current_user)

    assert not opened
    assert not borrowing.requests


@pytest.mark.parametrize(
    "field, value",
    [
        ("account_status", "Locked"),
        ("account_status", "Inactive"),
        ("role", "Admin"),
        ("expiration_date", "2026-11-17"),
    ],
)
def test_rejects_ineligible_reader_accounts(setup, field, value):
    service, conn, books, borrowing, opened = setup
    borrowing.reader[field] = value

    with pytest.raises(PermissionError):
        service.request_borrow(
            4, 1, {"user_id": 2, "role": "READER"}
        )

    assert not borrowing.requests
    assert conn.rolled_back
    assert conn.closed
    assert not conn.committed


def test_missing_reader_account_rolls_back(setup):
    service, conn, books, borrowing, opened = setup
    borrowing.reader = None

    with pytest.raises(PermissionError, match="Reader account not found"):
        service.request_borrow(
            4, 1, {"user_id": 2, "role": "READER"}
        )

    assert not borrowing.requests
    assert conn.rolled_back
    assert conn.closed


def test_invalid_expiration_date_is_rejected(setup):
    service, conn, books, borrowing, opened = setup
    borrowing.reader["expiration_date"] = "not-a-date"

    with pytest.raises(ValueError, match="expiration date is invalid"):
        service.request_borrow(
            4, 1, {"user_id": 2, "role": "READER"}
        )

    assert not borrowing.requests
    assert conn.rolled_back
    assert conn.closed


def test_reader_membership_valid_through_today(setup):
    service, conn, books, borrowing, opened = setup
    borrowing.reader["expiration_date"] = "2026-11-18"

    service.request_borrow(
        4, 1, {"user_id": 2, "role": "Reader"}
    )

    assert conn.committed
    assert conn.closed


@pytest.mark.parametrize(
    "book_id, quantity",
    [
        (True, 1),
        (0, 1),
        ("4", 1),
        (4, 0),
        (4, True),
        (4, 1.5),
        (4, 4),
    ],
)
def test_invalid_input_does_not_open_connection(
    setup, book_id, quantity
):
    service, conn, books, borrowing, opened = setup

    with pytest.raises(ValueError):
        service.request_borrow(
            book_id, quantity, {"user_id": 2, "role": "READER"}
        )

    assert not opened
    assert not borrowing.requests


@pytest.mark.parametrize("period", [None, 0, -1, True, "10"])
def test_lending_period_requires_explicit_valid_configuration(
    setup, period
):
    service, conn, books, borrowing, opened = setup
    service.loan_period_days = period

    with pytest.raises(ValueError, match="Borrowing requests are unavailable"):
        service.request_borrow(
            4, 1, {"user_id": 2, "role": "READER"}
        )

    assert not opened
    assert not borrowing.requests


@pytest.mark.parametrize(
    "failure", ["missing", "unavailable", "insufficient"]
)
def test_failed_stock_check_does_not_save_request(setup, failure):
    service, conn, books, borrowing, opened = setup

    if failure == "missing":
        books.book = None
    elif failure == "unavailable":
        books.book.status = "Unavailable"
    else:
        books.book.quantity = 1

    with pytest.raises(ValueError):
        service.request_borrow(
            4,
            2 if failure == "insufficient" else 1,
            {"user_id": 2, "role": "READER"},
        )

    assert not borrowing.requests
    assert conn.rolled_back
    assert conn.closed
    assert not conn.committed


@pytest.mark.parametrize("failure", ["save", "commit"])
def test_storage_failure_rolls_back_and_closes_connection(
    setup, failure
):
    service, conn, books, borrowing, opened = setup
    borrowing.fail_save = failure == "save"
    conn.fail_commit = failure == "commit"

    with pytest.raises(RuntimeError):
        service.request_borrow(
            4, 1, {"user_id": 2, "role": "READER"}
        )

    assert conn.rolled_back
    assert conn.closed
    assert not conn.committed
    assert books.book.quantity == 3


@pytest.mark.parametrize("held, requested", [(3, 1), (2, 2), (4, 1)])
def test_rejects_copies_currently_held_by_other_readers(
    setup, held, requested
):
    service, conn, books, borrowing, opened = setup
    borrowing.borrowed_copies = held

    with pytest.raises(ValueError):
        service.request_borrow(
            4, requested, {"user_id": 2, "role": "READER"}
        )

    assert not borrowing.requests
    assert books.book.quantity == 3
    assert conn.rolled_back and conn.closed


def test_allows_exactly_remaining_copies(setup):
    service, conn, books, borrowing, opened = setup
    borrowing.borrowed_copies = 2

    result = service.request_borrow(
        4, 1, {"user_id": 2, "role": "READER"}
    )

    assert result["quantity"] == 1
    assert books.book.quantity == 3
    assert conn.committed and conn.closed

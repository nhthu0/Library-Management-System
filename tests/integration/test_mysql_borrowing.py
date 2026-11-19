import os
from datetime import date
from pathlib import Path
from uuid import uuid4

import mysql.connector
import pytest

import app.repositories.book_repository as book_module
from app.controllers.borrowing_controller import BorrowingController
from app.repositories.borrowing_repository import BorrowingRepository
from app.services.borrowing_service import BorrowingService


pytestmark = pytest.mark.skipif(
    os.environ.get("TV4_MYSQL_TESTS") != "1",
    reason="Start the isolated MySQL container and set TV4_MYSQL_TESTS=1.",
)


@pytest.fixture
def mysql_case(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    password = (root / ".venv/tv4_mysql/app_password").read_text().strip()

    def connect():
        return mysql.connector.connect(
            host="127.0.0.1",
            port=3308,
            database="library_management",
            user="library_user",
            password=password,
            connection_timeout=5,
        )

    def sql(query, params=()):
        conn = connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchall() if cursor.with_rows else cursor.lastrowid
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    assert sql("SELECT VERSION()")[0][0].startswith("8.0.")
    monkeypatch.setattr(book_module, "get_connection", connect)
    users, readers, books = [], [], []
    tag = uuid4().hex[:12]

    try:
        for suffix in ("reader", "other"):
            username = f"tv4_{tag}_{suffix}"
            user_id = sql(
                """
                INSERT INTO users
                    (username, full_name, email, password, role, account_status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    username,
                    "Integration Test",
                    f"{username}@example.invalid",
                    "test-only-no-login",
                    "Reader",
                    "Active",
                ),
            )
            users.append(user_id)
            readers.append(
                sql("INSERT INTO readers (userID) VALUES (%s)", (user_id,))
            )

        book_id = sql(
            """
            INSERT INTO books (title, author, category, status, quantity)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (f"TV4 {tag}", "Integration Test", "Test", "Available", 3),
        )
        books.append(book_id)

        repository = BorrowingRepository(connection_factory=connect)
        service = BorrowingService(
            borrowing_repository=repository,
            connection_factory=connect,
            loan_period_days=10,  # Test only; not the production loan policy.
            today_provider=lambda: date(2026, 11, 18),
        )
        controller = BorrowingController(
            current_user={
                "user_id": users[0],
                "role": "READER",
                "reader_id": readers[1],
            },
            service=service,
        )

        def seed_loan(reader_id, status, quantity):
            returned_on = "2026-11-18" if status == "Returned" else None
            borrowing_id = sql(
                """
                INSERT INTO borrowing_records
                    (readerID, borrow_date, due_date, return_date, status)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (reader_id, "2026-11-01", "2026-11-20", returned_on, status),
            )
            for _ in range(quantity):
                sql(
                    """
                    INSERT INTO borrowing_details
                        (borrowingID, bookID, return_date)
                    VALUES (%s, %s, %s)
                    """,
                    (borrowing_id, book_id, returned_on),
                )
            return borrowing_id

        def request_count():
            return sql(
                "SELECT COUNT(*) FROM borrowing_records WHERE readerID=%s",
                (readers[0],),
            )[0][0]

        yield {
            "sql": sql,
            "controller": controller,
            "repository": repository,
            "users": users,
            "readers": readers,
            "book_id": book_id,
            "seed_loan": seed_loan,
            "request_count": request_count,
        }

    finally:
        # Delete only rows created by this test.
        for reader_id in readers:
            sql(
                """
                DELETE d FROM borrowing_details d
                JOIN borrowing_records r ON r.borrowingID=d.borrowingID
                WHERE r.readerID=%s
                """,
                (reader_id,),
            )
            sql("DELETE FROM borrowing_records WHERE readerID=%s", (reader_id,))
            sql("DELETE FROM readers WHERE readerID=%s", (reader_id,))

        for user_id in users:
            sql("DELETE FROM users WHERE userID=%s", (user_id,))

        for book_id in books:
            sql("DELETE FROM books WHERE bookID=%s", (book_id,))


@pytest.mark.parametrize("quantity", [1, 2, 3])
def test_pending_request_is_persisted_without_changing_total(mysql_case, quantity):
    case = mysql_case
    result = case["controller"].request_borrow(case["book_id"], quantity)
    assert result["success"], result

    data = result["data"]
    assert data["reader_id"] == case["readers"][0]
    assert data["status"] == "Pending"
    assert data["due_date"] == "2026-11-28"

    assert case["sql"](
        "SELECT readerID, status FROM borrowing_records WHERE borrowingID=%s",
        (data["borrowing_id"],),
    ) == [(case["readers"][0], "Pending")]

    assert case["sql"](
        "SELECT bookID FROM borrowing_details WHERE borrowingID=%s",
        (data["borrowing_id"],),
    ) == [(case["book_id"],)] * quantity

    assert case["sql"](
        "SELECT quantity FROM books WHERE bookID=%s",
        (case["book_id"],),
    ) == [(3,)]


@pytest.mark.parametrize("status", ["Borrowed", "ReturnRequested"])
def test_three_unreturned_copies_block_new_request(mysql_case, status):
    case = mysql_case
    case["seed_loan"](case["readers"][0], status, 3)

    result = case["controller"].request_borrow(case["book_id"], 1)

    assert result == {
        "success": False,
        "message": "The borrowing limit is 3 books.",
        "data": None,
    }
    assert case["request_count"]() == 1


@pytest.mark.parametrize("status", ["Borrowed", "ReturnRequested"])
def test_other_reader_holds_all_copies(mysql_case, status):
    case = mysql_case
    case["seed_loan"](case["readers"][1], status, 3)

    result = case["controller"].request_borrow(case["book_id"], 1)

    assert not result["success"], result
    assert result["data"] is None
    assert case["request_count"]() == 0


def test_request_cannot_exceed_remaining_copies(mysql_case):
    case = mysql_case
    case["seed_loan"](case["readers"][1], "Borrowed", 2)

    result = case["controller"].request_borrow(case["book_id"], 2)

    assert result == {
        "success": False,
        "message": "Only 1 copies are available.",
        "data": None,
    }
    assert case["request_count"]() == 0


@pytest.mark.parametrize("status", ["Pending", "Returned", "Rejected"])
def test_non_active_loans_do_not_consume_available_copies(mysql_case, status):
    case = mysql_case
    case["seed_loan"](case["readers"][1], status, 3)

    result = case["controller"].request_borrow(case["book_id"], 3)

    assert result["success"], result


@pytest.mark.parametrize("account_status", ["Locked", "Inactive"])
def test_database_account_status_overrides_stale_session(
    mysql_case, account_status
):
    case = mysql_case
    case["sql"](
        "UPDATE users SET account_status=%s WHERE userID=%s",
        (account_status, case["users"][0]),
    )

    result = case["controller"].request_borrow(case["book_id"], 1)

    assert not result["success"], result
    assert case["request_count"]() == 0


def test_failed_detail_insert_rolls_back_request_header(mysql_case):
    case = mysql_case

    with pytest.raises(mysql.connector.IntegrityError):
        case["repository"].create_pending_request(
            case["readers"][0], 0, 2, "2026-11-18", "2026-11-28"
        )

    assert case["request_count"]() == 0
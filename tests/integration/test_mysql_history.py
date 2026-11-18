import json
import os

import mysql.connector
import pytest

from tests.integration.test_mysql_borrowing import mysql_case


pytestmark = pytest.mark.skipif(
    os.environ.get("TV4_MYSQL_TESTS") != "1",
    reason="Start the isolated MySQL container and set TV4_MYSQL_TESTS=1.",
)


def test_empty_history_does_not_expose_other_reader(mysql_case):
    case = mysql_case
    case["seed_loan"](case["readers"][1], "Borrowed", 1)
    result = case["controller"].get_my_borrowing_history()
    assert result == {
        "success": True, "message": "Borrowing history loaded successfully.", "data": [],
    }


@pytest.mark.parametrize("status, returned", [("Borrowed", 0), ("Returned", 2)])
def test_history_uses_session_owner_and_groups_copies(mysql_case, status, returned):
    case = mysql_case
    own_id = case["seed_loan"](case["readers"][0], status, 2)
    case["seed_loan"](case["readers"][1], "Borrowed", 3)
    result = case["controller"].get_my_borrowing_history()
    assert result["success"], result
    assert set(result) == {"success", "message", "data"}
    assert len(result["data"]) == 1
    record = result["data"][0]
    assert record["borrowing_id"] == own_id
    assert record["reader_id"] == case["readers"][0]
    assert record["status"] == status
    assert record["quantity"] == 2
    assert record["returned_quantity"] == returned
    assert record["return_date"] == ("2026-11-18" if returned else None)
    assert record["due_date"] == "2026-11-20"
    assert len(record["books"]) == 1
    book = record["books"][0]
    assert book["book_id"] == case["book_id"]
    assert book["quantity"] == 2 and book["returned_quantity"] == returned
    assert book["title"] and book["author"]
    json.dumps(result)


def test_history_includes_all_states_and_orders_by_date_then_id(mysql_case):
    case = mysql_case
    statuses = ["Pending", "Borrowed", "ReturnRequested", "Returned", "Rejected"]
    ids = [case["seed_loan"](case["readers"][0], status, 1) for status in statuses]
    case["sql"]("UPDATE borrowing_records SET borrow_date=%s WHERE borrowingID=%s",
                ("2026-11-02", ids[0]))
    result = case["controller"].get_my_borrowing_history()
    assert result["success"], result
    assert [row["borrowing_id"] for row in result["data"]] == [ids[0], *reversed(ids[1:])]
    assert {row["status"] for row in result["data"]} == set(statuses)


def test_history_groups_multiple_books_without_duplicate_records(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 2)
    second_book = case["sql"](
        "INSERT INTO books (title, author, category, quantity) VALUES (%s,%s,%s,%s)",
        ("History Test", "Integration Test", "Test", 1),
    )
    try:
        case["sql"]("INSERT INTO borrowing_details (borrowingID, bookID) VALUES (%s,%s)",
                    (borrowing_id, second_book))
        result = case["controller"].get_my_borrowing_history()
        assert result["success"], result
        assert len(result["data"]) == 1
        record = result["data"][0]
        assert record["quantity"] == 3
        assert {book["book_id"]: book["quantity"] for book in record["books"]} == {
            case["book_id"]: 2, second_book: 1,
        }
    finally:
        case["sql"]("DELETE FROM borrowing_details WHERE bookID=%s", (second_book,))
        case["sql"]("DELETE FROM books WHERE bookID=%s", (second_book,))


@pytest.mark.parametrize("session", [None, {"user_id": 2, "role": "ADMIN"}])
def test_history_requires_reader_session(mysql_case, session):
    mysql_case["controller"].current_user = session
    result = mysql_case["controller"].get_my_borrowing_history()
    assert result["success"] is False and result["data"] is None


@pytest.mark.parametrize("field, value", [("role", "Admin"), ("account_status", "Locked")])
def test_history_rechecks_database_permissions(mysql_case, field, value):
    case = mysql_case
    if field == "role":
        case["sql"]("UPDATE users SET role=%s WHERE userID=%s", (value, case["users"][0]))
    else:
        case["sql"]("UPDATE users SET account_status=%s WHERE userID=%s",
                    (value, case["users"][0]))
    result = case["controller"].get_my_borrowing_history()
    assert result["success"] is False and result["data"] is None


def test_history_allows_expired_membership_and_does_not_update_loans(mysql_case):
    case = mysql_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 1)
    case["sql"]("UPDATE readers SET expiration_date=%s WHERE readerID=%s",
                ("2026-11-17", case["readers"][0]))
    result = case["controller"].get_my_borrowing_history()
    assert result["success"], result
    assert case["sql"](
        "SELECT status, return_date FROM borrowing_records WHERE borrowingID=%s",
        (borrowing_id,),
    ) == [("Borrowed", None)]
    assert case["sql"]("SELECT quantity FROM books WHERE bookID=%s", (case["book_id"],)) == [(3,)]


def test_history_hides_database_error_details(mysql_case):
    def unavailable():
        raise mysql.connector.OperationalError("private connection details")

    mysql_case["controller"].service._get_connection = unavailable
    result = mysql_case["controller"].get_my_borrowing_history()
    assert result == {
        "success": False,
        "message": "Unable to load borrowing history. Please contact the library administrator.",
        "data": None,
    }

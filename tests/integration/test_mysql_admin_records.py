import json
import os

import mysql.connector
import pytest

from tests.integration.test_mysql_approval import approval_case
from tests.integration.test_mysql_borrowing import mysql_case


pytestmark = pytest.mark.skipif(
    os.environ.get("TV4_MYSQL_TESTS") != "1",
    reason="Start the isolated MySQL container and set TV4_MYSQL_TESTS=1.",
)


def test_admin_records_returns_empty_list(approval_case):
    result = approval_case["controller"].get_all_borrowing_records()
    assert result["success"] and result["data"] == []


def test_all_readers_all_states_grouped_newest_first_without_mutation(approval_case):
    case = approval_case
    states = ["Pending", "Borrowed", "ReturnRequested", "Returned", "Rejected"]
    ids = [
        case["seed_loan"](case["readers"][index % 2], status, 2)
        for index, status in enumerate(states)
    ]
    case["sql"](
        "UPDATE borrowing_records SET borrow_date='2026-11-02' WHERE borrowingID=%s",
        (ids[0],),
    )
    before = case["sql"](
        "SELECT borrowingID, status, return_date FROM borrowing_records ORDER BY borrowingID"
    )

    result = case["controller"].get_all_borrowing_records()
    assert result["success"], result
    rows = result["data"]

    assert [row["borrowing_id"] for row in rows] == [ids[0]] + list(reversed(ids[1:]))
    assert {row["reader_id"] for row in rows} == set(case["readers"])
    assert {row["status"] for row in rows} == set(states)
    assert all(row["quantity"] == 2 and len(row["books"]) == 1 for row in rows)

    returned = next(row for row in rows if row["status"] == "Returned")
    assert returned["returned_quantity"] == 2
    assert returned["return_date"] == "2026-11-18"

    serialized = json.dumps(rows)
    assert "password" not in serialized and "test-only" not in serialized
    assert case["sql"](
        "SELECT borrowingID, status, return_date FROM borrowing_records ORDER BY borrowingID"
    ) == before
    assert case["sql"](
        "SELECT quantity FROM books WHERE bookID=%s", (case["book_id"],)
    ) == [(3,)]


def test_multiple_titles_stay_in_one_record(approval_case):
    case = approval_case
    borrowing_id = case["seed_loan"](case["readers"][0], "Borrowed", 1)
    book_id = case["sql"](
        """INSERT INTO books (title, author, category, status, quantity)
           VALUES ('Second admin history title', 'Test', 'Test', 'Available', 1)"""
    )
    try:
        case["sql"](
            "INSERT INTO borrowing_details (borrowingID, bookID) VALUES (%s, %s)",
            (borrowing_id, book_id),
        )
        result = case["controller"].get_all_borrowing_records()
        assert result["success"] and len(result["data"]) == 1, result
        record = result["data"][0]
        assert record["borrowing_id"] == borrowing_id and record["quantity"] == 2
        assert {book["book_id"] for book in record["books"]} == {
            case["book_id"], book_id
        }
    finally:
        case["sql"]("DELETE FROM borrowing_details WHERE bookID=%s", (book_id,))
        case["sql"]("DELETE FROM books WHERE bookID=%s", (book_id,))


@pytest.mark.parametrize("session", ["anonymous", "reader", "invalid_admin"])
def test_non_admin_sessions_cannot_read_all_records(approval_case, session):
    case = approval_case
    case["seed_loan"](case["readers"][1], "Pending", 1)
    sessions = {
        "anonymous": None,
        "reader": {"user_id": case["users"][0], "role": "READER"},
        "invalid_admin": {"user_id": True, "role": "ADMIN"},
    }
    case["controller"].current_user = sessions[session]
    result = case["controller"].get_all_borrowing_records()
    assert result["success"] is False and result["data"] is None


@pytest.mark.parametrize("field", ["role", "account_status"])
def test_stale_admin_session_is_rechecked_in_database(approval_case, field):
    case = approval_case
    if field == "role":
        case["sql"](
            "UPDATE users SET role='Reader' WHERE userID=%s",
            (case["admin_user_id"],),
        )
    else:
        case["sql"](
            "UPDATE users SET account_status='Locked' WHERE userID=%s",
            (case["admin_user_id"],),
        )
    result = case["controller"].get_all_borrowing_records()
    assert result["success"] is False and result["data"] is None


def test_database_errors_do_not_expose_internal_details(approval_case, monkeypatch):
    case = approval_case

    def fail(*args):
        raise mysql.connector.OperationalError("private SQL column details")

    monkeypatch.setattr(case["repository"], "get_admin_record_rows", fail)
    result = case["controller"].get_all_borrowing_records()
    assert result["success"] is False and result["data"] is None
    assert "private" not in result["message"] and "column" not in result["message"]

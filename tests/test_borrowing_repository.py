import sqlite3

import pytest

from app.repositories.borrowing_repository import BorrowingRepository


class CursorAdapter:
    """Adapt MySQL placeholders for the temporary test database."""

    def __init__(self, raw, fail=False):
        self.raw = raw
        self.fail = fail
        self.closed = False

    def execute(self, sql, parameters):
        if self.fail:
            raise RuntimeError("Simulated query failure")
        self.raw.execute(sql.replace("%s", "?"), parameters)

    def fetchone(self):
        return self.raw.fetchone()

    def close(self):
        self.raw.close()
        self.closed = True


class ConnectionAdapter:
    def __init__(self, fail_query=False, fail_cursor=False):
        self.raw = sqlite3.connect(":memory:")
        self.closed = False
        self.fail_query = fail_query
        self.fail_cursor = fail_cursor
        self.last_cursor = None
        self.raw.executescript("""
            CREATE TABLE borrowing_records (
                borrowingID INTEGER PRIMARY KEY,
                readerID INTEGER NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE borrowing_details (
                detailID INTEGER PRIMARY KEY,
                borrowingID INTEGER NOT NULL,
                bookID INTEGER NOT NULL,
                return_date TEXT
            );
        """)

    def cursor(self):
        if self.fail_cursor:
            raise RuntimeError("Simulated cursor failure")
        self.last_cursor = CursorAdapter(
            self.raw.cursor(), self.fail_query
        )
        return self.last_cursor

    def close(self):
        self.raw.close()
        self.closed = True


@pytest.mark.parametrize(
    "status, expected",
    [
        ("Borrowed", 2),
        ("ReturnRequested", 2),
        ("Pending", 0),
        ("Rejected", 0),
        ("Returned", 0),
    ],
)
def test_counts_copies_by_actual_record_status(status, expected):
    conn = ConnectionAdapter()
    conn.raw.execute(
        "INSERT INTO borrowing_records VALUES (1, 7, ?)",
        (status,),
    )
    conn.raw.executemany(
        "INSERT INTO borrowing_details VALUES (?, 1, 4, NULL)",
        [(1,), (2,)],
    )

    result = BorrowingRepository().count_active_books(7, conn)

    assert result == expected
    assert not conn.closed
    assert conn.last_cursor.closed
    assert conn.raw.execute(
        "SELECT COUNT(*) FROM borrowing_details"
    ).fetchone()[0] == 2
    conn.close()


def test_counts_only_current_reader_and_unreturned_copies():
    conn = ConnectionAdapter()
    conn.raw.executemany(
        "INSERT INTO borrowing_records VALUES (?, ?, ?)",
        [
            (1, 7, "Borrowed"),
            (2, 7, "ReturnRequested"),
            (3, 8, "Borrowed"),
        ],
    )
    conn.raw.executemany(
        "INSERT INTO borrowing_details VALUES (?, ?, ?, ?)",
        [
            (1, 1, 4, None),
            (2, 1, 4, None),
            (3, 2, 5, None),
            (4, 1, 6, "2026-11-17"),
            (5, 3, 4, None),
        ],
    )

    repo = BorrowingRepository()

    assert repo.count_active_books(7, conn) == 3
    assert repo.count_active_books(8, conn) == 1
    assert repo.count_active_books(9, conn) == 0
    conn.close()


def test_reader_id_is_passed_as_data():
    conn = ConnectionAdapter()
    conn.raw.execute(
        "INSERT INTO borrowing_records VALUES (1, 7, 'Borrowed')"
    )
    conn.raw.execute(
        "INSERT INTO borrowing_details VALUES (1, 1, 4, NULL)"
    )

    repo = BorrowingRepository()

    assert repo.count_active_books("7 OR 1=1", conn) == 0
    assert repo.count_active_books(7, conn) == 1
    conn.close()


def test_closes_its_own_connection():
    conn = ConnectionAdapter()

    result = BorrowingRepository(
        lambda: conn
    ).count_active_books(7)

    assert result == 0
    assert conn.closed
    assert conn.last_cursor.closed


@pytest.mark.parametrize("owns_connection", [True, False])
def test_query_failure_closes_only_owned_resources(owns_connection):
    conn = ConnectionAdapter(fail_query=True)
    repo = BorrowingRepository(lambda: conn)

    with pytest.raises(RuntimeError, match="Simulated query failure"):
        repo.count_active_books(
            7, None if owns_connection else conn
        )

    assert conn.last_cursor.closed
    assert conn.closed is owns_connection

    if not owns_connection:
        conn.close()


def test_cursor_failure_closes_owned_connection():
    conn = ConnectionAdapter(fail_cursor=True)

    with pytest.raises(RuntimeError, match="Simulated cursor failure"):
        BorrowingRepository(
            lambda: conn
        ).count_active_books(7)

    assert conn.closed
import sqlite3

import pytest

from app.repositories.borrowing_repository import BorrowingRepository


class WriteCursor:
    def __init__(self, raw):
        self.raw = raw
        self.closed = False

    def execute(self, sql, parameters):
        self.raw.execute(sql.replace("%s", "?"), parameters)

    def executemany(self, sql, parameters):
        self.raw.executemany(sql.replace("%s", "?"), parameters)

    @property
    def lastrowid(self):
        return self.raw.lastrowid

    def close(self):
        self.raw.close()
        self.closed = True


class WriteConnection:
    def __init__(self, path, fail_commit=False):
        self.raw = sqlite3.connect(path)
        self.raw.execute("PRAGMA foreign_keys = ON")
        self.closed = False
        self.fail_commit = fail_commit
        self.commits = 0
        self.rollbacks = 0
        self.last_cursor = None

    def cursor(self):
        self.last_cursor = WriteCursor(self.raw.cursor())
        return self.last_cursor

    def start_transaction(self):
        self.raw.execute("BEGIN")

    def commit(self):
        if self.fail_commit:
            raise RuntimeError("Simulated commit failure")
        self.raw.commit()
        self.commits += 1

    def rollback(self):
        self.raw.rollback()
        self.rollbacks += 1

    def close(self):
        self.raw.close()
        self.closed = True


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "borrowing.sqlite"

    with sqlite3.connect(path) as raw:
        raw.executescript("""
            PRAGMA foreign_keys = ON;

            CREATE TABLE readers (
                readerID INTEGER PRIMARY KEY
            );

            CREATE TABLE books (
                bookID INTEGER PRIMARY KEY,
                quantity INTEGER NOT NULL
            );

            CREATE TABLE borrowing_records (
                borrowingID INTEGER PRIMARY KEY,
                readerID INTEGER NOT NULL REFERENCES readers(readerID),
                borrow_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE borrowing_details (
                detailID INTEGER PRIMARY KEY,
                borrowingID INTEGER NOT NULL
                    REFERENCES borrowing_records(borrowingID),
                bookID INTEGER NOT NULL REFERENCES books(bookID)
            );

            INSERT INTO readers VALUES (7);
            INSERT INTO books VALUES (4, 5);
        """)

    return path


def saved_counts(path):
    with sqlite3.connect(path) as raw:
        return (
            raw.execute(
                "SELECT COUNT(*) FROM borrowing_records"
            ).fetchone()[0],
            raw.execute(
                "SELECT COUNT(*) FROM borrowing_details"
            ).fetchone()[0],
        )


@pytest.mark.parametrize("quantity", [1, 2, 3])
def test_saves_pending_request_with_one_detail_per_copy(database, quantity):
    conn = WriteConnection(database)
    repo = BorrowingRepository(lambda: conn)

    borrowing_id = repo.create_pending_request(
        7, 4, quantity, "2026-11-18", "2026-12-01"
    )

    assert type(borrowing_id) is int
    assert borrowing_id > 0
    assert conn.commits == 1
    assert conn.closed
    assert conn.last_cursor.closed
    assert saved_counts(database) == (1, quantity)

    with sqlite3.connect(database) as raw:
        record = raw.execute(
            """
            SELECT readerID, borrow_date, due_date, status
            FROM borrowing_records
            """
        ).fetchone()

        assert record == (
            7, "2026-11-18", "2026-12-01", "Pending"
        )

        stock = raw.execute(
            "SELECT quantity FROM books WHERE bookID = 4"
        ).fetchone()[0]

        assert stock == 5

        details = raw.execute(
            """
            SELECT COUNT(*)
            FROM borrowing_details
            WHERE borrowingID = ? AND bookID = 4
            """,
            (borrowing_id,),
        ).fetchone()[0]

        assert details == quantity


@pytest.mark.parametrize(
    "reader_id, book_id",
    [(999, 4), (7, 999)],
)
def test_failed_insert_rolls_back_record_and_details(
    database, reader_id, book_id
):
    conn = WriteConnection(database)

    with pytest.raises(sqlite3.IntegrityError):
        BorrowingRepository(lambda: conn).create_pending_request(
            reader_id, book_id, 2, "2026-11-18", "2026-12-01"
        )

    assert saved_counts(database) == (0, 0)
    assert conn.rollbacks == 1
    assert conn.closed
    assert conn.last_cursor.closed


@pytest.mark.parametrize(
    "quantity", [0, -1, True, 1.5, "1", None]
)
def test_invalid_quantity_does_not_open_connection(quantity):
    def forbidden_factory():
        pytest.fail(
            "Invalid quantity must be rejected before database access"
        )

    with pytest.raises(
        ValueError, match="Quantity must be a positive integer"
    ):
        BorrowingRepository(forbidden_factory).create_pending_request(
            7, 4, quantity, "2026-11-18", "2026-12-01"
        )


@pytest.mark.parametrize("commit", [True, False])
def test_shared_connection_leaves_transaction_to_caller(database, commit):
    conn = WriteConnection(database)
    conn.start_transaction()

    BorrowingRepository().create_pending_request(
        7, 4, 2, "2026-11-18", "2026-12-01", connection=conn
    )

    assert not conn.closed
    assert conn.last_cursor.closed
    assert conn.commits == 0
    assert conn.raw.in_transaction
    assert saved_counts(database) == (0, 0)

    if commit:
        conn.commit()
        assert saved_counts(database) == (1, 2)
    else:
        conn.rollback()
        assert saved_counts(database) == (0, 0)

    conn.close()


def test_commit_failure_rolls_back_all_changes(database):
    conn = WriteConnection(database, fail_commit=True)

    with pytest.raises(RuntimeError, match="Simulated commit failure"):
        BorrowingRepository(lambda: conn).create_pending_request(
            7, 4, 2, "2026-11-18", "2026-12-01"
        )

    assert saved_counts(database) == (0, 0)
    assert conn.rollbacks == 1
    assert conn.closed


def test_shared_connection_error_can_be_rolled_back_by_caller(database):
    conn = WriteConnection(database)
    conn.start_transaction()

    with pytest.raises(sqlite3.IntegrityError):
        BorrowingRepository().create_pending_request(
            7, 999, 2, "2026-11-18", "2026-12-01", connection=conn
        )

    assert not conn.closed
    assert conn.rollbacks == 0

    conn.rollback()

    assert saved_counts(database) == (0, 0)
    conn.close()
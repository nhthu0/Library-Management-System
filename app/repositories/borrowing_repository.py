from app.database.connection import get_connection


class BorrowingRepository:
    def __init__(self, connection_factory=None):
        self._get_connection = (
            connection_factory
            if connection_factory is not None
            else get_connection
        )

    def count_active_books(self, reader_id: int, connection=None) -> int:
        """Count unreturned copies, including returns awaiting confirmation."""
        owns_connection = connection is None
        conn = self._get_connection() if owns_connection else connection
        cursor = None

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM borrowing_details AS d
                JOIN borrowing_records AS r
                    ON r.borrowingID = d.borrowingID
                WHERE r.readerID = %s
                  AND r.status IN (%s, %s)
                  AND d.return_date IS NULL
                """,
                (reader_id, "Borrowed", "ReturnRequested"),
            )
            return int(cursor.fetchone()[0])

        finally:
            try:
                if cursor is not None:
                    cursor.close()
            finally:
                if owns_connection:
                    conn.close()

    def create_pending_request(
        self,
        reader_id: int,
        book_id: int,
        quantity: int,
        borrow_date: str,
        due_date: str,
        connection=None,
    ) -> int:
        """Save a pending request with one detail row per book copy.

        The caller controls commit and rollback when supplying a connection.
        """
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        owns_connection = connection is None
        conn = self._get_connection() if owns_connection else connection
        cursor = None

        try:
            if owns_connection:
                conn.start_transaction()

            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO borrowing_records
                    (readerID, borrow_date, due_date, status)
                VALUES (%s, %s, %s, %s)
                """,
                (reader_id, borrow_date, due_date, "Pending"),
            )
            borrowing_id = int(cursor.lastrowid)

            cursor.executemany(
                """
                INSERT INTO borrowing_details (borrowingID, bookID)
                VALUES (%s, %s)
                """,
                [(borrowing_id, book_id) for _ in range(quantity)],
            )

            if owns_connection:
                conn.commit()

            return borrowing_id

        except Exception:
            if owns_connection:
                conn.rollback()
            raise

        finally:
            try:
                if cursor is not None:
                    cursor.close()
            finally:
                if owns_connection:
                    conn.close()

    def get_reader_for_update(self, user_id: int, connection):
        """Read and lock the Reader account within the caller's transaction."""
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT r.readerID AS reader_id,
                       r.expiration_date,
                       u.role,
                       u.account_status
                FROM readers AS r
                JOIN users AS u ON u.userID = r.userID
                WHERE u.userID = %s
                FOR UPDATE
                """,
                (user_id,),
            )
            return cursor.fetchone()

        finally:
            cursor.close()

    def count_active_copies_for_book(self, book_id: int, connection=None) -> int:
        """Count copies held by Readers until return confirmation."""
        owns_connection = connection is None
        conn = self._get_connection() if owns_connection else connection
        cursor = None

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM borrowing_details AS d
                JOIN borrowing_records AS r
                    ON r.borrowingID = d.borrowingID
                WHERE d.bookID = %s
                  AND r.status IN (%s, %s)
                  AND d.return_date IS NULL
                """,
                (book_id, "Borrowed", "ReturnRequested"),
            )
            return int(cursor.fetchone()[0])

        finally:
            try:
                if cursor is not None:
                    cursor.close()
            finally:
                if owns_connection:
                    conn.close()
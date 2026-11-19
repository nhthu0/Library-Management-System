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

    def get_own_borrowing_for_update(
        self, borrowing_id: int, reader_id: int, connection
    ):
        """Lock a Reader's own record in the caller's transaction."""
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT borrowingID AS borrowing_id,
                       readerID AS reader_id,
                       borrow_date, due_date, return_date, status
                FROM borrowing_records
                WHERE borrowingID = %s AND readerID = %s
                FOR UPDATE
                """,
                (borrowing_id, reader_id),
            )
            record = cursor.fetchone()
            if record is not None:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS quantity
                    FROM borrowing_details
                    WHERE borrowingID = %s AND return_date IS NULL
                    """,
                    (borrowing_id,),
                )
                record["quantity"] = int(cursor.fetchone()["quantity"])
            return record
        finally:
            cursor.close()

    def mark_return_requested(
        self, borrowing_id: int, reader_id: int, connection
    ) -> bool:
        """Change only a still-borrowed record; the caller commits or rolls back."""
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE borrowing_records
                SET status = %s
                WHERE borrowingID = %s AND readerID = %s
                  AND status = %s AND return_date IS NULL
                """,
                ("ReturnRequested", borrowing_id, reader_id, "Borrowed"),
            )
            return cursor.rowcount == 1
        finally:
            cursor.close()

    def get_reader_profile(self, user_id: int, connection):
        """Read the session owner's Reader profile without locking rows."""
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT r.readerID AS reader_id, u.role, u.account_status
                FROM readers AS r
                JOIN users AS u ON u.userID = r.userID
                WHERE u.userID = %s
                """,
                (user_id,),
            )
            return cursor.fetchone()
        finally:
            cursor.close()

    def get_reader_history_rows(self, reader_id: int, connection) -> list:
        """Return all loan states, grouping detail rows into book quantities."""
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT r.borrowingID AS borrowing_id,
                       r.readerID AS reader_id,
                       r.borrow_date, r.due_date, r.return_date,
                       r.status, r.renewal_count,
                       d.bookID AS book_id, b.title, b.author,
                       COUNT(d.detailID) AS quantity,
                       SUM(CASE WHEN d.return_date IS NOT NULL
                                THEN 1 ELSE 0 END) AS returned_quantity
                FROM borrowing_records AS r
                LEFT JOIN borrowing_details AS d
                    ON d.borrowingID = r.borrowingID
                LEFT JOIN books AS b ON b.bookID = d.bookID
                WHERE r.readerID = %s
                GROUP BY r.borrowingID, r.readerID, r.borrow_date,
                         r.due_date, r.return_date, r.status, r.renewal_count,
                         d.bookID, b.title, b.author
                ORDER BY r.borrow_date DESC, r.borrowingID DESC, d.bookID ASC
                """,
                (reader_id,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_admin_profile(self, user_id: int, connection):
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT a.adminID AS admin_id,
                       u.role, u.account_status
                FROM admins AS a
                JOIN users AS u ON u.userID = a.userID
                WHERE u.userID = %s
                """,
                (user_id,),
            )
            return cursor.fetchone()
        finally:
            cursor.close()

    def _fetch_approval(self, query, params, connection, many=False):
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall() if many else cursor.fetchone()
        finally:
            cursor.close()

    def get_borrowing_owner(self, borrowing_id: int, connection):
        return self._fetch_approval(
            """SELECT r.readerID AS reader_id, p.userID AS user_id
               FROM borrowing_records AS r
               JOIN readers AS p ON p.readerID = r.readerID
               WHERE r.borrowingID = %s""",
            (borrowing_id,), connection,
        )

    def get_request_books(self, borrowing_id: int, connection):
        return self._fetch_approval(
            """SELECT bookID AS book_id, COUNT(*) AS quantity,
                      SUM(CASE WHEN return_date IS NOT NULL THEN 1 ELSE 0 END)
                          AS returned_quantity
               FROM borrowing_details WHERE borrowingID = %s
               GROUP BY bookID ORDER BY bookID""",
            (borrowing_id,), connection, many=True,
        )

    def lock_requested_books(self, book_ids, connection):
        return {
            book_id: self._fetch_approval(
                "SELECT bookID AS book_id, status, quantity FROM books WHERE bookID = %s FOR UPDATE",
                (book_id,), connection,
            )
            for book_id in sorted(set(book_ids))
        }

    def save_borrow_decision(
        self, borrowing_id, reader_id, admin_id, status, borrow_date, due_date, connection
    ) -> bool:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """UPDATE borrowing_records
                   SET status = %s, adminID = %s, borrow_date = %s, due_date = %s
                   WHERE borrowingID = %s AND readerID = %s
                     AND status = %s AND return_date IS NULL""",
                (status, admin_id, borrow_date, due_date,
                 borrowing_id, reader_id, "Pending"),
            )
            return cursor.rowcount == 1
        finally:
            cursor.close()

    def get_admin_record_rows(self, status, connection):
        return self._fetch_approval(
            """
            SELECT r.borrowingID AS borrowing_id, r.readerID AS reader_id,
                   u.full_name AS reader_name, r.adminID AS admin_id,
                   r.borrow_date, r.due_date, r.return_date, r.status,
                   r.renewal_count, d.bookID AS book_id, b.title, b.author,
                   COUNT(d.detailID) AS quantity,
                   SUM(CASE WHEN d.return_date IS NOT NULL THEN 1 ELSE 0 END)
                       AS returned_quantity
            FROM borrowing_records AS r
            JOIN readers AS p ON p.readerID = r.readerID
            JOIN users AS u ON u.userID = p.userID
            LEFT JOIN borrowing_details AS d ON d.borrowingID = r.borrowingID
            LEFT JOIN books AS b ON b.bookID = d.bookID
            WHERE (%s IS NULL OR r.status = %s)
            GROUP BY r.borrowingID, r.readerID, u.full_name, r.adminID,
                     r.borrow_date, r.due_date, r.return_date, r.status,
                     r.renewal_count, d.bookID, b.title, b.author
            ORDER BY r.borrow_date, r.borrowingID, d.bookID
            """,
            (status, status), connection, many=True,
        )

    def mark_exhausted_books(self, book_ids, connection):
        if not book_ids:
            return
        cursor = connection.cursor()
        try:
            cursor.executemany(
                "UPDATE books SET status = %s WHERE bookID = %s",
                [("Unavailable", book_id) for book_id in book_ids],
            )
        finally:
            cursor.close()

    def get_return_details(self, borrowing_id, connection):
        return self._fetch_approval(
            """SELECT detailID AS detail_id, bookID AS book_id, return_date
               FROM borrowing_details WHERE borrowingID = %s
               ORDER BY detailID FOR UPDATE""",
            (borrowing_id,), connection, many=True,
        )

    def complete_return(self, borrowing_id, admin_id, returned_on, quantity, connection):
        cursor = connection.cursor()
        try:
            cursor.execute(
                """UPDATE borrowing_records
                   SET status = %s, adminID = %s, return_date = %s
                   WHERE borrowingID = %s AND status = %s AND return_date IS NULL""",
                ("Returned", admin_id, returned_on, borrowing_id, "ReturnRequested"),
            )
            if cursor.rowcount != 1:
                raise ValueError("This return request has changed. Please refresh.")
            cursor.execute(
                """UPDATE borrowing_details SET return_date = %s
                   WHERE borrowingID = %s AND return_date IS NULL""",
                (returned_on, borrowing_id),
            )
            if cursor.rowcount != quantity:
                raise ValueError("Return details have changed. Please refresh.")
        finally:
            cursor.close()

    def refresh_book_statuses(self, book_ids, connection):
        # The service already holds these book locks until commit.
        cursor = connection.cursor()
        try:
            for book_id in sorted(set(book_ids)):
                cursor.execute(
                    """UPDATE books SET status = CASE
                         WHEN quantity > (
                           SELECT COUNT(*) FROM borrowing_details AS d
                           JOIN borrowing_records AS r ON r.borrowingID = d.borrowingID
                           WHERE d.bookID = %s AND d.return_date IS NULL
                             AND r.status IN (%s, %s)
                         ) THEN %s ELSE %s END
                       WHERE bookID = %s""",
                    (book_id, "Borrowed", "ReturnRequested", "Available", "Unavailable", book_id),
                )
        finally:
            cursor.close()

    def save_overdue_fine(self, borrowing_id, amount, returned_on, admin_id, connection):
        """Record only the overdue charge; preserve paid and unrelated fines.

        This runs in the return transaction. TV5 can reuse it with the same
        connection; its payment controller remains responsible for payment.
        """
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT fineID, amount, payment_status FROM fines
                   WHERE borrowingID = %s AND reason = %s ORDER BY fineID FOR UPDATE""",
                (borrowing_id, "Overdue return"),
            )
            rows = cursor.fetchall()
            paid = sum(row["amount"] for row in rows if row["payment_status"] == "Paid")
            outstanding = max(0, amount - paid)
            unpaid = [row for row in rows if row["payment_status"] == "Unpaid"]
            if len(unpaid) > 1:
                raise ValueError("Multiple overdue charges require administrator review.")
            fine_id = rows[-1]["fineID"] if rows else None
            if unpaid:
                fine_id = unpaid[0]["fineID"]
                cursor.execute(
                    """UPDATE fines SET amount = %s, fine_date = %s, adminID = %s
                       WHERE fineID = %s AND payment_status = %s""",
                    (outstanding, returned_on, admin_id, fine_id, "Unpaid"),
                )
            elif outstanding:
                cursor.execute(
                    """INSERT INTO fines
                       (borrowingID, amount, reason, fine_date, payment_status, adminID)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (borrowing_id, outstanding, "Overdue return", returned_on, "Unpaid", admin_id),
                )
                fine_id = int(cursor.lastrowid)
            return {"fine_id": fine_id, "fine_amount": int(amount),
                    "unpaid_amount": float(outstanding)}
        finally:
            cursor.close()

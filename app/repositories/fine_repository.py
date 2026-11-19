
from app.database.connection import get_connection
from app.models.fine import Fine


class FineRepository:

    def get_borrowing_for_fine(self, borrowing_id: int) -> dict | None:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT borrowingID, readerID, adminID,
                    due_date, return_date, status
                FROM borrowing_records
                WHERE borrowingID = %s
                """,
                (borrowing_id,)
            )
            return cursor.fetchone()

        finally:
            cursor.close()
            conn.close()

    def get_borrowing_details(self, borrowing_id: int) -> list[dict]:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT detailID, borrowingID, bookID, return_date
                FROM borrowing_details
                WHERE borrowingID = %s
                ORDER BY detailID ASC
                """,
                (borrowing_id,)
            )
            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

    def get_by_borrowing_id(self, borrowing_id: int) -> Fine | None:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT *
                FROM fines
                WHERE borrowingID = %s
                ORDER BY fineID DESC
                LIMIT 1
                """,
                (borrowing_id,)
            )

            row = cursor.fetchone()

            if not row:
                return None

            return Fine(
                fine_id=row["fineID"],
                borrowing_id=row["borrowingID"],
                amount=row["amount"],
                reason=row["reason"],
                fine_date=row["fine_date"],
                payment_status=row["payment_status"],
                payment_date=row["payment_date"],
                admin_id=row["adminID"]
            )

        finally:
            cursor.close()
            conn.close()

    def create_fine(self, fine: Fine) -> Fine:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT borrowingID
                FROM borrowing_records
                WHERE borrowingID = %s
                FOR UPDATE
                """,
                (fine.borrowing_id,)
            )

            borrowing = cursor.fetchone()

            if not borrowing:
                raise ValueError("Borrowing record not found.")

            cursor.execute(
                """
                SELECT fineID
                FROM fines
                WHERE borrowingID = %s
                LIMIT 1
                """,
                (fine.borrowing_id,)
            )

            existing_fine = cursor.fetchone()

            if existing_fine:
                raise ValueError(
                    "A fine already exists for this borrowing record."
                )

            cursor.execute(
                """
                INSERT INTO fines (
                    borrowingID,
                    amount,
                    reason,
                    fine_date,
                    payment_status,
                    payment_date,
                    adminID
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    fine.borrowing_id,
                    fine.amount,
                    fine.reason,
                    fine.fine_date,
                    fine.payment_status,
                    fine.payment_date,
                    fine.admin_id
                )
            )

            fine.fine_id = cursor.lastrowid
            conn.commit()

            return fine

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    def get_fines_by_reader(self, reader_id: int) -> list[dict]:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    f.fineID AS fine_id,
                    f.borrowingID AS borrowing_id,
                    f.amount,
                    f.reason,
                    f.fine_date,
                    f.payment_status,
                    f.payment_date,
                    br.due_date,
                    br.return_date,

                    (
                        SELECT GROUP_CONCAT(
                            DISTINCT b.title
                            ORDER BY b.title
                            SEPARATOR ', '
                        )
                        FROM borrowing_details bd
                        JOIN books b
                            ON bd.bookID = b.bookID
                        WHERE bd.borrowingID = f.borrowingID
                    ) AS book_titles,

                    (
                        SELECT COALESCE(
                            SUM(
                                GREATEST(
                                    DATEDIFF(
                                        COALESCE(
                                            NULLIF(bd.return_date, ''),
                                            NULLIF(br.return_date, '')
                                        ),
                                        br.due_date
                                    ),
                                    0
                                )
                            ),
                            0
                        )
                        FROM borrowing_details bd
                        WHERE bd.borrowingID = f.borrowingID
                    ) AS days_overdue

                FROM fines f
                INNER JOIN borrowing_records br
                    ON f.borrowingID = br.borrowingID

                WHERE br.readerID = %s

                ORDER BY f.fine_date DESC, f.fineID DESC
                """,
                (reader_id,)
            )

            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

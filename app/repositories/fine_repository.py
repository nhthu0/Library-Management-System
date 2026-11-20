
from mysql.connector import Error, errorcode

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
            # Start transaction before acquiring the lock.
            conn.start_transaction(
                isolation_level="READ COMMITTED"
            )

            # Lock the borrowing record to prevent concurrent
            # fine creation for the same borrowing.
            cursor.execute(
                """
                SELECT borrowingID, status
                FROM borrowing_records
                WHERE borrowingID = %s
                FOR UPDATE
                """,
                (fine.borrowing_id,)
            )

            borrowing = cursor.fetchone()

            if not borrowing:
                raise ValueError("Borrowing record not found.")

            if borrowing["status"] != "Returned":
                raise ValueError(
                    "Fine can only be created for returned borrowing records."
                )

            # Check whether a fine already exists.
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

            # Insert the new fine.
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

    # LMS-45: Confirm fine payment.
    def confirm_payment(
        self,
        fine_id: int,
        payment_date: str
    ) -> dict | None:

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction(
                isolation_level="READ COMMITTED"
            )

            cursor.execute(
                """
                SELECT
                    fineID AS fine_id,
                    amount,
                    payment_status,
                    payment_date
                FROM fines
                WHERE fineID = %s
                FOR UPDATE
                """,
                (fine_id,)
            )

            fine = cursor.fetchone()

            if not fine:
                conn.rollback()
                return None

            if fine["payment_status"] == "Paid":
                raise ValueError(
                    "Fine has already been paid."
                )

            if fine["payment_status"] != "Unpaid":
                raise ValueError(
                    "Invalid fine payment status."
                )

            # Lock orders after the fine, matching the online payment service.
            try:
                cursor.execute(
                    "SELECT state FROM fine_momo_orders WHERE fineID = %s FOR UPDATE",
                    (fine_id,),
                )
                order = cursor.fetchone()
            except Error as error:
                if error.errno != errorcode.ER_NO_SUCH_TABLE:
                    raise
                order = None
            if order and order["state"] == "Pending":
                raise ValueError("This fine has a pending MoMo payment. Check its status first.")

            cursor.execute(
                """
                UPDATE fines
                SET payment_status = 'Paid',
                    payment_date = %s
                WHERE fineID = %s
                  AND payment_status = 'Unpaid'
                """,
                (payment_date, fine_id)
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Unable to confirm fine payment."
                )

            conn.commit()

            fine["payment_status"] = "Paid"
            fine["payment_date"] = payment_date

            return fine

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

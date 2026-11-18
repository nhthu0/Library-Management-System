from app.database.connection import get_connection
from app.models.fine import Fine

class FineRepository:

    def _row_to_fine(self, row: dict | None) -> Fine | None:
        if not row:
            return None

        return Fine(
            fine_id=row.get("fineID"),
            borrowing_id=row.get("borrowingID"),
            days_overdue=row.get("days_overdue", 0),
            amount=row.get("amount", 0),
            reason=row.get("reason"),
            fine_date=row.get("fine_date"),
            status=row.get("payment_status", "Unpaid"),
            payment_date=row.get("payment_date"),
            admin_id=row.get("adminID")
        )

    def get_borrowing_for_fine(self, borrowing_id: int) -> dict | None:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    borrowingID,
                    readerID,
                    adminID,
                    due_date,
                    return_date,
                    status
                FROM borrowing_records
                WHERE borrowingID = %s
                """,
                (borrowing_id,)
            )
            borrowing = cursor.fetchone()

            if not borrowing:
                return None

            cursor.execute(
                """
                SELECT
                    detailID,
                    bookID,
                    return_date
                FROM borrowing_details
                WHERE borrowingID = %s
                ORDER BY detailID ASC
                """,
                (borrowing_id,)
            )

            borrowing["details"] = cursor.fetchall()
            return borrowing

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
                LIMIT 1
                """,
                (borrowing_id,)
            )

            return self._row_to_fine(cursor.fetchone())

        finally:
            cursor.close()
            conn.close()

    def save_calculated_fine(
        self,
        borrowing_id: int,
        amount: float,
        days_overdue: int,
        reason: str,
        fine_date: str
    ) -> Fine:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction()
            cursor.execute(
                """
                SELECT borrowingID
                FROM borrowing_records
                WHERE borrowingID = %s
                FOR UPDATE
                """,
                (borrowing_id,)
            )

            if not cursor.fetchone():
                raise ValueError("Borrowing record does not exist.")

            cursor.execute(
                """
                SELECT *
                FROM fines
                WHERE borrowingID = %s
                LIMIT 1
                FOR UPDATE
                """,
                (borrowing_id,)
            )

            existing = cursor.fetchone()

            if existing:
                if existing["payment_status"] == "Paid":
                    conn.commit()
                    return self._row_to_fine(existing)

                cursor.execute(
                    """
                    UPDATE fines
                    SET amount = %s,
                        reason = %s,
                        fine_date = %s
                    WHERE fineID = %s
                    """,
                    (
                        amount,
                        reason,
                        fine_date,
                        existing["fineID"]
                    )
                )

                fine_id = existing["fineID"]

            else:
                cursor.execute(
                    """
                    INSERT INTO fines (
                        borrowingID,
                        amount,
                        reason,
                        fine_date,
                        payment_status
                    )
                    VALUES (%s, %s, %s, %s, 'Unpaid')
                    """,
                    (
                        borrowing_id,
                        amount,
                        reason,
                        fine_date
                    )
                )

                fine_id = cursor.lastrowid

            conn.commit()

            cursor.execute(
                "SELECT * FROM fines WHERE fineID = %s",
                (fine_id,)
            )

            row = cursor.fetchone()
            fine = self._row_to_fine(row)

            if fine:
                fine.days_overdue = days_overdue

            return fine

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    def _get_fines(self, reader_id: int | None = None) -> list[Fine]:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            sql = """
                SELECT
                    f.*,
                    COALESCE(
                        SUM(
                            GREATEST(
                                DATEDIFF(
                                    STR_TO_DATE(
                                        COALESCE(bd.return_date, br.return_date),
                                        '%Y-%m-%d'
                                    ),
                                    STR_TO_DATE(br.due_date, '%Y-%m-%d')
                                ),
                                0
                            )
                        ),
                        0
                    ) AS days_overdue
                FROM fines f
                INNER JOIN borrowing_records br
                    ON f.borrowingID = br.borrowingID
                LEFT JOIN borrowing_details bd
                    ON br.borrowingID = bd.borrowingID
            """

            params = []

            if reader_id is not None:
                sql += " WHERE br.readerID = %s"
                params.append(reader_id)

            sql += """
                GROUP BY
                    f.fineID,
                    f.borrowingID,
                    f.amount,
                    f.reason,
                    f.fine_date,
                    f.payment_status,
                    f.payment_date,
                    f.adminID
                ORDER BY f.fineID DESC
            """

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

            return [self._row_to_fine(row) for row in rows]

        finally:
            cursor.close()
            conn.close()

    def get_all(self) -> list[Fine]:
        return self._get_fines()

    def get_by_reader_id(self, reader_id: int) -> list[Fine]:
        return self._get_fines(reader_id)

    def confirm_payment(self, fine_id: int, admin_id: int) -> Fine | None:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            conn.start_transaction()

            cursor.execute(
                """
                SELECT *
                FROM fines
                WHERE fineID = %s
                FOR UPDATE
                """,
                (fine_id,)
            )

            fine = cursor.fetchone()

            if not fine:
                raise ValueError("Fine not found.")

            if fine["payment_status"] == "Paid":
                raise ValueError("This fine has already been paid.")

            cursor.execute(
                """
                UPDATE fines
                SET payment_status = 'Paid',
                    payment_date = %s,
                    adminID = %s
                WHERE fineID = %s
                """,
                (
                    __import__("datetime").date.today().isoformat(),
                    admin_id,
                    fine_id
                )
            )

            conn.commit()

            cursor.execute(
                "SELECT * FROM fines WHERE fineID = %s",
                (fine_id,)
            )

            return self._row_to_fine(cursor.fetchone())

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

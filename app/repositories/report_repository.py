from app.database.connection import get_connection


class ReportRepository:

    def get_book_statistics(self) -> dict:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    COUNT(bookID) AS total_titles,
                    COALESCE(SUM(quantity), 0) AS total_quantity,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN status = 'Available' THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS available_titles,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN status = 'Unavailable' THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS unavailable_titles
                FROM books
                """
            )

            summary = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                    category,
                    COUNT(bookID) AS total_titles,
                    COALESCE(SUM(quantity), 0) AS total_quantity
                FROM books
                GROUP BY category
                ORDER BY category ASC
                """
            )

            categories = cursor.fetchall()

            return {
                "total_titles": summary["total_titles"],
                "total_quantity": summary["total_quantity"],
                "available_titles": summary["available_titles"],
                "unavailable_titles": summary["unavailable_titles"],
                "by_category": categories
            }

        finally:
            cursor.close()
            conn.close()

    # LMS-47: Reader Statistics
    def get_reader_statistics(self) -> dict:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    COUNT(r.readerID) AS total_readers,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN u.account_status = 'Active' THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS active_readers,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN u.account_status = 'Locked' THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS locked_readers,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN u.account_status = 'Inactive' THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS inactive_readers
                FROM readers r
                INNER JOIN users u ON r.userID = u.userID
                WHERE u.role = 'Reader'
                """
            )
            summary = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                    u.account_status,
                    COUNT(r.readerID) AS total_readers
                FROM readers r
                INNER JOIN users u ON r.userID = u.userID
                WHERE u.role = 'Reader'
                GROUP BY u.account_status
                ORDER BY u.account_status ASC
                """
            )
            statuses = cursor.fetchall()

            return {
                "total_readers": summary["total_readers"],
                "active_readers": summary["active_readers"],
                "locked_readers": summary["locked_readers"],
                "inactive_readers": summary["inactive_readers"],
                "by_status": statuses
            }

        finally:
            cursor.close()
            conn.close()

    # LMS-48: Borrowing and Returning Statistics

    def get_borrowing_report(
        self,
        start_date: str,
        end_date: str
    ) -> dict:

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT COUNT(*) AS total_borrowings
                FROM borrowing_records
                WHERE borrow_date BETWEEN %s AND %s
                """,
                (start_date, end_date)
            )
            borrowing_summary = cursor.fetchone()

            cursor.execute(
                """
                SELECT COUNT(*) AS total_returns
                FROM borrowing_records
                WHERE return_date IS NOT NULL
                    AND return_date != ''
                    AND return_date BETWEEN %s AND %s
                """,
                (start_date, end_date)
            )
            return_summary = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                    borrow_date AS report_date,
                    COUNT(*) AS total
                FROM borrowing_records
                WHERE borrow_date BETWEEN %s AND %s
                GROUP BY borrow_date
                ORDER BY borrow_date ASC
                """,
                (start_date, end_date)
            )
            borrowings_by_date = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    return_date AS report_date,
                    COUNT(*) AS total
                FROM borrowing_records
                WHERE return_date IS NOT NULL
                    AND return_date != ''
                    AND return_date BETWEEN %s AND %s
                GROUP BY return_date
                ORDER BY return_date ASC
                """,
                (start_date, end_date)
            )
            returns_by_date = cursor.fetchall()

            return {
                "total_borrowings": borrowing_summary["total_borrowings"],
                "total_returns": return_summary["total_returns"],
                "borrowings_by_date": borrowings_by_date,
                "returns_by_date": returns_by_date
            }

        finally:
            cursor.close()
            conn.close()

    # LMS-49: Book Status Statistics

    def get_book_status_statistics(self) -> dict:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    COUNT(
                        CASE
                            WHEN br.status = 'Borrowed'
                                AND NULLIF(bd.return_date, '') IS NULL
                                AND NULLIF(br.return_date, '') IS NULL
                            THEN 1
                        END
                    ) AS currently_borrowed,

                    COUNT(
                        CASE
                            WHEN NULLIF(bd.return_date, '') IS NOT NULL
                                OR NULLIF(br.return_date, '') IS NOT NULL
                            THEN 1
                        END
                    ) AS returned,

                    COUNT(
                        CASE
                            WHEN br.status = 'Borrowed'
                                AND NULLIF(bd.return_date, '') IS NULL
                                AND NULLIF(br.return_date, '') IS NULL
                                AND br.due_date < CURDATE()
                            THEN 1
                        END
                    ) AS overdue

                FROM borrowing_details bd
                INNER JOIN borrowing_records br
                    ON bd.borrowingID = br.borrowingID
                """
            )

            result = cursor.fetchone()

            return {
                "currently_borrowed": result["currently_borrowed"],
                "returned": result["returned"],
                "overdue": result["overdue"]
            }

        finally:
            cursor.close()
            conn.close()

    # LMS-49: Fine Statistics

    def get_fine_statistics(self) -> dict:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    COUNT(fineID) AS total_fines,

                    COALESCE(SUM(amount), 0) AS total_amount,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_status = 'Paid'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS paid_amount,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_status = 'Unpaid'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS unpaid_amount,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_status = 'Paid'
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS paid_count,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_status = 'Unpaid'
                                THEN 1
                                ELSE 0
                            END
                        ),
                        0
                    ) AS unpaid_count

                FROM fines
                """
            )

            result = cursor.fetchone()

            return {
                "total_fines": result["total_fines"],
                "total_amount": result["total_amount"],
                "paid_amount": result["paid_amount"],
                "unpaid_amount": result["unpaid_amount"],
                "paid_count": result["paid_count"],
                "unpaid_count": result["unpaid_count"]
            }

        finally:
            cursor.close()
            conn.close()

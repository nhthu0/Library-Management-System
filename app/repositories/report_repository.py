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

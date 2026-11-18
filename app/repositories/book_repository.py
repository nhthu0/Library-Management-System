
from app.database.connection import get_connection
from app.models.book import Book


class BookRepository:
    def _row_to_book(self, row: dict | None) -> Book | None:
        if not row:
            return None

        return Book(
            book_id=row["bookID"],
            title=row["title"],
            author=row["author"],
            category=row["category"],
            publisher=row.get("publisher"),
            publication_year=row.get("publication_year"),
            status=row["status"],
            quantity=row["quantity"],
            available_quantity=max(0, int(row["quantity"]) - int(row.get("borrowed_quantity", 0))),
        )

    def get_all(self) -> list[Book]:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(self._book_select() + " ORDER BY b.bookID ASC")
            rows = cursor.fetchall()
            return [self._row_to_book(row) for row in rows]

        finally:
            cursor.close()
            conn.close()

    def get_by_id(self, book_id: int) -> Book | None:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                self._book_select() + " WHERE b.bookID = %s",
                (book_id,)
            )
            return self._row_to_book(cursor.fetchone())

        finally:
            cursor.close()
            conn.close()

    def search(self, keyword: str) -> list[Book]:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            like_kw = f"%{keyword}%"

            query = self._book_select() + """
                WHERE b.title LIKE %s
                   OR b.author LIKE %s
                   OR b.category LIKE %s
                   OR CAST(b.bookID AS CHAR) LIKE %s
                ORDER BY b.bookID ASC
            """

            cursor.execute(
                query,
                (like_kw, like_kw, like_kw, like_kw)
            )

            rows = cursor.fetchall()
            return [self._row_to_book(row) for row in rows]

        finally:
            cursor.close()
            conn.close()

    def create(self, book: Book) -> Book:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            query = """
                INSERT INTO books (
                    title,
                    author,
                    category,
                    publisher,
                    publication_year,
                    status,
                    quantity
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                book.title,
                book.author,
                book.category,
                book.publisher,
                book.publication_year,
                book.status,
                book.quantity
            )

            cursor.execute(query, values)
            conn.commit()

            book.book_id = cursor.lastrowid
            return book

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    def update(self, book: Book) -> bool:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            conn.start_transaction(isolation_level="READ COMMITTED")
            cursor.execute("SELECT bookID FROM books WHERE bookID = %s FOR UPDATE", (book.book_id,))
            if cursor.fetchone() is None:
                conn.rollback()
                return False
            cursor.execute(
                """SELECT COUNT(*) FROM borrowing_details AS d
                   JOIN borrowing_records AS r ON r.borrowingID = d.borrowingID
                   WHERE d.bookID = %s AND d.return_date IS NULL
                     AND r.status IN (%s, %s)""",
                (book.book_id, "Borrowed", "ReturnRequested"),
            )
            held = int(cursor.fetchone()[0])
            if book.quantity < held:
                raise ValueError("Total quantity cannot be less than the number of unreturned copies.")
            available = book.quantity - held
            if available <= 0:
                book.status = "Unavailable"
            query = """
                UPDATE books
                SET title = %s,
                    author = %s,
                    category = %s,
                    publisher = %s,
                    publication_year = %s,
                    status = %s,
                    quantity = %s
                WHERE bookID = %s
            """

            values = (
                book.title,
                book.author,
                book.category,
                book.publisher,
                book.publication_year,
                book.status,
                book.quantity,
                book.book_id
            )

            cursor.execute(query, values)
            changed = cursor.rowcount > 0
            conn.commit()
            book.available_quantity = available if book.status == "Available" else 0
            return changed

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    def has_borrowing_records(self, book_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT COUNT(*) FROM borrowing_details WHERE bookID = %s",
                (book_id,)
            )

            count = cursor.fetchone()[0]
            return count > 0

        finally:
            cursor.close()
            conn.close()

    def delete(self, book_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM books WHERE bookID = %s",
                (book_id,)
            )

            conn.commit()
            return cursor.rowcount > 0

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def _book_select():
        return """
            SELECT b.*,
                   (SELECT COUNT(*) FROM borrowing_details AS d
                    JOIN borrowing_records AS r ON r.borrowingID = d.borrowingID
                    WHERE d.bookID = b.bookID AND d.return_date IS NULL
                      AND r.status IN ('Borrowed', 'ReturnRequested')) AS borrowed_quantity
            FROM books AS b
        """

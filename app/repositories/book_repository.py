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
            quantity=row["quantity"]
        )

    def get_all(self) -> list[Book]:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM books ORDER BY bookID ASC")
            rows = cursor.fetchall()
            return [self._row_to_book(row) for row in rows]
        finally:
            cursor.close()
            conn.close()

    def get_by_id(self, book_id: int) -> Book | None:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM books WHERE bookID = %s", (book_id,))
            return self._row_to_book(cursor.fetchone())
        finally:
            cursor.close()
            conn.close()

    def search(self, keyword: str) -> list[Book]:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            like_kw = f"%{keyword}%"
            query = """
                SELECT * FROM books
                WHERE title LIKE %s
                   OR author LIKE %s
                   OR category LIKE %s
                   OR CAST(bookID AS CHAR) LIKE %s
                ORDER BY bookID ASC
            """
            cursor.execute(query, (like_kw, like_kw, like_kw, like_kw))
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
                INSERT INTO books (title, author, category, publisher, publication_year, status, quantity)
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
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update(self, book: Book) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        try:
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
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def has_borrowing_records(self, book_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM borrowing_details WHERE bookID = %s", (book_id,))
            count = cursor.fetchone()[0]
            return count > 0
        finally:
            cursor.close()
            conn.close()

    def delete(self, book_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM books WHERE bookID = %s", (book_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
from app.models.book import Book
from app.repositories.book_repository import BookRepository


class BookService:
    VALID_STATUSES = ("Available", "Unavailable")

    def __init__(self):
        self.repo = BookRepository()

    def _require_admin(self, current_user: dict | None):
        role = str(current_user.get("role", "")).upper() if isinstance(current_user, dict) else ""
        if role != "ADMIN":
            raise PermissionError("Access denied: Admin permission required.")

    def _validate_book_fields(
        self,
        title: str,
        author: str,
        category: str,
        publisher: str | None,
        publication_year: int | None,
        quantity: int,
        status: str
    ):
        if not title or len(title) > 200:
            raise ValueError("Book title is required and must not exceed 200 characters.")
        if not author or len(author) > 150:
            raise ValueError("Author is required and must not exceed 150 characters.")
        if not category or len(category) > 100:
            raise ValueError("Category is required and must not exceed 100 characters.")
        if publisher is not None and len(str(publisher)) > 150:
            raise ValueError("Publisher must not exceed 150 characters.")
        if publication_year is not None:
            if not isinstance(publication_year, int) or publication_year < 0 or publication_year > 2100:
                raise ValueError("Publication year is invalid.")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        if status not in self.VALID_STATUSES:
            raise ValueError("Status must be 'Available' or 'Unavailable'.")

    def get_all_books(self) -> list[dict]:
        books = self.repo.get_all()
        return [book.to_dict() for book in books]

    def get_book_by_id(self, book_id: int) -> dict:
        if not isinstance(book_id, int) or book_id <= 0:
            raise ValueError("Invalid book ID.")
        book = self.repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"Book with ID {book_id} not found.")
        return book.to_dict()

    def search_books(self, keyword: str) -> list[dict]:
        if keyword is None or not str(keyword).strip():
            return self.get_all_books()
        books = self.repo.search(str(keyword).strip())
        return [book.to_dict() for book in books]

    def check_book_availability(self, book_id: int) -> dict:
        if not isinstance(book_id, int) or book_id <= 0:
            raise ValueError("Invalid book ID.")
        book = self.repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"Book with ID {book_id} not found.")
        is_available = (book.status == "Available" and book.quantity > 0)
        return {
            "book_id": book.book_id,
            "title": book.title,
            "status": book.status,
            "is_available": is_available,
            "available_quantity": book.quantity if is_available else 0
        }

    def add_book(self, book_data: dict, current_user: dict | None) -> dict:
        self._require_admin(current_user)
        if not isinstance(book_data, dict):
            raise ValueError("Invalid book data.")

        title = str(book_data.get("title", "")).strip()
        author = str(book_data.get("author", "")).strip()
        category = str(book_data.get("category", "")).strip()
        publisher = str(book_data["publisher"]).strip() if book_data.get("publisher") else None

        pub_year_raw = book_data.get("publication_year")
        publication_year = int(pub_year_raw) if pub_year_raw not in (None, "") else None

        qty_raw = book_data.get("quantity", book_data.get("total_quantity", 0))
        try:
            quantity = int(qty_raw)
        except (TypeError, ValueError):
            raise ValueError("Quantity must be an integer.")

        default_status = "Available" if quantity > 0 else "Unavailable"
        status = book_data.get("status", default_status)
        if quantity == 0:
            status = "Unavailable"

        self._validate_book_fields(
            title, author, category, publisher, publication_year, quantity, status
        )

        new_book = Book(
            title=title,
            author=author,
            category=category,
            publisher=publisher,
            publication_year=publication_year,
            status=status,
            quantity=quantity
        )
        created_book = self.repo.create(new_book)
        return created_book.to_dict()

    def update_book(self, book_id: int, book_data: dict, current_user: dict | None) -> dict:
        self._require_admin(current_user)
        if not isinstance(book_id, int) or book_id <= 0:
            raise ValueError("Invalid book ID.")
        if not isinstance(book_data, dict):
            raise ValueError("Invalid book data.")

        existing = self.repo.get_by_id(book_id)
        if not existing:
            raise ValueError(f"Book with ID {book_id} not found.")

        title = str(book_data.get("title", existing.title)).strip()
        author = str(book_data.get("author", existing.author)).strip()
        category = str(book_data.get("category", existing.category)).strip()

        if "publisher" in book_data:
            publisher = str(book_data["publisher"]).strip() if book_data["publisher"] else None
        else:
            publisher = existing.publisher

        if "publication_year" in book_data:
            pub_year_raw = book_data["publication_year"]
            publication_year = int(pub_year_raw) if pub_year_raw not in (None, "") else None
        else:
            publication_year = existing.publication_year

        if "quantity" in book_data or "total_quantity" in book_data:
            qty_raw = book_data.get("quantity", book_data.get("total_quantity"))
            try:
                quantity = int(qty_raw)
            except (TypeError, ValueError):
                raise ValueError("Quantity must be an integer.")
        else:
            quantity = existing.quantity

        if "status" in book_data:
            status = book_data["status"]
        else:
            status = "Available" if quantity > 0 else "Unavailable"

        if quantity == 0:
            status = "Unavailable"

        self._validate_book_fields(
            title, author, category, publisher, publication_year, quantity, status
        )

        existing.title = title
        existing.author = author
        existing.category = category
        existing.publisher = publisher
        existing.publication_year = publication_year
        existing.status = status
        existing.quantity = quantity

        self.repo.update(existing)
        return existing.to_dict()

    def delete_book(self, book_id: int, current_user: dict | None) -> dict:
        self._require_admin(current_user)
        if not isinstance(book_id, int) or book_id <= 0:
            raise ValueError("Invalid book ID.")

        existing = self.repo.get_by_id(book_id)
        if not existing:
            raise ValueError(f"Book with ID {book_id} not found.")

        if self.repo.has_borrowing_records(book_id):
            raise ValueError("Cannot delete book because it has existing borrowing records.")

        self.repo.delete(book_id)
        return {"book_id": book_id}
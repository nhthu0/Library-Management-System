
from app.models.book import Book
from app.repositories.book_repository import BookRepository


class BookService:
    VALID_STATUSES = ("Available", "Unavailable")

    def __init__(self):
        self.repo = BookRepository()

    def _require_admin(self, current_user: dict | None):
        role = (
            str(current_user.get("role", "")).upper()
            if isinstance(current_user, dict)
            else ""
        )

        if role != "ADMIN":
            raise PermissionError(
                "Access denied: Admin permission required."
            )

    def _parse_integer(self, value, field_name: str) -> int:
        if isinstance(value, bool):
            raise ValueError(
                f"{field_name} must be an integer."
            )

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            value = value.strip()

            if value and value.isdecimal():
                return int(value)

        raise ValueError(
            f"{field_name} must be an integer."
        )

    def _parse_required_text(
        self,
        value,
        field_name: str
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"{field_name} must be a string."
            )

        return value.strip()

    def _parse_publisher(self, value) -> str | None:
        if value is None or value == "":
            return None

        if not isinstance(value, str):
            raise ValueError(
                "Publisher must be a string."
            )

        publisher = value.strip()
        return publisher if publisher else None

    def _parse_publication_year(self, value) -> int | None:
        if value is None or value == "":
            return None

        return self._parse_integer(
            value,
            "Publication year"
        )

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
            raise ValueError(
                "Book title is required and must not exceed 200 characters."
            )

        if not author or len(author) > 150:
            raise ValueError(
                "Author is required and must not exceed 150 characters."
            )

        if not category or len(category) > 100:
            raise ValueError(
                "Category is required and must not exceed 100 characters."
            )

        if publisher is not None and len(publisher) > 150:
            raise ValueError(
                "Publisher must not exceed 150 characters."
            )

        if publication_year is not None:
            if (
                not isinstance(publication_year, int)
                or isinstance(publication_year, bool)
                or publication_year < 0
                or publication_year > 2100
            ):
                raise ValueError(
                    "Publication year is invalid."
                )

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
        ):
            raise ValueError(
                "Quantity must be an integer."
            )

        if quantity < 0:
            raise ValueError(
                "Quantity cannot be negative."
            )

        if status not in self.VALID_STATUSES:
            raise ValueError(
                "Status must be 'Available' or 'Unavailable'."
            )

    def _validate_book_id(self, book_id: int):
        if (
            not isinstance(book_id, int)
            or isinstance(book_id, bool)
            or book_id <= 0
        ):
            raise ValueError("Invalid book ID.")

    def get_all_books(self) -> list[dict]:
        books = self.repo.get_all()
        return [
            book.to_dict()
            for book in books
        ]

    def get_book_by_id(self, book_id: int) -> dict:
        self._validate_book_id(book_id)

        book = self.repo.get_by_id(book_id)

        if not book:
            raise ValueError(
                f"Book with ID {book_id} not found."
            )

        return book.to_dict()

    def search_books(self, keyword: str) -> list[dict]:
        if keyword is None or not str(keyword).strip():
            return self.get_all_books()

        books = self.repo.search(
            str(keyword).strip()
        )

        return [
            book.to_dict()
            for book in books
        ]

    def check_book_availability(self, book_id: int) -> dict:
        self._validate_book_id(book_id)

        book = self.repo.get_by_id(book_id)

        if not book:
            raise ValueError(
                f"Book with ID {book_id} not found."
            )

        data = book.to_dict()
        is_available = data["available_quantity"] > 0

        return {
            "book_id": book.book_id,
            "title": book.title,
            "status": data["status"],
            "is_available": is_available,
            "available_quantity": data["available_quantity"],
        }

    def add_book(
        self,
        book_data: dict,
        current_user: dict | None
    ) -> dict:
        self._require_admin(current_user)

        if not isinstance(book_data, dict):
            raise ValueError("Invalid book data.")

        title = self._parse_required_text(
            book_data.get("title"),
            "Book title"
        )

        author = self._parse_required_text(
            book_data.get("author"),
            "Author"
        )

        category = self._parse_required_text(
            book_data.get("category"),
            "Category"
        )

        publisher = self._parse_publisher(
            book_data.get("publisher")
        )

        publication_year = self._parse_publication_year(
            book_data.get("publication_year")
        )

        qty_raw = book_data.get(
            "quantity",
            book_data.get("total_quantity", 0)
        )

        quantity = self._parse_integer(
            qty_raw,
            "Quantity"
        )

        default_status = (
            "Available"
            if quantity > 0
            else "Unavailable"
        )

        status = book_data.get(
            "status",
            default_status
        )

        if quantity == 0:
            status = "Unavailable"

        self._validate_book_fields(
            title,
            author,
            category,
            publisher,
            publication_year,
            quantity,
            status
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

    def update_book(
        self,
        book_id: int,
        book_data: dict,
        current_user: dict | None
    ) -> dict:
        self._require_admin(current_user)
        self._validate_book_id(book_id)

        if not isinstance(book_data, dict):
            raise ValueError("Invalid book data.")

        existing = self.repo.get_by_id(book_id)

        if not existing:
            raise ValueError(
                f"Book with ID {book_id} not found."
            )

        title = self._parse_required_text(
            book_data.get("title", existing.title),
            "Book title"
        )

        author = self._parse_required_text(
            book_data.get("author", existing.author),
            "Author"
        )

        category = self._parse_required_text(
            book_data.get("category", existing.category),
            "Category"
        )

        publisher = self._parse_publisher(
            book_data.get("publisher", existing.publisher)
        )

        publication_year = self._parse_publication_year(
            book_data.get(
                "publication_year",
                existing.publication_year
            )
        )

        if (
            "quantity" in book_data
            or "total_quantity" in book_data
        ):
            qty_raw = book_data.get(
                "quantity",
                book_data.get("total_quantity")
            )

            quantity = self._parse_integer(
                qty_raw,
                "Quantity"
            )
        else:
            quantity = existing.quantity

        if "status" in book_data:
            status = book_data["status"]

        elif quantity == 0:
            status = "Unavailable"

        elif quantity > existing.quantity and (
            existing.quantity == 0 or existing.available_quantity == 0
        ):
            status = "Available"

        else:
            status = existing.status

        if quantity == 0:
            status = "Unavailable"

        self._validate_book_fields(
            title,
            author,
            category,
            publisher,
            publication_year,
            quantity,
            status
        )

        existing.title = title
        existing.author = author
        existing.category = category
        existing.publisher = publisher
        existing.publication_year = publication_year
        existing.status = status
        existing.quantity = quantity

        updated = self.repo.update(existing)

        if not updated:
            current_book = self.repo.get_by_id(book_id)

            if current_book is None:
                raise ValueError(
                    f"Book with ID {book_id} no longer exists."
                )

        return existing.to_dict()

    def delete_book(
        self,
        book_id: int,
        current_user: dict | None
    ) -> dict:
        self._require_admin(current_user)
        self._validate_book_id(book_id)

        existing = self.repo.get_by_id(book_id)

        if not existing:
            raise ValueError(
                f"Book with ID {book_id} not found."
            )

        if self.repo.has_borrowing_records(book_id):
            raise ValueError(
                "Cannot delete book because it has existing borrowing records."
            )

        deleted = self.repo.delete(book_id)

        if not deleted:
            raise ValueError(
                "Book could not be deleted."
            )

        return {"book_id": book_id}

from app.repositories.book_repository import BookRepository


class BorrowingService:
    def __init__(self, book_repository=None):
        self.book_repo = (
            book_repository
            if book_repository is not None
            else BookRepository()
        )

    def _validate_book_availability(self, book_id: int, quantity: int):
        """Validate borrowing stock without changing book quantities."""
        if type(book_id) is not int or book_id <= 0:
            raise ValueError("Book ID must be a positive integer.")

        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        book = self.book_repo.get_by_id(book_id)

        if book is None:
            raise ValueError("Book not found.")

        if book.status != "Available" or book.quantity <= 0:
            raise ValueError("Book is currently unavailable.")

        if quantity > book.quantity:
            raise ValueError(
                f"Only {book.quantity} copies are available."
            )
        return book
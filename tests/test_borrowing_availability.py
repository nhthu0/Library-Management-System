import pytest

from app.models.book import Book
from app.services.borrowing_service import BorrowingService


class FakeBookRepository:
    def __init__(self, book):
        self.book = book
        self.lookups = []

    def get_by_id(self, book_id):
        self.lookups.append(book_id)
        if self.book is not None and self.book.book_id == book_id:
            return self.book
        return None


@pytest.mark.parametrize("quantity", [1, 2])
def test_valid_request_preserves_inventory(quantity):
    book = Book(book_id=1, title="Clean Code", quantity=2)
    original = book.to_dict().copy()
    repo = FakeBookRepository(book)
    service = BorrowingService(repo)

    result = service._validate_book_availability(1, quantity)

    assert result is book
    assert book.to_dict() == original
    assert repo.lookups == [1]


@pytest.mark.parametrize("book_id", [0, -1, True, 1.5, "1", None])
def test_invalid_book_ids_do_not_query_repository(book_id):
    repo = FakeBookRepository(None)

    with pytest.raises(ValueError, match="Book ID must be a positive integer"):
        BorrowingService(repo)._validate_book_availability(book_id, 1)

    assert repo.lookups == []


@pytest.mark.parametrize("quantity", [0, -1, True, 1.5, "1", None])
def test_invalid_quantities_do_not_query_repository(quantity):
    repo = FakeBookRepository(None)

    with pytest.raises(ValueError, match="Quantity must be a positive integer"):
        BorrowingService(repo)._validate_book_availability(1, quantity)

    assert repo.lookups == []


def test_missing_book():
    repo = FakeBookRepository(None)

    with pytest.raises(ValueError, match="Book not found"):
        BorrowingService(repo)._validate_book_availability(1, 1)

    assert repo.lookups == [1]


@pytest.mark.parametrize(
    "status, quantity", [("Available", 0), ("Unavailable", 5)]
)
def test_unavailable_book(status, quantity):
    book = Book(book_id=1, status=status, quantity=quantity)
    original = book.to_dict().copy()

    with pytest.raises(ValueError, match="Book is currently unavailable"):
        BorrowingService(FakeBookRepository(book))._validate_book_availability(1, 1)

    assert book.to_dict() == original


def test_insufficient_stock_preserves_inventory():
    book = Book(book_id=1, quantity=2)

    with pytest.raises(ValueError, match="Only 2 copies are available"):
        BorrowingService(FakeBookRepository(book))._validate_book_availability(1, 3)

    assert book.quantity == 2


def test_stock_is_rechecked_on_each_call():
    book = Book(book_id=1, quantity=2)
    repo = FakeBookRepository(book)
    service = BorrowingService(repo)
    service._validate_book_availability(1, 2)

    book.quantity = 1

    with pytest.raises(ValueError, match="Only 1 copies are available"):
        service._validate_book_availability(1, 2)

    assert repo.lookups == [1, 1]
    assert book.quantity == 1
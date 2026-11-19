
import pytest
from decimal import Decimal

from app.services.fine_service import FineService


class FakeFineRepository:

    def __init__(
        self,
        borrowing=None,
        details=None,
        existing_fine=None,
        fines=None
    ):
        self.borrowing = borrowing
        self.details = details or []
        self.existing_fine = existing_fine
        self.created_fine = None
        self.fines = fines or []
        self.requested_reader_id = None

    def get_borrowing_for_fine(self, borrowing_id):
        return self.borrowing

    def get_borrowing_details(self, borrowing_id):
        return self.details

    def get_by_borrowing_id(self, borrowing_id):
        return self.existing_fine

    def create_fine(self, fine):
        fine.fine_id = 100
        self.created_fine = fine
        return fine

    def get_fines_by_reader(self, reader_id):
        self.requested_reader_id = reader_id
        return self.fines


@pytest.fixture
def reader_user():
    return {
        "user_id": 2,
        "reader_id": 2,
        "username": "reader",
        "role": "READER"
    }


@pytest.fixture
def admin_user():
    return {
        "user_id": 1,
        "admin_id": 1,
        "username": "admin",
        "role": "ADMIN"
    }


@pytest.fixture
def reader_fines_service():
    fines = [
        {
            "fine_id": 1,
            "borrowing_id": 10,
            "amount": Decimal("6000.00"),
            "reason": "Overdue fine",
            "fine_date": "2026-11-15",
            "payment_status": "Unpaid",
            "payment_date": None,
            "book_titles": "Python Programming",
            "days_overdue": 3
        },
        {
            "fine_id": 2,
            "borrowing_id": 11,
            "amount": Decimal("4000.00"),
            "reason": "Overdue fine",
            "fine_date": "2026-11-16",
            "payment_status": "Paid",
            "payment_date": "2026-11-17",
            "book_titles": "Database Systems",
            "days_overdue": 2
        }
    ]

    service = FineService()
    service.repo = FakeFineRepository(fines=fines)

    return service



def test_calculate_fine_one_book_overdue():
    borrowing = {
        "borrowingID": 1,
        "readerID": 2,
        "status": "Returned",
        "due_date": "2026-11-10",
        "return_date": "2026-11-13"
    }

    details = [
        {
            "bookID": 1,
            "return_date": "2026-11-13"
        }
    ]

    service = FineService()
    service.repo = FakeFineRepository(
        borrowing=borrowing,
        details=details
    )

    current_user = {
        "user_id": 1,
        "admin_id": 1,
        "role": "ADMIN"
    }

    result = service.calculate_fine(1, current_user)

    assert result["amount"] == Decimal("6000.00")
    assert result["days_overdue"] == 3


def test_calculate_fine_multiple_books():
    borrowing = {
        "borrowingID": 1,
        "readerID": 2,
        "status": "Returned",
        "due_date": "2026-11-10",
        "return_date": "2026-11-13"
    }

    details = [
        {
            "bookID": 1,
            "return_date": "2026-11-12"
        },
        {
            "bookID": 2,
            "return_date": "2026-11-13"
        }
    ]

    service = FineService()
    service.repo = FakeFineRepository(
        borrowing=borrowing,
        details=details
    )

    current_user = {
        "user_id": 1,
        "admin_id": 1,
        "role": "ADMIN"
    }

    result = service.calculate_fine(1, current_user)

    # Book 1: 2 days x 2,000 = 4,000
    # Book 2: 3 days x 2,000 = 6,000
    assert result["amount"] == Decimal("10000.00")
    assert result["days_overdue"] == 5


def test_no_fine_when_returned_on_time():
    borrowing = {
        "borrowingID": 1,
        "readerID": 2,
        "status": "Returned",
        "due_date": "2026-11-10",
        "return_date": "2026-11-10"
    }

    details = [
        {
            "bookID": 1,
            "return_date": "2026-11-10"
        }
    ]

    service = FineService()
    service.repo = FakeFineRepository(
        borrowing=borrowing,
        details=details
    )

    current_user = {
        "user_id": 1,
        "admin_id": 1,
        "role": "ADMIN"
    }

    result = service.calculate_fine(1, current_user)

    assert result["amount"] == Decimal("0.00")


def test_reader_cannot_calculate_fine():
    service = FineService()
    service.repo = FakeFineRepository()

    current_user = {
        "user_id": 2,
        "reader_id": 2,
        "role": "READER"
    }

    with pytest.raises(PermissionError):
        service.calculate_fine(1, current_user)


def test_calculate_fine_requires_login():
    service = FineService()
    service.repo = FakeFineRepository()

    with pytest.raises(PermissionError):
        service.calculate_fine(1, None)


def test_invalid_borrowing_id():
    service = FineService()
    service.repo = FakeFineRepository()

    current_user = {
        "user_id": 1,
        "admin_id": 1,
        "role": "ADMIN"
    }

    with pytest.raises(ValueError):
        service.calculate_fine(-1, current_user)


def test_borrowing_must_be_returned():
    borrowing = {
        "borrowingID": 1,
        "readerID": 2,
        "status": "Borrowed",
        "due_date": "2026-11-10",
        "return_date": None
    }

    service = FineService()
    service.repo = FakeFineRepository(borrowing=borrowing)

    current_user = {
        "user_id": 1,
        "admin_id": 1,
        "role": "ADMIN"
    }

    with pytest.raises(ValueError):
        service.calculate_fine(1, current_user)


def test_prevent_duplicate_fine():
    borrowing = {
        "borrowingID": 1,
        "readerID": 2,
        "status": "Returned",
        "due_date": "2026-11-10",
        "return_date": "2026-11-13"
    }

    details = [
        {
            "bookID": 1,
            "return_date": "2026-11-13"
        }
    ]

    existing_fine = {
        "fineID": 10,
        "borrowingID": 1
    }

    service = FineService()
    service.repo = FakeFineRepository(
        borrowing=borrowing,
        details=details,
        existing_fine=existing_fine
    )

    current_user = {
        "user_id": 1,
        "admin_id": 1,
        "role": "ADMIN"
    }

    with pytest.raises(ValueError):
        service.calculate_fine(1, current_user)


def test_borrowing_not_found():
    service = FineService()
    service.repo = FakeFineRepository(borrowing=None)

    current_user = {
        "user_id": 1,
        "admin_id": 1,
        "role": "ADMIN"
    }

    with pytest.raises(ValueError):
        service.calculate_fine(999, current_user)



def test_reader_can_view_own_fines(
    reader_fines_service,
    reader_user
):
    result = reader_fines_service.get_my_fines(reader_user)

    assert len(result) == 2
    assert result[0]["fine_id"] == 1
    assert result[1]["fine_id"] == 2

    assert reader_fines_service.repo.requested_reader_id == 2


def test_reader_fines_contain_display_information(
    reader_fines_service,
    reader_user
):
    result = reader_fines_service.get_my_fines(reader_user)

    first_fine = result[0]

    assert first_fine["book_titles"] == "Python Programming"
    assert first_fine["days_overdue"] == 3
    assert first_fine["amount"] == Decimal("6000.00")
    assert first_fine["payment_status"] == "Unpaid"
    assert first_fine["fine_date"] == "2026-11-15"


def test_reader_with_no_fines_gets_empty_list(reader_user):
    service = FineService()
    service.repo = FakeFineRepository(fines=[])

    result = service.get_my_fines(reader_user)

    assert result == []


def test_admin_cannot_use_reader_personal_fines(
    reader_fines_service,
    admin_user
):
    with pytest.raises(PermissionError):
        reader_fines_service.get_my_fines(admin_user)


def test_reader_fines_require_login(reader_fines_service):
    with pytest.raises(PermissionError):
        reader_fines_service.get_my_fines(None)


def test_reader_id_is_required(reader_fines_service):
    user = {
        "user_id": 2,
        "role": "READER"
    }

    with pytest.raises(ValueError):
        reader_fines_service.get_my_fines(user)


def test_invalid_reader_id_is_rejected(reader_fines_service):
    user = {
        "user_id": 2,
        "reader_id": -1,
        "role": "READER"
    }

    with pytest.raises(ValueError):
        reader_fines_service.get_my_fines(user)

import mysql.connector
import pytest

from app.controllers.borrowing_controller import BorrowingController
from tests.test_borrowing_service import setup


class StubBorrowingService:
    def __init__(self, error=None):
        self.error = error
        self.calls = []
        self.result = {
            "borrowing_id": 20,
            "status": "Pending",
        }

    def request_borrow(self, book_id, quantity, current_user):
        self.calls.append((book_id, quantity, current_user))

        if self.error is not None:
            raise self.error

        return self.result


def test_success_response_and_session_forwarding():
    current_user = {"user_id": 2, "role": "READER"}
    service = StubBorrowingService()
    controller = BorrowingController(
        current_user=current_user,
        service=service,
    )

    result = controller.request_borrow(book_id=4, quantity=2)

    assert result == {
        "success": True,
        "message": "Borrowing request submitted successfully.",
        "data": service.result,
    }
    assert service.calls == [(4, 2, current_user)]


@pytest.mark.parametrize(
    "error",
    [
        ValueError("The borrowing limit is 3 books."),
        PermissionError("Reader permission is required."),
    ],
)
def test_business_errors_return_standard_failure(error):
    controller = BorrowingController(
        service=StubBorrowingService(error)
    )

    result = controller.request_borrow(4, 1)

    assert result == {
        "success": False,
        "message": str(error),
        "data": None,
    }


@pytest.mark.parametrize(
    "error, expected_message",
    [
        (
            mysql.connector.Error(
                "SELECT internal_column FROM internal_table"
            ),
            "Unable to save the borrowing request. "
            "Please contact the library administrator.",
        ),
        (
            RuntimeError("internal stack trace details"),
            "An unexpected error occurred.",
        ),
    ],
)
def test_internal_errors_are_not_exposed(error, expected_message):
    controller = BorrowingController(
        service=StubBorrowingService(error)
    )

    result = controller.request_borrow(4, 1)

    assert result == {
        "success": False,
        "message": expected_message,
        "data": None,
    }
    assert str(error) not in result["message"]


@pytest.mark.parametrize(
    "current_user, message",
    [
        (None, "Reader permission is required."),
        (
            {"user_id": 1, "role": "ADMIN"},
            "Reader permission is required.",
        ),
        (
            {"role": "READER"},
            "A valid authenticated session is required.",
        ),
    ],
)
def test_real_service_rejects_unauthorized_sessions(
    current_user, message
):
    controller = BorrowingController(current_user=current_user)

    result = controller.request_borrow(4, 1)

    assert result == {
        "success": False,
        "message": message,
        "data": None,
    }


def test_unconfigured_lending_policy_returns_standard_failure():
    controller = BorrowingController(
        current_user={"user_id": 2, "role": "READER"}
    )

    result = controller.request_borrow(4, 1)

    assert result == {
        "success": False,
        "message": "Borrowing requests are unavailable. "
        "Please contact the library administrator.",
        "data": None,
    }


def test_controller_and_real_service_use_authenticated_reader(setup):
    service, conn, books, borrowing, opened = setup
    controller = BorrowingController(
        current_user={
            "user_id": 2,
            "role": "READER",
            "reader_id": 999,
        },
        service=service,
    )

    result = controller.request_borrow(4, 1)

    assert result["success"] is True
    assert set(result) == {"success", "message", "data"}
    assert result["data"]["reader_id"] == 7
    assert result["data"]["borrowing_id"] == 20
    assert result["data"]["status"] == "Pending"
    assert borrowing.lookups == [2]
    assert conn.committed
    assert conn.closed
    assert books.book.quantity == 3


def test_controller_and_real_service_enforce_limit(setup):
    service, conn, books, borrowing, opened = setup
    borrowing.active_quantity = 3

    controller = BorrowingController(
        current_user={"user_id": 2, "role": "READER"},
        service=service,
    )

    result = controller.request_borrow(4, 1)

    assert result == {
        "success": False,
        "message": "The borrowing limit is 3 books.",
        "data": None,
    }
    assert not borrowing.requests
    assert conn.rolled_back
    assert conn.closed
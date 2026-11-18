import mysql.connector

from app.services.borrowing_service import BorrowingService


class BorrowingController:
    def __init__(
        self,
        current_user=None,
        service=None,
        loan_period_days=None,
    ):
        """Receive current_user from the authenticated session."""
        self.current_user = current_user
        self.service = (
            service
            if service is not None
            else BorrowingService(loan_period_days=loan_period_days)
        )

    def _success(self, message: str, data=None) -> dict:
        return {
            "success": True,
            "message": message,
            "data": data,
        }

    def _error(self, message: str) -> dict:
        return {
            "success": False,
            "message": message,
            "data": None,
        }

    def request_borrow(self, book_id: int, quantity: int) -> dict:
        try:
            data = self.service.request_borrow(
                book_id, quantity, self.current_user
            )
            return self._success(
                "Borrowing request submitted successfully.",
                data,
            )

        except (ValueError, PermissionError) as error:
            return self._error(str(error))

        except mysql.connector.Error:
            return self._error(
                "Unable to save the borrowing request. "
                "Please contact the library administrator."
            )

        except Exception:
            return self._error("An unexpected error occurred.")

    def request_return(self, borrowing_id: int) -> dict:
        try:
            data = self.service.request_return(borrowing_id, self.current_user)
            message = "Return request submitted. Please wait for Admin confirmation."
            if data["days_overdue"] > 0:
                message += (
                    f" This loan is {data['days_overdue']} day(s) overdue."
                )
            return self._success(message, data)
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error(
                "Unable to save the return request. "
                "Please contact the library administrator."
            )
        except Exception:
            return self._error("An unexpected error occurred.")

    def get_my_borrowing_history(self) -> dict:
        try:
            data = self.service.get_my_borrowing_history(self.current_user)
            return self._success("Borrowing history loaded successfully.", data)
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error(
                "Unable to load borrowing history. "
                "Please contact the library administrator."
            )
        except Exception:
            return self._error("An unexpected error occurred.")

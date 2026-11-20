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
                if "estimated_fine" in data:
                    message += (
                        f" Estimated overdue fine: {data['estimated_fine']:,} VND."
                        " The final amount uses the actual return date."
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

    def get_pending_borrow_requests(self) -> dict:
        try:
            data = self.service.get_pending_borrow_requests(self.current_user)
            return self._success("Pending borrowing requests loaded successfully.", data)
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error("Unable to load borrowing requests. Please contact the library administrator.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def approve_borrow(self, borrowing_id: int) -> dict:
        return self._borrow_decision(borrowing_id, True)

    def reject_borrow(self, borrowing_id: int) -> dict:
        return self._borrow_decision(borrowing_id, False)

    def _borrow_decision(self, borrowing_id, approve):
        try:
            action = self.service.approve_borrow if approve else self.service.reject_borrow
            data = action(borrowing_id, self.current_user)
            return self._success("Borrowing request approved." if approve else "Borrowing request rejected.", data)
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error("Unable to process the borrowing request. Please contact the library administrator.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def get_pending_return_requests(self) -> dict:
        try:
            data = self.service.get_pending_return_requests(self.current_user)
            return self._success("Pending return requests loaded successfully.", data)
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error("Unable to load return requests. Please contact the library administrator.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def get_pending_return_copies(self, borrowing_id):
        return self._renewal_action(self.service.get_pending_return_copies, "Copies loaded.", borrowing_id)

    def confirm_return(self, borrowing_id: int, return_items=None) -> dict:
        try:
            if return_items is None:
                data = self.service.confirm_return(borrowing_id, self.current_user)
            else:
                data = self.service.confirm_return(borrowing_id, self.current_user, return_items)
            return self._success("Book return confirmed successfully.", data)
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error("Unable to confirm the return. Please contact the library administrator.")
        except Exception:
            return self._error("An unexpected error occurred.")

    def _renewal_action(self, action, message, *args):
        try:
            return self._success(message, action(*args, self.current_user))
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error("Unable to process the renewal. Please contact the library.")

    def get_renewal_requests(self):
        return self._renewal_action(self.service.get_renewal_requests, "Renewal requests loaded.")

    def request_renewal(self, borrowing_id, new_due_date):
        return self._renewal_action(self.service.request_renewal, "Renewal request submitted.", borrowing_id, new_due_date)

    def decide_renewal(self, borrowing_id, approved):
        return self._renewal_action(self.service.decide_renewal, "Renewal request processed.", borrowing_id, approved)

    def get_all_borrowing_records(self) -> dict:
        try:
            data = self.service.get_all_borrowing_records(self.current_user)
            return self._success("Borrowing records loaded successfully.", data)
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error("Unable to load borrowing records. Please contact the library administrator.")
        except Exception:
            return self._error("An unexpected error occurred.")

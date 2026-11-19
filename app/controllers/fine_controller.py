
import mysql.connector

from app.services.fine_service import FineService


class FineController:

    def __init__(self, current_user: dict | None = None):
        self.service = FineService()
        self.current_user = current_user


    def set_current_user(self, current_user: dict | None):
        self.current_user = current_user


    def _success(self, message: str, data=None) -> dict:
        return {
            "success": True,
            "message": message,
            "data": data
        }

    def _error(self, message: str) -> dict:
        return {
            "success": False,
            "message": message,
            "data": None
        }


    def calculate_fine(self, borrowing_id: int) -> dict:
        try:
            fine = self.service.calculate_fine(
                borrowing_id,
                self.current_user
            )

            return self._success(
                "Fine calculated successfully.",
                fine
            )

        except (ValueError, PermissionError) as error:
            return self._error(str(error))

        except mysql.connector.Error:
            return self._error(
                "Database error occurred while calculating fine."
            )

        except Exception:
            return self._error(
                "An unexpected error occurred."
            )


    def get_my_fines(self) -> dict:
        try:
            fines = self.service.get_my_fines(
                self.current_user
            )

            return self._success(
                "Retrieved reader fines successfully.",
                fines
            )

        except (ValueError, PermissionError) as error:
            return self._error(str(error))

        except mysql.connector.Error:
            return self._error(
                "Database error occurred while retrieving fines."
            )

        except Exception:
            return self._error(
                "An unexpected error occurred."
            )

    # LMS-45: Confirm fine payment.
    def confirm_payment(self, fine_id: int) -> dict:

        try:
            fine = self.service.confirm_payment(
                fine_id,
                self.current_user
            )

            return self._success(
                "Fine payment confirmed successfully.",
                fine
            )

        except (ValueError, PermissionError) as error:
            return self._error(str(error))

        except mysql.connector.Error:
            return self._error(
                "Database error occurred while confirming fine payment."
            )

        except Exception:
            return self._error(
                "An unexpected error occurred."
            )

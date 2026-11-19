
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

import mysql.connector

from app.services.report_service import ReportService


class ReportController:

    def __init__(self, current_user: dict | None = None):
        self.service = ReportService()
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

    def get_statistics(self) -> dict:
        try:
            statistics = self.service.get_statistics(
                self.current_user
            )

            return self._success(
                "Retrieved book statistics successfully.",
                statistics
            )

        except (ValueError, PermissionError) as error:
            return self._error(str(error))

        except mysql.connector.Error:
            return self._error(
                "Database error occurred while retrieving statistics."
            )

        except Exception:
            return self._error(
                "An unexpected error occurred."
            )

    # LMS-47: Reader Statistics
    def get_reader_statistics(self) -> dict:
        try:
            statistics = self.service.get_reader_statistics(
                self.current_user
            )
            return self._success(
                "Retrieved reader statistics successfully.",
                statistics
            )
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error(
                "Database error occurred while retrieving reader statistics."
            )
        except Exception:
            return self._error(
                "An unexpected error occurred."
            )

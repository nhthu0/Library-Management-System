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

    # LMS-48: Borrowing and Returning Statistics

    def get_borrowing_report(
        self,
        start_date: str,
        end_date: str
    ) -> dict:
        try:
            statistics = self.service.get_borrowing_report(
                start_date,
                end_date,
                self.current_user
            )

            return self._success(
                "Retrieved borrowing and returning statistics successfully.",
                statistics
            )

        except (ValueError, PermissionError) as error:
            return self._error(str(error))

        except mysql.connector.Error:
            return self._error(
                "Database error occurred while retrieving borrowing and returning statistics."
            )

        except Exception:
            return self._error(
                "An unexpected error occurred."
            )

    # LMS-49: Book Status Statistics

    def get_book_status_statistics(self) -> dict:
        try:
            statistics = self.service.get_book_status_statistics(
                self.current_user
            )
            return self._success(
                "Retrieved book status statistics successfully.",
                statistics
            )
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error(
                "Database error occurred while retrieving book status statistics."
            )
        except Exception:
            return self._error(
                "An unexpected error occurred."
            )

    # LMS-49: Fine Statistics

    def get_fine_statistics(self) -> dict:
        try:
            statistics = self.service.get_fine_statistics(
                self.current_user
            )
            return self._success(
                "Retrieved fine statistics successfully.",
                statistics
            )
        except (ValueError, PermissionError) as error:
            return self._error(str(error))
        except mysql.connector.Error:
            return self._error(
                "Database error occurred while retrieving fine statistics."
            )
        except Exception:
            return self._error(
                "An unexpected error occurred."
            )

    # LMS-49: Export Report to CSV

    def export_report(
        self,
        report_type: str,
        file_path: str,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> dict:
        try:
            exported_path = self.service.export_report(
                report_type,
                file_path,
                self.current_user,
                start_date,
                end_date
            )

            return self._success(
                "Report exported to CSV successfully.",
                {"file_path": exported_path}
            )

        except (ValueError, PermissionError) as error:
            return self._error(str(error))

        except OSError:
            return self._error(
                "Unable to export report to CSV."
            )

        except mysql.connector.Error:
            return self._error(
                "Database error occurred while exporting report."
            )

        except Exception:
            return self._error(
                "An unexpected error occurred."
            )

from app.repositories.report_repository import ReportRepository
from app.utils.csv_exporter import export_report_to_csv


class ReportService:

    def __init__(self):
        self.repo = ReportRepository()

    def _require_admin(self, current_user: dict | None):
        if not isinstance(current_user, dict):
            raise PermissionError("Please log in first.")

        role = str(current_user.get("role", "")).upper()

        if role != "ADMIN":
            raise PermissionError(
                "Access denied: Admin permission required."
            )

    # LMS-46: Book Statistics
    def get_statistics(
        self,
        current_user: dict | None
    ) -> dict:
        self._require_admin(current_user)
        return self.repo.get_book_statistics()

    # LMS-47: Reader Statistics
    def get_reader_statistics(
        self,
        current_user: dict | None
    ) -> dict:
        self._require_admin(current_user)
        return self.repo.get_reader_statistics()

    # LMS-48: Borrowing and Returning Statistics

    def get_borrowing_report(
        self,
        start_date: str,
        end_date: str,
        current_user: dict | None
    ) -> dict:

        self._require_admin(current_user)

        if not isinstance(start_date, str) or not isinstance(end_date, str):
            raise ValueError("Start date and end date must be strings.")

        from datetime import date

        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")

        if start_date != start.isoformat() or end_date != end.isoformat():
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")

        if start > end:
            raise ValueError("Start date must not be after end date.")

        return self.repo.get_borrowing_report(
            start_date,
            end_date
        )

    # LMS-49: Book Status Statistics

    def get_book_status_statistics(
        self,
        current_user: dict | None
    ) -> dict:
        self._require_admin(current_user)
        return self.repo.get_book_status_statistics()

    # LMS-49: Fine Statistics

    def get_fine_statistics(
        self,
        current_user: dict | None
    ) -> dict:
        self._require_admin(current_user)
        return self.repo.get_fine_statistics()

    # LMS-49: Export Report to CSV

    def export_report(
        self,
        report_type: str,
        file_path: str,
        current_user: dict | None,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> str:
        self._require_admin(current_user)

        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("Invalid CSV file path.")

        reports = {
            "book_statistics": self.get_statistics,
            "reader_statistics": self.get_reader_statistics,
            "book_status_statistics": self.get_book_status_statistics,
            "fine_statistics": self.get_fine_statistics
        }

        if report_type == "borrowing_report":
            if start_date is None or end_date is None:
                raise ValueError(
                    "Start date and end date are required for borrowing reports."
                )

            report_data = self.get_borrowing_report(
                start_date,
                end_date,
                current_user
            )

        elif isinstance(report_type, str) and report_type in reports:
            report_data = reports[report_type](current_user)

        else:
            raise ValueError("Unsupported report type.")

        return export_report_to_csv(report_data, file_path)

from app.repositories.report_repository import ReportRepository


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

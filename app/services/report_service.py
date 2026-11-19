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

    def get_statistics(
        self,
        current_user: dict | None
    ) -> dict:
        self._require_admin(current_user)

        return self.repo.get_book_statistics()

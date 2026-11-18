from datetime import date, datetime
from app.repositories.fine_repository import FineRepository

class FineService:
    FINE_PER_DAY = 2000

    def __init__(self):
        self.repository = FineRepository()

    def _check_role(self, current_user: dict | None, required_role: str):
        if not current_user:
            raise PermissionError("User is not logged in.")

        role = str(current_user.get("role", "")).upper()

        if role != required_role:
            raise PermissionError("You do not have permission to perform this action.")

    def _parse_date(self, value) -> date:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if not value:
            raise ValueError("Borrowing date information is incomplete.")

        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()

    def get_my_fines(self, current_user: dict) -> list[dict]:
        self._check_role(current_user, "READER")

        reader_id = current_user.get("reader_id")

        if not reader_id:
            raise ValueError("Reader information is missing from the session.")

        fines = self.repository.get_by_reader_id(reader_id)

        return [fine.to_dict() for fine in fines]

    def get_all_fines(self, current_user: dict) -> list[dict]:
        self._check_role(current_user, "ADMIN")

        fines = self.repository.get_all()

        return [fine.to_dict() for fine in fines]

    def calculate_fine(self, borrowing_id: int, current_user: dict) -> dict | None:
        self._check_role(current_user, "ADMIN")

        if not isinstance(borrowing_id, int) or borrowing_id <= 0:
            raise ValueError("Invalid borrowing ID.")

        borrowing = self.repository.get_borrowing_for_fine(borrowing_id)

        if not borrowing:
            raise ValueError("Borrowing record not found.")

        if str(borrowing.get("status", "")).lower() != "returned":
            raise ValueError("The borrowing record has not been returned.")

        due_date = self._parse_date(borrowing.get("due_date"))
        record_return_date = borrowing.get("return_date")
        details = borrowing.get("details", [])

        if not details:
            raise ValueError("No borrowed book details were found.")

        total_days_overdue = 0
        total_amount = 0
        overdue_books = 0

        for detail in details:
            # Ưu tiên ngày trả riêng của từng sách.
            # Nếu chưa có thì dùng ngày trả của phiếu mượn.
            actual_return_date = (
                detail.get("return_date") or record_return_date
            )

            if not actual_return_date:
                raise ValueError("Actual return date is missing.")

            return_date = self._parse_date(actual_return_date)
            days_overdue = max((return_date - due_date).days, 0)

            if days_overdue > 0:
                overdue_books += 1
                total_days_overdue += days_overdue
                total_amount += days_overdue * self.FINE_PER_DAY

        if total_amount == 0:
            return None

        reason = (
            f"Overdue fine for {overdue_books} book(s). "
            f"Rate: {self.FINE_PER_DAY} VND per day per book."
        )

        fine = self.repository.save_calculated_fine(
            borrowing_id=borrowing_id,
            amount=total_amount,
            days_overdue=total_days_overdue,
            reason=reason,
            fine_date=date.today().isoformat()
        )

        return fine.to_dict() if fine else None

    def confirm_payment(self, fine_id: int, current_user: dict) -> dict:
        self._check_role(current_user, "ADMIN")

        if not isinstance(fine_id, int) or fine_id <= 0:
            raise ValueError("Invalid fine ID.")

        admin_id = current_user.get("admin_id")

        if not admin_id:
            raise ValueError("Admin information is missing from the session.")

        fine = self.repository.confirm_payment(fine_id, admin_id)

        if not fine:
            raise ValueError("Fine not found.")

        return fine.to_dict()

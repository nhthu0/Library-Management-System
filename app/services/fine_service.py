
from datetime import date
from decimal import Decimal

from app.models.fine import Fine
from app.repositories.fine_repository import FineRepository


class FineService:
    FINE_RATE_PER_DAY = Decimal("2000.00")

    def __init__(self):
        self.repo = FineRepository()

    def _require_admin(self, current_user: dict | None):
        if not isinstance(current_user, dict):
            raise PermissionError("Please log in first.")

        role = str(current_user.get("role", "")).upper()

        if role != "ADMIN":
            raise PermissionError(
                "Access denied: Admin permission required."
            )

    def _validate_borrowing_id(self, borrowing_id: int):
        if (
            not isinstance(borrowing_id, int)
            or isinstance(borrowing_id, bool)
            or borrowing_id <= 0
        ):
            raise ValueError("Invalid borrowing ID.")

    def calculate_fine(
        self,
        borrowing_id: int,
        current_user: dict | None
    ) -> dict:
        self._require_admin(current_user)
        self._validate_borrowing_id(borrowing_id)

        borrowing = self.repo.get_borrowing_for_fine(borrowing_id)

        if not borrowing:
            raise ValueError("Borrowing record not found.")

        if borrowing["status"] != "Returned":
            raise ValueError(
                "Fine can only be calculated for returned borrowing records."
            )

        existing_fine = self.repo.get_by_borrowing_id(borrowing_id)

        if existing_fine:
            raise ValueError(
                "A fine already exists for this borrowing record."
            )

        try:
            due_date = date.fromisoformat(borrowing["due_date"])
        except (TypeError, ValueError):
            raise ValueError("Invalid borrowing due date.")

        details = self.repo.get_borrowing_details(borrowing_id)

        if not details:
            raise ValueError("No borrowed book details found.")

        total_days_overdue = 0
        total_amount = Decimal("0.00")

        for detail in details:
            returned_date_value = (
                detail["return_date"]
                or borrowing["return_date"]
            )

            if not returned_date_value:
                raise ValueError(
                    "Return date is missing for a borrowed book."
                )

            try:
                returned_date = date.fromisoformat(
                    returned_date_value
                )
            except (TypeError, ValueError):
                raise ValueError("Invalid book return date.")

            days_overdue = max(
                (returned_date - due_date).days,
                0
            )

            total_days_overdue += days_overdue

            total_amount += (
                Decimal(days_overdue) * self.FINE_RATE_PER_DAY
            )

        if total_amount <= 0:
            return {
                "fine_id": None,
                "borrowing_id": borrowing_id,
                "days_overdue": 0,
                "amount": 0.0,
                "reason": "No overdue books.",
                "fine_date": date.today().isoformat(),
                "payment_status": None,
                "payment_date": None,
                "admin_id": None
            }

        admin_id = current_user.get("admin_id")

        if not admin_id:
            raise ValueError(
                "Admin ID is missing from the current session."
            )

        fine = Fine(
            borrowing_id=borrowing_id,
            amount=total_amount,
            reason=(
                f"Overdue fine: {total_days_overdue} "
                f"overdue book-days x 2,000 VND."
            ),
            fine_date=date.today().isoformat(),
            payment_status="Unpaid",
            payment_date=None,
            admin_id=admin_id,
            days_overdue=total_days_overdue
        )

        created_fine = self.repo.create_fine(fine)

        result = created_fine.to_dict()
        result["days_overdue"] = total_days_overdue

        return result

    def get_my_fines(self, current_user: dict | None) -> list[dict]:
        if not isinstance(current_user, dict):
            raise PermissionError("Please log in to view your fines.")

        role = str(current_user.get("role", "")).upper()

        if role != "READER":
            raise PermissionError(
                "Only readers can view their personal fines."
            )

        reader_id = current_user.get("reader_id")

        if not reader_id:
            raise ValueError(
                "Reader ID is missing from the current session."
            )

        if (
            not isinstance(reader_id, int)
            or isinstance(reader_id, bool)
            or reader_id <= 0
        ):
            raise ValueError("Invalid reader ID.")

        return self.repo.get_fines_by_reader(reader_id)

    # LMS-45: Confirm fine payment.
    def confirm_payment(
        self,
        fine_id: int,
        current_user: dict | None
    ) -> dict:

        self._require_admin(current_user)

        if (
            not isinstance(fine_id, int)
            or isinstance(fine_id, bool)
            or fine_id <= 0
        ):
            raise ValueError("Invalid fine ID.")

        payment_date = date.today().isoformat()

        fine = self.repo.confirm_payment(
            fine_id,
            payment_date
        )

        if fine is None:
            raise ValueError("Fine not found.")

        return fine

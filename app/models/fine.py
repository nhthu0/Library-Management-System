from decimal import Decimal


class Fine:
    def __init__(
        self,
        fine_id: int | None = None,
        borrowing_id: int | None = None,
        amount: Decimal | float = Decimal("0.00"),
        reason: str | None = None,
        fine_date: str | None = None,
        payment_status: str = "Unpaid",
        payment_date: str | None = None,
        admin_id: int | None = None,
        days_overdue: int = 0
    ):
        self.fine_id = fine_id
        self.borrowing_id = borrowing_id
        self.amount = Decimal(str(amount))
        self.reason = reason
        self.fine_date = fine_date
        self.payment_status = payment_status
        self.payment_date = payment_date
        self.admin_id = admin_id
        self.days_overdue = days_overdue

    def to_dict(self) -> dict:
        return {
            "fine_id": self.fine_id,
            "borrowing_id": self.borrowing_id,
            "amount": float(self.amount),
            "reason": self.reason,
            "fine_date": self.fine_date,
            "payment_status": self.payment_status,
            "payment_date": self.payment_date,
            "admin_id": self.admin_id,
            "days_overdue": self.days_overdue
        }
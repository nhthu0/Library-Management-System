
class Fine:
    def __init__(
        self,
        fine_id: int | None = None,
        borrowing_id: int | None = None,
        days_overdue: int = 0,
        amount: float = 0,
        reason: str | None = None,
        fine_date: str | None = None,
        status: str = "Unpaid",
        payment_date: str | None = None,
        admin_id: int | None = None
    ):
        self.fine_id = fine_id
        self.borrowing_id = borrowing_id
        self.days_overdue = days_overdue
        self.amount = amount
        self.reason = reason
        self.fine_date = fine_date
        self.status = status
        self.payment_date = payment_date
        self.admin_id = admin_id

    def to_dict(self) -> dict:
        return {
            "fine_id": int(self.fine_id) if self.fine_id is not None else None,
            "borrowing_id": int(self.borrowing_id) if self.borrowing_id is not None else None,
            "days_overdue": int(self.days_overdue or 0),
            "amount": float(self.amount or 0),
            "reason": self.reason,
            "fine_date": self.fine_date,
            "status": self.status,
            "payment_date": self.payment_date,
            "admin_id": int(self.admin_id) if self.admin_id is not None else None
        }

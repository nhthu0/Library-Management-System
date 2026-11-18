from datetime import date, timedelta

from app.database.connection import get_connection
from app.repositories.book_repository import BookRepository
from app.repositories.borrowing_repository import BorrowingRepository


class BorrowingService:
    MAX_BORROWED_BOOKS = 3

    def __init__(
        self,
        book_repository=None,
        borrowing_repository=None,
        connection_factory=None,
        loan_period_days=None,
        today_provider=None,
    ):
        """Use the lending period agreed by the project team."""
        self.book_repo = (
            book_repository
            if book_repository is not None
            else BookRepository()
        )
        self.borrowing_repo = (
            borrowing_repository
            if borrowing_repository is not None
            else BorrowingRepository()
        )
        self._get_connection = (
            connection_factory
            if connection_factory is not None
            else get_connection
        )
        self.loan_period_days = loan_period_days
        self._today = today_provider if today_provider is not None else date.today

    @staticmethod
    def _validate_book_input(book_id: int, quantity: int):
        if type(book_id) is not int or book_id <= 0:
            raise ValueError("Book ID must be a positive integer.")

        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

    def _validate_book_availability(
        self, book_id: int, quantity: int, *, borrowed_copies: int = 0
    ):
        """Validate total stock less active copies counted by the caller."""
        self._validate_book_input(book_id, quantity)
        book = self.book_repo.get_by_id(book_id)

        if book is None:
            raise ValueError("Book not found.")

        available = max(0, book.quantity - borrowed_copies)
        if book.status != "Available" or available <= 0:
            raise ValueError("Book is currently unavailable.")

        if quantity > available:
            raise ValueError(
                f"Only {available} copies are available."
            )
        return book

    @staticmethod
    def _require_reader(current_user):
        if (
            not isinstance(current_user, dict)
            or str(current_user.get("role", "")).upper() != "READER"
        ):
            raise PermissionError("Reader permission is required.")

        user_id = current_user.get("user_id")
        if type(user_id) is not int or user_id <= 0:
            raise PermissionError("A valid authenticated session is required.")

        return user_id

    @staticmethod
    def _validate_reader_eligibility(reader, today):
        if not reader or str(reader.get("role", "")).upper() != "READER":
            raise PermissionError("Reader account not found.")

        if str(reader.get("account_status", "")).upper() != "ACTIVE":
            raise PermissionError("Reader account is locked or inactive.")

        expiry = reader.get("expiration_date")
        if expiry:
            try:
                expires_on = date.fromisoformat(str(expiry))
            except ValueError:
                raise ValueError("Reader expiration date is invalid.") from None

            if expires_on < today:
                raise PermissionError("Reader membership has expired.")

    def request_borrow(self, book_id: int, quantity: int, current_user) -> dict:
        user_id = self._require_reader(current_user)
        self._validate_book_input(book_id, quantity)

        if quantity > self.MAX_BORROWED_BOOKS:
            raise ValueError("The borrowing limit is 3 books.")

        if type(self.loan_period_days) is not int or self.loan_period_days <= 0:
            raise ValueError(
                "Borrowing requests are unavailable. "
                "Please contact the library administrator."
            )

        today = self._today()
        try:
            due_date = today + timedelta(days=self.loan_period_days)
        except OverflowError:
            raise ValueError(
                "The borrowing period is outside the supported date range."
            ) from None

        conn = self._get_connection()

        try:
            conn.start_transaction()
            reader = self.borrowing_repo.get_reader_for_update(user_id, conn)
            self._validate_reader_eligibility(reader, today)
            reader_id = reader["reader_id"]

            active_quantity = self.borrowing_repo.count_active_books(
                reader_id, conn
            )
            if active_quantity + quantity > self.MAX_BORROWED_BOOKS:
                raise ValueError("The borrowing limit is 3 books.")

            borrowed_copies = self.borrowing_repo.count_active_copies_for_book(
                book_id, conn
            )
            book = self._validate_book_availability(
                book_id, quantity, borrowed_copies=borrowed_copies
            )

            borrowing_id = self.borrowing_repo.create_pending_request(
                reader_id,
                book_id,
                quantity,
                today.isoformat(),
                due_date.isoformat(),
                connection=conn,
            )
            conn.commit()

            return {
                "borrowing_id": borrowing_id,
                "reader_id": reader_id,
                "book_id": book.book_id,
                "quantity": quantity,
                "borrow_date": today.isoformat(),
                "due_date": due_date.isoformat(),
                "status": "Pending",
            }

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    def request_return(self, borrowing_id: int, current_user) -> dict:
        user_id = self._require_reader(current_user)
        if type(borrowing_id) is not int or borrowing_id <= 0:
            raise ValueError("Borrowing ID must be a positive integer.")

        conn = self._get_connection()
        try:
            conn.start_transaction()
            reader = self.borrowing_repo.get_reader_for_update(user_id, conn)
            if not reader or str(reader.get("role", "")).upper() != "READER":
                raise PermissionError("Reader account not found.")
            if str(reader.get("account_status", "")).upper() != "ACTIVE":
                raise PermissionError("Reader account is locked or inactive.")

            # An expired membership must not prevent returning existing loans.
            reader_id = reader["reader_id"]
            record = self.borrowing_repo.get_own_borrowing_for_update(
                borrowing_id, reader_id, conn
            )
            if record is None:
                raise ValueError("Borrowing record not found for this Reader.")
            if (
                record["status"] != "Borrowed"
                or record["return_date"] is not None
                or record["quantity"] <= 0
            ):
                raise ValueError("This borrowing record cannot be requested for return.")

            try:
                due_date = date.fromisoformat(str(record["due_date"]))
            except ValueError:
                raise ValueError("Borrowing due date is invalid.") from None
            days_overdue = max(0, (self._today() - due_date).days)

            changed = self.borrowing_repo.mark_return_requested(
                borrowing_id, reader_id, conn
            )
            if not changed:
                raise ValueError("This borrowing record has changed. Please refresh.")

            conn.commit()
            return {
                "borrowing_id": borrowing_id,
                "reader_id": reader_id,
                "quantity": record["quantity"],
                "due_date": due_date.isoformat(),
                "status": "ReturnRequested",
                "return_date": None,
                "days_overdue": days_overdue,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_my_borrowing_history(self, current_user) -> list:
        user_id = self._require_reader(current_user)
        conn = self._get_connection()
        try:
            conn.start_transaction(readonly=True)
            reader = self.borrowing_repo.get_reader_profile(user_id, conn)
            if not reader or str(reader.get("role", "")).upper() != "READER":
                raise PermissionError("Reader account not found.")
            if str(reader.get("account_status", "")).upper() != "ACTIVE":
                raise PermissionError("Reader account is locked or inactive.")

            rows = self.borrowing_repo.get_reader_history_rows(reader["reader_id"], conn)
            records = {}
            for row in rows:
                borrowing_id = int(row["borrowing_id"])
                if borrowing_id not in records:
                    records[borrowing_id] = {
                        "borrowing_id": borrowing_id,
                        "reader_id": int(row["reader_id"]),
                        "borrow_date": str(row["borrow_date"]),
                        "due_date": str(row["due_date"]),
                        "return_date": (
                            str(row["return_date"])
                            if row["return_date"] is not None else None
                        ),
                        "status": row["status"],
                        "renewal_count": int(row["renewal_count"]),
                        "quantity": 0,
                        "returned_quantity": 0,
                        "books": [],
                    }
                if row["book_id"] is not None:
                    quantity = int(row["quantity"])
                    returned = int(row["returned_quantity"])
                    records[borrowing_id]["books"].append({
                        "book_id": int(row["book_id"]),
                        "title": row["title"], "author": row["author"],
                        "quantity": quantity, "returned_quantity": returned,
                    })
                    records[borrowing_id]["quantity"] += quantity
                    records[borrowing_id]["returned_quantity"] += returned
            conn.commit()
            return list(records.values())
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

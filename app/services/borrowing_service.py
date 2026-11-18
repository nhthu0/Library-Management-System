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
            estimated_fine = self._calculate_overdue_fine(days_overdue, record["quantity"])

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
                "estimated_fine": estimated_fine,
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

    @staticmethod
    def _require_admin(current_user):
        if not isinstance(current_user, dict) or str(current_user.get("role", "")).upper() != "ADMIN":
            raise PermissionError("Admin permission is required.")
        user_id = current_user.get("user_id")
        if type(user_id) is not int or user_id <= 0:
            raise PermissionError("A valid authenticated session is required.")
        return user_id

    @staticmethod
    def _validate_admin_profile(admin):
        if not admin or str(admin.get("role", "")).upper() != "ADMIN":
            raise PermissionError("Admin account not found.")
        if str(admin.get("account_status", "")).upper() != "ACTIVE":
            raise PermissionError("Admin account is locked or inactive.")

    @staticmethod
    def _group_admin_records(rows):
        records = {}
        keys = ("borrowing_id", "reader_id", "reader_name", "admin_id",
                "borrow_date", "due_date", "return_date", "status", "renewal_count")
        for row in rows:
            record_id = int(row["borrowing_id"])
            if record_id not in records:
                record = {key: row[key] for key in keys}
                for key in ("borrow_date", "due_date", "return_date"):
                    record[key] = str(record[key]) if record[key] is not None else None
                record.update(quantity=0, returned_quantity=0, books=[])
                records[record_id] = record
            if row["book_id"] is not None:
                quantity, returned = int(row["quantity"]), int(row["returned_quantity"])
                records[record_id]["books"].append({
                    "book_id": int(row["book_id"]), "title": row["title"],
                    "author": row["author"], "quantity": quantity,
                    "returned_quantity": returned,
                })
                records[record_id]["quantity"] += quantity
                records[record_id]["returned_quantity"] += returned
        return list(records.values())

    def get_pending_borrow_requests(self, current_user) -> list:
        user_id = self._require_admin(current_user)
        conn = self._get_connection()
        try:
            conn.start_transaction(readonly=True)
            self._validate_admin_profile(self.borrowing_repo.get_admin_profile(user_id, conn))
            result = self._group_admin_records(
                self.borrowing_repo.get_admin_record_rows("Pending", conn)
            )
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def approve_borrow(self, borrowing_id: int, current_user) -> dict:
        return self._decide_borrow(borrowing_id, current_user, True)

    def reject_borrow(self, borrowing_id: int, current_user) -> dict:
        return self._decide_borrow(borrowing_id, current_user, False)

    def _decide_borrow(self, borrowing_id, current_user, approve):
        user_id = self._require_admin(current_user)
        if type(borrowing_id) is not int or borrowing_id <= 0:
            raise ValueError("Borrowing ID must be a positive integer.")
        today, due_date = self._today(), None
        if approve:
            if type(self.loan_period_days) is not int or self.loan_period_days <= 0:
                raise ValueError("Borrow approvals are unavailable. Please contact the library administrator.")
            try:
                due_date = today + timedelta(days=self.loan_period_days)
            except OverflowError:
                raise ValueError("The borrowing period is outside the supported date range.") from None

        conn = self._get_connection()
        try:
            # Each count sees the latest commit after waiting for book locks.
            conn.start_transaction(isolation_level="READ COMMITTED")
            admin = self.borrowing_repo.get_admin_profile(user_id, conn)
            self._validate_admin_profile(admin)
            owner = self.borrowing_repo.get_borrowing_owner(borrowing_id, conn)
            if owner is None:
                raise ValueError("Borrowing record not found.")
            reader = self.borrowing_repo.get_reader_for_update(owner["user_id"], conn)
            record = self.borrowing_repo.get_own_borrowing_for_update(
                borrowing_id, owner["reader_id"], conn
            )
            if not record or record["status"] != "Pending" or record["return_date"] is not None:
                raise ValueError("Only pending borrowing requests can be processed.")

            exhausted = []
            if approve:
                self._validate_reader_eligibility(reader, today)
                requested = self.borrowing_repo.get_request_books(borrowing_id, conn)
                quantity = sum(int(item["quantity"]) for item in requested)
                if quantity <= 0 or any(int(item["returned_quantity"]) for item in requested):
                    raise ValueError("Borrowing request details are invalid.")
                # Lock Reader, record, then books in ascending ID order.
                books = self.borrowing_repo.lock_requested_books(
                    [item["book_id"] for item in requested], conn
                )
                active = self.borrowing_repo.count_active_books(owner["reader_id"], conn)
                if active + quantity > self.MAX_BORROWED_BOOKS:
                    raise ValueError("The borrowing limit is 3 books.")
                for item in requested:
                    book = books[item["book_id"]]
                    if book is None:
                        raise ValueError("Book not found.")
                    held = self.borrowing_repo.count_active_copies_for_book(item["book_id"], conn)
                    available = max(0, int(book["quantity"]) - held)
                    if book["status"] != "Available" or available == 0:
                        raise ValueError("Book is currently unavailable.")
                    if int(item["quantity"]) > available:
                        raise ValueError(f"Only {available} copies are available.")
                    if int(item["quantity"]) == available:
                        exhausted.append(item["book_id"])

            status = "Borrowed" if approve else "Rejected"
            borrow_date = today.isoformat() if approve else record["borrow_date"]
            deadline = due_date.isoformat() if approve else record["due_date"]
            changed = self.borrowing_repo.save_borrow_decision(
                borrowing_id, owner["reader_id"], admin["admin_id"], status,
                borrow_date, deadline, conn,
            )
            if not changed:
                raise ValueError("This borrowing request has changed. Please refresh.")
            self.borrowing_repo.mark_exhausted_books(exhausted, conn)
            conn.commit()
            return {
                "borrowing_id": borrowing_id, "reader_id": owner["reader_id"],
                "admin_id": admin["admin_id"], "status": status,
                "borrow_date": str(borrow_date), "due_date": str(deadline),
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _calculate_overdue_fine(days_overdue, quantity):
        # Requirements: 2,000 VND per overdue day per book copy.
        return max(0, days_overdue) * quantity * 2000

    def _get_admin_records(self, status, current_user):
        user_id = self._require_admin(current_user)
        conn = self._get_connection()
        try:
            conn.start_transaction(readonly=True)
            self._validate_admin_profile(self.borrowing_repo.get_admin_profile(user_id, conn))
            records = self._group_admin_records(
                self.borrowing_repo.get_admin_record_rows(status, conn)
            )
            conn.commit()
            return records
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_pending_return_requests(self, current_user) -> list:
        return self._get_admin_records("ReturnRequested", current_user)

    def confirm_return(self, borrowing_id: int, current_user) -> dict:
        user_id = self._require_admin(current_user)
        if type(borrowing_id) is not int or borrowing_id <= 0:
            raise ValueError("Borrowing ID must be a positive integer.")

        conn = self._get_connection()
        try:
            conn.start_transaction(isolation_level="READ COMMITTED")
            admin = self.borrowing_repo.get_admin_profile(user_id, conn)
            self._validate_admin_profile(admin)
            owner = self.borrowing_repo.get_borrowing_owner(borrowing_id, conn)
            if owner is None:
                raise ValueError("Borrowing record not found.")
            # Keep the same lock order as approval: Reader, record, then books.
            self.borrowing_repo.get_reader_for_update(owner["user_id"], conn)
            record = self.borrowing_repo.get_own_borrowing_for_update(
                borrowing_id, owner["reader_id"], conn
            )
            if (not record or record["status"] != "ReturnRequested"
                    or record["return_date"] is not None or record["quantity"] <= 0):
                raise ValueError("Only pending return requests can be confirmed.")

            today = self._today()
            try:
                borrowed_on = date.fromisoformat(str(record["borrow_date"]))
                due_date = date.fromisoformat(str(record["due_date"]))
            except ValueError:
                raise ValueError("Borrowing dates are invalid.") from None
            if today < borrowed_on or due_date < borrowed_on:
                raise ValueError("Borrowing dates are invalid.")

            details = self.borrowing_repo.get_return_details(borrowing_id, conn)
            book_ids = [row["book_id"] for row in details if row["return_date"] is None]
            if len(book_ids) != record["quantity"]:
                raise ValueError("Return details are invalid.")
            books = self.borrowing_repo.lock_requested_books(book_ids, conn)
            if any(book is None for book in books.values()):
                raise ValueError("Book not found.")

            # Charge every copy by its actual return date, including legacy partial returns.
            amount = 0
            for row in details:
                try:
                    returned_on = (today if row["return_date"] is None
                                   else date.fromisoformat(str(row["return_date"])))
                except ValueError:
                    raise ValueError("A book return date is invalid.") from None
                if not borrowed_on <= returned_on <= today:
                    raise ValueError("A book return date is invalid.")
                amount += self._calculate_overdue_fine((returned_on - due_date).days, 1)
            if amount > 99999999:
                raise ValueError("The overdue charge exceeds the supported amount.")

            self.borrowing_repo.complete_return(
                borrowing_id, admin["admin_id"], today.isoformat(), len(book_ids), conn
            )
            fine = self.borrowing_repo.save_overdue_fine(
                borrowing_id, amount, today.isoformat(), admin["admin_id"], conn
            )
            self.borrowing_repo.refresh_book_statuses(book_ids, conn)
            conn.commit()
            return {
                "borrowing_id": borrowing_id, "reader_id": owner["reader_id"],
                "admin_id": admin["admin_id"], "status": "Returned",
                "return_date": today.isoformat(), "quantity": len(book_ids),
                "days_overdue": max(0, (today - due_date).days), **fine,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_all_borrowing_records(self, current_user) -> list:
        records = self._get_admin_records(None, current_user)
        return sorted(
            records,
            key=lambda row: (row["borrow_date"], row["borrowing_id"]),
            reverse=True,
        )

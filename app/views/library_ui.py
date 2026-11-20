import logging
import webbrowser
from collections import Counter
from queue import Empty, SimpleQueue
from threading import Thread
from datetime import date
from tkinter import filedialog, messagebox

import mysql.connector

from app.controllers.fine_controller import FineController
from app.controllers.member_controller import MemberController
from app.controllers.report_controller import ReportController
from app.repositories.fine_repository import FineRepository
from app.services.member_service import MemberService
from app.services.fine_momo_service import FineMomoService
from app.services.momo_gateway import MoMoGatewayError
from app.views.fine_management_view import FineManagementView
from app.views.fine_payment_view import FinePaymentView
from app.views.member_management_view import MemberManagementView
from app.views.profile_view import ProfileView
from app.views.renewal_view import RenewalView
from app.views.return_details_dialog import ReturnDetailsDialog
from app.views.workflow_list_view import WorkflowListView


def borrowing_row(record, reader_name=""):
    books = record["books"]
    status = record["status"]
    if status == "Borrowed":
        status = "Overdue" if str(record["due_date"]) < date.today().isoformat() else "Approved"
    return {
        **record,
        "id": record["borrowing_id"],
        "reader_name": record.get("reader_name", reader_name),
        "request_date": record["borrow_date"],
        "card_number": record["reader_id"],
        "book_title": ", ".join(book["title"] for book in books),
        "book_code": ", ".join(str(book["book_id"]) for book in books),
        "borrowed_date": record["borrow_date"],
        "returned_date": record["return_date"],
        "status": status,
        "books": [{**book, "code": book["book_id"]} for book in books],
    }


class LibraryUI:
    """Connect the desktop views to the existing application interfaces."""

    def __init__(self, app):
        self.app = app

    def data(self, result, title, fallback=None):
        if result["success"]:
            return result["data"]
        messagebox.showerror(title, result["message"], parent=self.app)
        return fallback

    def members_controller(self):
        return MemberController(
            MemberService(self.app.reader_repo, self.app.user_repo),
            self.app.current_user,
            self.app.auth_service,
        )

    def history(self, controller, is_admin):
        result = (controller.get_all_borrowing_records() if is_admin
                  else controller.get_my_borrowing_history())
        reader = self.app.current_user.get("full_name") or self.app.current_user.get("username", "")
        return [borrowing_row(row, reader) for row in self.data(result, "Borrowing history", [])]

    def borrow_approval(self, view_class, controller):
        def refresh():
            rows = self.data(controller.get_pending_borrow_requests(), "Borrow requests", [])
            view.set_requests([borrowing_row(row) for row in rows])

        def decide(row, action):
            result = action(row["id"])
            if result["success"]:
                refresh()
                messagebox.showinfo("Borrow requests", result["message"], parent=view)
            else:
                self.data(result, "Borrow requests")

        view = view_class(
            self.app, on_navigate=self.app.handle_navigation,
            on_approve=lambda row: decide(row, controller.approve_borrow),
            on_reject=lambda row: decide(row, controller.reject_borrow),
            on_refresh=refresh,
        )
        refresh()
        return view

    def returns(self, view_class, controller, is_admin):

        def refresh():
            if is_admin:
                result = controller.get_pending_return_requests()
                rows = [borrowing_row(row) for row in self.data(result, "Return books", [])]
            else:
                history = self.history(controller, False)
                view.set_pending_counts(
                    sum(row["status"] == "Pending" for row in history),
                    sum(row["status"] == "ReturnRequested" for row in history),
                )
                rows = [row for row in history if row["status"] in ("Approved", "Overdue")]
            view.set_transactions(rows)

        def submit(rows):
            if is_admin:
                copies = []
                for row in rows:
                    pending = self.data(controller.get_pending_return_copies(row["id"]), "Return confirmation")
                    if pending is None:
                        return
                    if pending:
                        copies.append((row["id"], pending))
                if copies:
                    ReturnDetailsDialog(view, copies, process)
                else:
                    refresh()
            else:
                process(dict.fromkeys(row["id"] for row in rows))

        def process(selected):
            messages = []
            failed = False
            for loan_id, items in selected.items():
                result = controller.confirm_return(loan_id, items) if is_admin else controller.request_return(loan_id)
                text = result["message"]
                if is_admin and result["success"] and result["data"]["status"] == "ReturnRequested":
                    text = "Selected copies were recorded. Remaining copies are still awaiting return."
                messages.append(f"#{loan_id}  {text}")
                failed |= not result["success"]
            refresh()
            dialog = messagebox.showwarning if failed else messagebox.showinfo
            dialog("Return books", "\n".join(messages), parent=view)

        view = view_class(
            self.app, on_navigate=self.app.handle_navigation,
            on_return_selected=submit, on_return_all=submit,
            on_refresh=refresh,
        )
        refresh()
        return view

    def renewals(self, controller, is_admin):
        if is_admin:
            def refresh():
                rows = self.data(controller.get_renewal_requests(), "Renewals", [])
                view.show_rows([
                    (
                        f"#{row['borrowing_id']}  {row['reader_name']}  |  {row['due_date']} to {row['requested_due_date']}",
                        [("Approve", lambda key=row["borrowing_id"]: decide(key, True)),
                         ("Reject", lambda key=row["borrowing_id"]: decide(key, False))],
                    )
                    for row in rows
                ], "No pending renewal requests.")

            def decide(borrowing_id, approved):
                result = controller.decide_renewal(borrowing_id, approved)
                if self.data(result, "Renewals") is not None:
                    refresh()

            view = WorkflowListView(self.app, "Renewal approval",
                                    lambda: self.app.handle_navigation("Dashboard"), refresh)
        else:
            def refresh():
                requests = self.data(controller.get_renewal_requests(), "Renewals", [])
                pending = {row["borrowing_id"] for row in requests if row["status"] == "Pending"}
                view.set_transactions([
                    row for row in self.history(controller, False)
                    if row["status"] == "Approved" and not row["renewal_count"] and row["id"] not in pending
                ])

            def request(row, new_due):
                result = controller.request_renewal(row["id"], new_due)
                if self.data(result, "Renewals") is not None:
                    messagebox.showinfo("Renewals", result["message"], parent=view)
                    refresh()

            view = RenewalView(self.app, on_navigate=self.app.handle_navigation, on_renew=request)
        refresh()
        return view

    def notifications(self, controller):
        def refresh():
            rows = []
            for loan in self.history(controller, False):
                label = f"#{loan['id']}  {loan['book_title']}"
                if loan["status"] == "Rejected":
                    rows.append((f"{label}: Borrowing request rejected.", []))
                elif loan["status"] != "Pending":
                    rows.append((f"{label}: Borrowing request approved. Due {loan['due_date']}.", []))
                if loan["returned_date"]:
                    rows.append((f"{label}: Return confirmed on {loan['returned_date']}.", []))
            for request in self.data(controller.get_renewal_requests(), "Renewals", []):
                rows.append((f"#{request['borrowing_id']}: Renewal {request['status'].lower()} ({request['requested_due_date']}).", []))
            view.show_rows(rows, "No borrowing or return updates yet.")

        view = WorkflowListView(self.app, "Notifications",
                                lambda: self.app.handle_navigation("Dashboard"), refresh)
        refresh()
        return view

    def profile(self):
        controller = self.members_controller()
        user_id = self.app.current_user["user_id"]
        view = ProfileView(
            self.app,
            on_back=lambda: self.app.handle_navigation("Dashboard"),
            on_save=lambda fields: controller.update_my_profile(user_id, fields),
        )
        view.set_profile(self.data(controller.get_my_profile(user_id), "My profile"))
        return view

    def members(self):
        return MemberManagementView(
            self.app, controller=self.members_controller(),
            on_back=lambda: self.app.handle_navigation("Dashboard"),
            on_create=self.app.show_admin_registration,
        )

    def fines(self, is_admin, payment=False):
        controller = FineController(current_user=self.app.current_user)
        repository = FineRepository() if is_admin else None

        def refresh():
            if is_admin:
                readers = self.data(self.members_controller().get_all_readers(), "Fines", [])
                rows = [
                    {**fine, "reader_name": reader["full_name"]}
                    for reader in readers
                    for fine in repository.get_fines_by_reader(reader["readerID"])
                ]
            else:
                rows = self.data(controller.get_my_fines(), "My fines", [])

            view.set_fines([
                {**row, "id": row["fine_id"], "book_title": row["book_titles"],
                 "created_date": row["fine_date"], "status": row["payment_status"]}
                for row in rows
            ])

        def pay(row):
            if not messagebox.askyesno(
                "Confirm fine payment", f"Record payment for fine #{row['id']}?", parent=view
            ):
                return
            result = controller.confirm_payment(row["id"])
            if result["success"]:
                refresh()
                messagebox.showinfo("Fine payment", result["message"], parent=view)
            else:
                self.data(result, "Fine payment")

        def use_momo(row, operation):
            user = dict(self.app.current_user)
            result = SimpleQueue()
            view.set_payment_busy(True)
            view.message_label.configure(text="Contacting MoMo Sandbox...")

            def request():
                try:
                    service = FineMomoService()
                    response = getattr(service, operation)(row["id"], user)
                    result.put((True, response))
                except (ValueError, PermissionError, MoMoGatewayError) as error:
                    result.put((False, str(error)))
                except mysql.connector.Error as error:
                    logging.getLogger(__name__).warning("MoMo payment database error %s", error.errno)
                    result.put((False, "Cannot access the payment database. Check the MoMo migration."))
                except Exception:
                    logging.getLogger(__name__).exception("Unexpected MoMo payment error")
                    result.put((False, "Unable to process the payment. Try checking its status again."))

            def receive():
                if not view.winfo_exists() or self.app.current_view is not view:
                    return
                try:
                    success, response = result.get_nowait()
                except Empty:
                    self.app.after(100, receive)
                    return
                view.set_payment_busy(False)
                if not success:
                    view.message_label.configure(text=response)
                    return
                if operation == "start":
                    try:
                        opened = webbrowser.open(response)
                    except webbrowser.Error:
                        opened = False
                    text = (
                        "Finish payment in your browser, then select Check MoMo status."
                        if opened else "Could not open the browser. Select Pay with MoMo Sandbox to retry."
                    )
                else:
                    refresh()
                    text = {
                        "Paid": "MoMo verified this payment. The fine is now paid.",
                        "Failed": "The MoMo payment failed or expired. You can start a new payment.",
                        "Pending": "MoMo has not confirmed payment yet. Check again after completing it.",
                    }[response]
                view.message_label.configure(text=text)

            Thread(target=request, daemon=True).start()
            self.app.after(100, receive)

        if is_admin and not payment:
            view = FineManagementView(self.app, on_navigate=self.app.handle_navigation, on_pay=pay)
        else:
            view = FinePaymentView(
                self.app, on_navigate=self.app.handle_navigation,
                on_payment=pay if is_admin else lambda row: use_momo(row, "start"),
                on_check_payment=None if is_admin else lambda row: use_momo(row, "check"),
                is_admin=is_admin,
            )
        refresh()
        return view

    def admin_statistics(self, borrowing_controller):
        controller = ReportController(current_user=self.app.current_user)
        readers = self.data(controller.get_reader_statistics(), "Reader statistics", {})
        status = self.data(controller.get_book_status_statistics(), "Book status", {})
        catalog = self.data(controller.get_statistics(), "Book statistics", {})
        transactions = self.history(borrowing_controller, True)
        approved = [row for row in transactions if row["status"] not in ("Pending", "Rejected")]
        by_month = Counter(row["borrowed_date"][:7] for row in approved if row["borrowed_date"])
        return {
            "chart_months": [by_month[f"{date.today().year}-{month:02}"] for month in range(1, 13)],
            "available_titles": catalog.get("available_titles"),
            "unavailable_titles": catalog.get("unavailable_titles"),
            "Total Borrowings": len(approved),
            "Books Borrowed": status.get("currently_borrowed"),
            "Active Readers": readers.get("active_readers"),
            "Overdue Books": status.get("overdue"),
            "transactions": transactions,
        }

    def reports(self, view_class, borrowing_controller):
        controller = ReportController(current_user=self.app.current_user)
        catalog = self.data(controller.get_statistics(), "Book statistics", {})
        readers = self.data(controller.get_reader_statistics(), "Reader statistics", {})
        status = self.data(controller.get_book_status_statistics(), "Book status", {})

        reports = {
            "Borrowing and returns": ("borrowing_report", controller.get_borrowing_report),
            "Book inventory": ("book_statistics", controller.get_statistics),
            "Reader accounts": ("reader_statistics", controller.get_reader_statistics),
            "Book status": ("book_status_statistics", controller.get_book_status_statistics),
            "Fines and payments": ("fine_statistics", controller.get_fine_statistics),
        }

        def preview(label, start, end):
            _, fetch = reports[label]
            args = (start.isoformat(), end.isoformat()) if start is not None else ()
            return self.data(fetch(*args), "Reports")

        def export_csv(label, start, end):
            report_type, _ = reports[label]
            path = filedialog.asksaveasfilename(
                parent=view, defaultextension=".csv", filetypes=[("CSV report", "*.csv")],
                initialfile=report_type + ".csv"
            )
            if path:
                dates = (start.isoformat(), end.isoformat()) if start is not None else ()
                result = controller.export_report(report_type, path, *dates)
                if self.data(result, "Reports") is not None:
                    messagebox.showinfo("Export report", result["message"], parent=view)

        def export(start, end, extension):
            report = self.data(controller.get_borrowing_report(start.isoformat(), end.isoformat()), "Reports")
            if report is None:
                return
            path = filedialog.asksaveasfilename(
                parent=view, defaultextension=extension,
                filetypes=[("Report", "*" + extension)],
                initialfile=f"borrowing-{start}-{end}{extension}"
            )
            if not path:
                return
            try:
                from app.views.report_export import save_report
                save_report(path, start, end, report)
            except (OSError, ImportError, ValueError) as error:
                messagebox.showerror("Export report", str(error), parent=view)
            else:
                messagebox.showinfo("Export report", f"Saved {path}", parent=view)

        view = view_class(
            self.app, on_navigate=self.app.handle_navigation, on_logout=self.app.handle_logout,
            report_types=list(reports), on_preview=preview, on_export_csv=export_csv,
            on_export_pdf=lambda start, end: export(start, end, ".pdf"),
            on_export_excel=lambda start, end: export(start, end, ".xlsx"),
            catalog=catalog, readers=readers, status=status,
            transactions=self.history(borrowing_controller, True),
        )
        return view

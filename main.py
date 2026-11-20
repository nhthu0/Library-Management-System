
import customtkinter as ctk
import mysql.connector
from tkinter import messagebox

from app.database.connection import get_connection


from app.repositories.user_repository import UserRepository
from app.repositories.reader_repository import ReaderRepository

from app.services.auth_service import AuthService
from app.services.password_reset_service import PasswordResetService

from app.controllers.auth_controller import AuthController
from app.controllers.book_controller import BookController
from app.controllers.borrowing_controller import BorrowingController

from app.views.login_view import LoginView
from app.views.register_view import RegisterView
from app.views.password_reset_view import PasswordResetView
from app.views.admin_dashboard_view import AdminDashboardView
from app.views.reader_dashboard_view import ReaderDashboardView
from app.views.borrow_request_view import BorrowRequestView

from app.views.book_management_view import BookManagementView
from app.views.book_search_view import BookSearchView
from app.views.borrow_approval_view import BorrowApprovalView
from app.views.borrowing_history_view import BorrowingHistoryView
from app.views.return_request_view import ReturnRequestView
from app.views.reports_view import ReportsView
from app.views.return_confirmation_view import ReturnConfirmationView
from app.views.library_ui import LibraryUI

LOAN_PERIOD_DAYS = 30


class LibraryManagementApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Library Management System")
        self.state("zoomed")
        self.minsize(1100, 650)

        self.current_view = None
        self.current_page = None
        self._outgoing_view = None
        self._transition_job = None
        self.current_user = None
        self.borrow_selection = []
        self.library_ui = LibraryUI(self)
        self.db_connection = None

        # Connect database
        try:
            self.db_connection = get_connection()

            # Initialize repositories
            self.user_repo = UserRepository(
                self.db_connection
            )

            self.reader_repo = ReaderRepository(
                self.db_connection
            )

            # Initialize services
            self.auth_service = AuthService(
                self.user_repo,
                self.reader_repo
            )

            # Initialize controllers
            self.auth_controller = AuthController(
                self.auth_service
            )

        except mysql.connector.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Unable to connect to MySQL:\n{error}"
            )
            self.destroy()
            return

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

        self.show_login()

    # ==========================================
    # COMMON VIEW
    # ==========================================

    def show_view(self, view):

        self.finish_view_transition()
        previous = self.current_view
        self.current_view = view
        self.current_page = None

        if previous is None or isinstance(previous, LoginView) or isinstance(view, LoginView):
            view.place(relwidth=1, relheight=1)
            if previous is not None:
                previous.destroy()
            return

        self._outgoing_view = previous
        slide_offset = 8
        view.place(x=slide_offset, relwidth=1, relheight=1)
        view.lift()

        def slide(frame):
            self._transition_job = None
            if frame == 7:
                self.finish_view_transition()
                return

            progress = frame / 7
            view.place_configure(x=round(slide_offset * (1 - progress) ** 2))
            self._transition_job = self.after(16, slide, frame + 1)

        self._transition_job = self.after(16, slide, 1)

    def finish_view_transition(self):
        if self._transition_job is not None:
            self.after_cancel(self._transition_job)
            self._transition_job = None

        if self._outgoing_view is not None:
            self.current_view.place_configure(x=0)
            self._outgoing_view.destroy()
            self._outgoing_view = None

    # ==========================================
    # LOGIN
    # ==========================================

    def show_login(self):

        self.current_user = None
        self.borrow_selection.clear()

        login_view = LoginView(
            self,
            on_login=self.handle_login,
            on_register=self.handle_register,
            on_forgot_password=self.handle_forgot_password
        )

        self.show_view(login_view)

    def handle_login(self, username, password):

        result = self.auth_controller.login(
            username,
            password
        )

        if not result["success"]:
            self.current_view.message.configure(
                text=result["message"]
            )
            return

        user_data = result["data"]
        role = str(user_data.get("role", "")).upper()

        self.current_user = user_data

        if role == "ADMIN":
            self.show_admin_dashboard()

        elif role == "READER":
            self.show_reader_dashboard()

        else:
            self.current_user = None

            messagebox.showerror(
                "Login Error",
                f"Unsupported user role: {role}"
            )

    # ==========================================
    # DASHBOARDS
    # ==========================================

    def show_admin_dashboard(self):

        dashboard = AdminDashboardView(
            self,
            on_navigate=self.handle_navigation,
            on_logout=self.handle_logout,
            statistics=self.library_ui.admin_statistics(self.borrowing_controller()),
        )

        self.show_view(dashboard)
        self.current_page = "dashboard"

    def show_reader_dashboard(self):

        dashboard = ReaderDashboardView(
            self,
            on_navigate=self.handle_navigation,
            on_logout=self.handle_logout,
            transactions=self.library_ui.history(self.borrowing_controller(), False),
        )

        self.show_view(dashboard)
        self.current_page = "dashboard"

    # ==========================================
    # NAVIGATION
    # ==========================================

    def borrowing_controller(self):
        return BorrowingController(
            current_user=self.current_user,
            loan_period_days=LOAN_PERIOD_DAYS
        )

    def handle_navigation(self, page_name):

        print("CLICKED:", repr(page_name))

        try:
            page = page_name.strip().lower()
            page = {
                "history": "borrowing history",
                "browse books": "booklist",
                "home": "dashboard",
                "manage books": "book management",
                "borrow approval": "borrow books",
                "return confirmation": "return books",
                "reports": "statistics",
            }.get(page, page)
            role = str((self.current_user or {}).get("role", "")).upper()
            if role not in ("ADMIN", "READER"):
                return
            is_admin = role == "ADMIN"

            if page == self.current_page:
                return

            # Book Management
            if page == "book management" and is_admin:

                controller = BookController(
                    current_user=self.current_user
                )

                view = BookManagementView(
                    self,
                    on_navigate=self.handle_navigation,
                    on_logout=self.handle_logout,
                    controller=controller
                )

            # Booklist
            elif page == "booklist":

                controller = BookController(current_user=self.current_user)
                view = BookSearchView(
                    self,
                    on_navigate=self.handle_navigation,
                    controller=controller,
                    is_admin=is_admin
                )
                view.search_books()

            # Borrow Books
            elif page == "borrow books":

                borrowing_controller = self.borrowing_controller()
                if not is_admin:
                    book_controller = BookController(current_user=self.current_user)
                    view = BorrowRequestView(
                        self,
                        on_navigate=self.handle_navigation,
                        on_search_books=book_controller.search_books,
                        on_request_borrow=borrowing_controller.request_borrow,
                        on_load_history=borrowing_controller.get_my_borrowing_history,
                        selected_books=self.borrow_selection
                    )
                    view.search_books()
                else:
                    view = self.library_ui.borrow_approval(
                        BorrowApprovalView, borrowing_controller
                    )

            # Return Books
            elif page == "return books":

                view = self.library_ui.returns(
                    ReturnConfirmationView if is_admin else ReturnRequestView,
                    self.borrowing_controller(), is_admin
                )

            # Borrowing History
            elif page in ("borrowing history", "return history", "borrow status"):

                view = BorrowingHistoryView(self, on_navigate=self.handle_navigation)
                rows = self.library_ui.history(self.borrowing_controller(), is_admin)
                if page == "return history":
                    rows = [row for row in rows if row["returned_date"]]
                elif page == "borrow status":
                    rows = [
                        {**row, "status": (
                            "Approved" if row["status"] in ("Borrowed", "Overdue", "ReturnRequested", "Returned")
                            else row["status"]
                        )}
                        for row in rows
                    ]
                view.set_transactions(rows)

            # Statistics
            elif page == "statistics" and is_admin:

                view = self.library_ui.reports(ReportsView, self.borrowing_controller())

            elif (page == "renewal approval" and is_admin) or (page == "renew borrowing" and not is_admin):
                view = self.library_ui.renewals(self.borrowing_controller(), is_admin)

            elif page == "notifications" and not is_admin:
                view = self.library_ui.notifications(self.borrowing_controller())

            elif page == "member management" and is_admin:
                view = self.library_ui.members()

            elif page == "my profile" and not is_admin:
                view = self.library_ui.profile()

            elif page in ("fine management", "fine payment", "my fines"):
                view = self.library_ui.fines(is_admin, payment=page == "fine payment")

            # Dashboard
            elif page == "dashboard":

                if not is_admin:
                    self.show_reader_dashboard()
                else:
                    self.show_admin_dashboard()

                return

            else:
                messagebox.showinfo(
                    "Navigation",
                    f"{page_name} is not connected yet."
                )
                return

            self.show_view(view)
            self.current_page = page

            print("DEBUG: Opened", page_name)

        except Exception as error:

            messagebox.showerror(
                "Navigation Error",
                str(error)
            )

            print("ERROR:", error)

    # ==========================================
    # REGISTER
    # ==========================================

    def handle_register(self):

        view = RegisterView(
            self,
            on_register=self.submit_registration,
            on_back=self.show_login
        )
        self.show_view(view)

    def show_admin_registration(self):
        controller = self.library_ui.members_controller()

        def back():
            self.handle_navigation("Member Management")

        def submit(fields):
            result = controller.create_reader(fields)
            if not result["success"]:
                view.show_error(result["message"])
                return
            messagebox.showinfo("Members", result["message"], parent=view)
            back()

        view = RegisterView(self, on_register=submit, on_back=back, admin_mode=True)
        self.show_view(view)

    def submit_registration(self, user_data):
        result = self.auth_controller.register(user_data)
        if not result["success"]:
            self.current_view.show_error(result["message"])
            return

        self.show_login()
        messagebox.showinfo("Registration", result["message"], parent=self)

    # ==========================================
    # FORGOT PASSWORD
    # ==========================================

    def handle_forgot_password(self):

        service = PasswordResetService(self.db_connection, self.auth_service.hash_password)
        self.show_view(PasswordResetView(
            self, request=service.request, reset=service.reset, on_back=self.show_login
        ))

    # ==========================================
    # LOGOUT
    # ==========================================

    def handle_logout(self):

        self.auth_controller.logout()
        self.show_login()

    # ==========================================
    # CLOSE APPLICATION
    # ==========================================

    def close_application(self):

        self.finish_view_transition()

        try:
            if (
                self.db_connection
                and self.db_connection.is_connected()
            ):
                self.db_connection.close()

        except mysql.connector.Error:
            pass

        self.destroy()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")

    app = LibraryManagementApp()
    app.mainloop()

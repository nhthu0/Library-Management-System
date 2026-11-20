
from pathlib import Path
from datetime import datetime, date
import calendar

import customtkinter as ctk
from PIL import Image


# ==========================================
# COLORS
# ==========================================

BG = "#F7FAF9"
SIDEBAR = "#2D6857"
MENU_BG = "#397461"
ACTIVE = "#70D18F"
GREEN = "#008D3F"
DARK_GREEN = "#007536"
WHITE = "#FFFFFF"
TEXT = "#2D3A40"
MUTED = "#8293A5"
BORDER = "#E5EBE9"
LIGHT = "#F2FBF6"
RED = "#D94B55"


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not value:
        return None

    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(
                str(value).strip(), fmt
            ).date()
        except ValueError:
            continue

    return None


def display_date(value):
    result = parse_date(value)
    return result.strftime("%d/%m/%Y") if result else "-"


# ==========================================
# DATE PICKER
# ==========================================


class DatePicker(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.popup = None
        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self,
            height=36,
            placeholder_text="DD/MM/YYYY",
            fg_color=WHITE,
            border_color=BORDER,
            text_color=TEXT,
            font=("Segoe UI", 11)
        )
        self.entry.grid(row=0, column=0, sticky="ew")

        # Click the date field to open calendar
        self.entry.bind(
            "<Button-1>",
            lambda event: self.open_calendar()
        )

        self.calendar_button = ctk.CTkButton(
            self,
            text="▦",
            width=38,
            height=36,
            fg_color="#EAF3EE",
            hover_color="#DCECE3",
            text_color=SIDEBAR,
            border_color=BORDER,
            border_width=1,
            font=("Segoe UI", 17),
            command=self.open_calendar
        )
        self.calendar_button.grid(
            row=0,
            column=1,
            padx=(5, 0)
        )

    def get(self):
        return self.entry.get().strip()

    def set_date(self, value):
        parsed = parse_date(value)

        self.entry.delete(0, "end")

        if parsed:
            self.entry.insert(
                0,
                parsed.strftime("%d/%m/%Y")
            )

    def clear(self):
        self.entry.delete(0, "end")

    def open_calendar(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.lift()
            return

        selected = parse_date(self.get()) or date.today()
        year, month = selected.year, selected.month

        popup = ctk.CTkToplevel(self)
        self.popup = popup

        popup.title("Select date")
        popup.geometry("325x355")
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())

        header = ctk.CTkFrame(
            popup,
            fg_color="transparent"
        )
        header.pack(fill="x", padx=12, pady=12)
        header.grid_columnconfigure(1, weight=1)

        month_label = ctk.CTkLabel(
            header,
            text="",
            text_color=TEXT,
            font=("Segoe UI", 14, "bold")
        )
        month_label.grid(row=0, column=1)

        days_frame = ctk.CTkFrame(
            popup,
            fg_color="transparent"
        )
        days_frame.pack(
            fill="both",
            expand=True,
            padx=12
        )

        for col in range(7):
            days_frame.grid_columnconfigure(col, weight=1)

        def choose_day(value):
            self.set_date(value)
            popup.destroy()
            self.popup = None

        def render():
            for child in days_frame.winfo_children():
                child.destroy()

            month_label.configure(
                text=f"{calendar.month_name[month]} {year}"
            )

            for col, name in enumerate(
                ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
            ):
                ctk.CTkLabel(
                    days_frame,
                    text=name,
                    text_color=MUTED,
                    font=("Segoe UI", 10, "bold")
                ).grid(row=0, column=col, pady=5)

            current = parse_date(self.get())

            for row, week in enumerate(
                calendar.monthcalendar(year, month),
                start=1
            ):
                for col, day in enumerate(week):
                    if day == 0:
                        continue

                    value = date(year, month, day)
                    active = value == current

                    ctk.CTkButton(
                        days_frame,
                        text=str(day),
                        width=35,
                        height=32,
                        fg_color=GREEN if active else "transparent",
                        text_color=WHITE if active else TEXT,
                        hover_color="#DCECE3",
                        command=lambda d=value: choose_day(d)
                    ).grid(
                        row=row,
                        column=col,
                        padx=2,
                        pady=2
                    )

        def change_month(delta):
            nonlocal year, month

            month += delta

            if month < 1:
                month = 12
                year -= 1
            elif month > 12:
                month = 1
                year += 1

            render()

        ctk.CTkButton(
            header,
            text="‹",
            width=32,
            height=30,
            fg_color="transparent",
            text_color=GREEN,
            hover_color=LIGHT,
            font=("Segoe UI", 22),
            command=lambda: change_month(-1)
        ).grid(row=0, column=0)

        ctk.CTkButton(
            header,
            text="›",
            width=32,
            height=30,
            fg_color="transparent",
            text_color=GREEN,
            hover_color=LIGHT,
            font=("Segoe UI", 22),
            command=lambda: change_month(1)
        ).grid(row=0, column=2)

        ctk.CTkButton(
            popup,
            text="Today",
            height=32,
            fg_color=LIGHT,
            text_color=GREEN,
            hover_color="#DCECE3",
            command=lambda: choose_day(date.today())
        ).pack(
            fill="x",
            padx=15,
            pady=(5, 12)
        )

        render()
        popup.grab_set()

    def __init__(self, master):
        super().__init__(
            master,
            fg_color="transparent"
        )

        self.popup = None
        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self,
            height=36,
            placeholder_text="DD/MM/YYYY",
            fg_color=WHITE,
            border_color=BORDER,
            text_color=TEXT,
            font=("Segoe UI", 11)
        )
        self.entry.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        ctk.CTkButton(
            self,
            text="▦",
            width=38,
            height=36,
            fg_color="#EAF3EE",
            hover_color="#DCECE3",
            text_color=SIDEBAR,
            border_color=BORDER,
            border_width=1,
            font=("Segoe UI", 17),
            command=self.open_calendar
        ).grid(
            row=0,
            column=1,
            padx=(5, 0)
        )

    def get(self):
        return self.entry.get().strip()

    def set_date(self, value):
        self.entry.delete(0, "end")

        if value:
            parsed = parse_date(value)

            if parsed:
                self.entry.insert(
                    0,
                    parsed.strftime("%d/%m/%Y")
                )

    def clear(self):
        self.entry.delete(0, "end")

    def open_calendar(self):
        if self.popup and self.popup.winfo_exists():
            self.popup.lift()
            return

        current = parse_date(self.get()) or date.today()
        year = current.year
        month = current.month

        popup = ctk.CTkToplevel(self)
        self.popup = popup

        popup.title("Select date")
        popup.geometry("325x350")
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())

        header = ctk.CTkFrame(
            popup,
            fg_color="transparent"
        )
        header.pack(
            fill="x",
            padx=12,
            pady=12
        )
        header.grid_columnconfigure(1, weight=1)

        month_label = ctk.CTkLabel(
            header,
            text="",
            text_color=TEXT,
            font=("Segoe UI", 14, "bold")
        )
        month_label.grid(row=0, column=1)

        days_frame = ctk.CTkFrame(
            popup,
            fg_color="transparent"
        )
        days_frame.pack(
            fill="both",
            expand=True,
            padx=12
        )

        for col in range(7):
            days_frame.grid_columnconfigure(
                col,
                weight=1
            )

        def choose_day(value):
            self.set_date(value)
            popup.destroy()
            self.popup = None

        def render():
            for widget in days_frame.winfo_children():
                widget.destroy()

            month_label.configure(
                text=f"{calendar.month_name[month]} {year}"
            )

            for col, name in enumerate(
                ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
            ):
                ctk.CTkLabel(
                    days_frame,
                    text=name,
                    text_color=MUTED,
                    font=("Segoe UI", 10, "bold")
                ).grid(
                    row=0,
                    column=col,
                    pady=5
                )

            selected = parse_date(self.get())

            for row, week in enumerate(
                calendar.monthcalendar(year, month),
                start=1
            ):
                for col, day in enumerate(week):
                    if day == 0:
                        continue

                    value = date(year, month, day)
                    active = value == selected

                    ctk.CTkButton(
                        days_frame,
                        text=str(day),
                        width=35,
                        height=32,
                        fg_color=(
                            GREEN if active else "transparent"
                        ),
                        text_color=(
                            WHITE if active else TEXT
                        ),
                        hover_color="#DCECE3",
                        command=lambda d=value: choose_day(d)
                    ).grid(
                        row=row,
                        column=col,
                        padx=2,
                        pady=2
                    )

        def change_month(delta):
            nonlocal month, year

            month += delta

            if month < 1:
                month = 12
                year -= 1

            elif month > 12:
                month = 1
                year += 1

            render()

        ctk.CTkButton(
            header,
            text="‹",
            width=32,
            height=30,
            fg_color="transparent",
            text_color=GREEN,
            hover_color=LIGHT,
            font=("Segoe UI", 22),
            command=lambda: change_month(-1)
        ).grid(row=0, column=0)

        ctk.CTkButton(
            header,
            text="›",
            width=32,
            height=30,
            fg_color="transparent",
            text_color=GREEN,
            hover_color=LIGHT,
            font=("Segoe UI", 22),
            command=lambda: change_month(1)
        ).grid(row=0, column=2)

        ctk.CTkButton(
            popup,
            text="Today",
            height=32,
            fg_color=LIGHT,
            text_color=GREEN,
            hover_color="#DCECE3",
            command=lambda: choose_day(date.today())
        ).pack(
            fill="x",
            padx=15,
            pady=(5, 12)
        )

        render()
        popup.grab_set()


# ==========================================
# RENEWAL VIEW
# ==========================================

class RenewalView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_navigate=None,
        on_renew=None
    ):
        super().__init__(
            master,
            fg_color=BG
        )

        self.on_navigate = on_navigate
        self.on_renew = on_renew

        self.assets = (
            Path(__file__).resolve().parents[1]
            / "assets"
        )

        self.images = []
        self.transactions = []
        self.filtered_transactions = []
        self.selected_transaction = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()

        self.main = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            corner_radius=0
        )

        self.main.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=20,
            pady=20
        )

        self.main.grid_columnconfigure(0, weight=1)

        self.build_header()
        self.build_search()
        self.build_list()
        self.build_details()

    # ======================================
    # COMMON
    # ======================================

    def label(
        self,
        parent,
        text,
        size=12,
        color=TEXT,
        bold=False,
        **kwargs
    ):
        return ctk.CTkLabel(
            parent,
            text=text,
            text_color=color,
            font=(
                "Segoe UI",
                size,
                "bold" if bold else "normal"
            ),
            **kwargs
        )

    def card(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color=WHITE,
            corner_radius=11,
            border_width=1,
            border_color=BORDER
        )

    def load_image(self, path, size, tint=None):
        if not path.is_file():
            return None

        try:
            with Image.open(path) as source:
                image = source.convert("RGBA")

            if tint:
                colored = Image.new(
                    "RGBA",
                    image.size,
                    (*tint, 255)
                )
                colored.putalpha(
                    image.getchannel("A")
                )
                image = colored

            result = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=size
            )

            self.images.append(result)
            return result

        except (OSError, ValueError):
            return None

    def clear_frame(self, frame):
        for child in frame.winfo_children():
            child.destroy()

    # ======================================
    # SIDEBAR
    # ======================================

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=170,
            fg_color=SIDEBAR,
            corner_radius=12
        )

        sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(15, 0),
            pady=15
        )

        sidebar.grid_propagate(False)

        logo = self.load_image(
            self.assets / "logo.png",
            (40, 40)
        )

        if logo:
            ctk.CTkLabel(
                sidebar,
                text="",
                image=logo
            ).pack(pady=(20, 5))

        self.label(
            sidebar,
            "Library",
            14,
            WHITE,
            True
        ).pack()

        self.label(
            sidebar,
            "Library System",
            10,
            "#C5DCD4"
        ).pack(pady=(2, 26))

        menus = [
            ("dashboard.png", "Home"),
            ("borrow.png", "Borrow books"),
            ("booklist.png", "Return books"),
            ("history.png", "History"),
            ("management.png", "Manage books"),
            ("statistics.png", "Statistics")
        ]

        for filename, name in menus:
            # Renewal belongs to the borrowing section.
            active = name == "Borrow books"

            icon = self.load_image(
                self.assets / "icons" / filename,
                (16, 16),
                (
                    (42, 102, 77)
                    if active
                    else (231, 245, 238)
                )
            )

            ctk.CTkButton(
                sidebar,
                text=name,
                image=icon,
                compound="left",
                anchor="w",
                height=38,
                corner_radius=6,
                fg_color=(
                    ACTIVE if active else MENU_BG
                ),
                hover_color=(
                    "#82DB9F" if active else "#477F6D"
                ),
                text_color=(
                    "#285D48" if active else WHITE
                ),
                font=(
                    "Segoe UI",
                    11,
                    "bold" if active else "normal"
                ),
                command=lambda page=name: self.navigate(page)
            ).pack(
                fill="x",
                padx=10,
                pady=3
            )

        ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        ).pack(
            fill="both",
            expand=True
        )

        footer = ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        )
        footer.pack(pady=(0, 20))

        self.label(
            footer,
            "Librarian",
            11,
            WHITE,
            True
        ).pack()

        self.label(
            footer,
            "Library",
            10,
            "#C5DCD4"
        ).pack(pady=(3, 6))

        self.label(
            footer,
            "LG",
            10,
            "#326A50",
            True,
            width=35,
            height=35,
            fg_color=ACTIVE,
            corner_radius=18
        ).pack()

    # ======================================
    # HEADER
    # ======================================

    def build_header(self):
        header = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(8, 20)
        )

        self.label(
            header,
            "Renew borrowing",
            22,
            TEXT,
            True
        ).pack(anchor="w")

        self.label(
            header,
            "Search and request a book borrowing renewal",
            11,
            MUTED
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

    # ======================================
    # SEARCH
    # ======================================

    def build_search(self):
        card = self.card(self.main)

        card.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 16)
        )

        self.label(
            card,
            "Search borrowed books",
            14,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 5)
        )

        self.label(
            card,
            "Search by reader name, book title or transaction ID",
            11,
            MUTED
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 14)
        )

        search_row = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        search_row.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        self.search_entry = ctk.CTkEntry(
            search_row,
            height=36,
            placeholder_text=(
                "Enter reader name, book title or transaction ID..."
            ),
            fg_color=WHITE,
            border_color=BORDER,
            text_color=TEXT,
            font=("Segoe UI", 11)
        )

        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )

        self.search_entry.bind(
            "<Return>",
            lambda event: self.search_transactions()
        )

        ctk.CTkButton(
            search_row,
            text="Search",
            width=100,
            height=36,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            command=self.search_transactions
        ).pack(side="right")

    # ======================================
    # BORROWED BOOKS LIST
    # ======================================

    def build_list(self):
        card = self.card(self.main)

        card.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 16)
        )

        top = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        top.pack(
            fill="x",
            padx=15,
            pady=(15, 10)
        )

        self.label(
            top,
            "Borrowed books",
            14,
            TEXT,
            True
        ).pack(side="left")

        self.count_label = self.label(
            top,
            "0 transactions",
            10,
            MUTED
        )
        self.count_label.pack(side="right")

        self.list_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
            height=180
        )

        self.list_frame.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        self.render_transactions()

    def render_transactions(self):
        self.clear_frame(self.list_frame)

        self.count_label.configure(
            text=f"{len(self.filtered_transactions)} transactions"
        )

        if not self.filtered_transactions:
            empty = ctk.CTkFrame(
                self.list_frame,
                fg_color="transparent",
                height=150
            )
            empty.pack(fill="x")
            empty.pack_propagate(False)

            self.label(
                empty,
                "No borrowed books found",
                12,
                MUTED
            ).place(
                relx=0.5,
                rely=0.45,
                anchor="center"
            )

            self.label(
                empty,
                "Search to display borrowing transactions",
                10,
                MUTED
            ).place(
                relx=0.5,
                rely=0.62,
                anchor="center"
            )
            return

        for item in self.filtered_transactions:
            selected = (
                self.selected_transaction is item
            )

            row = ctk.CTkFrame(
                self.list_frame,
                fg_color=LIGHT,
                corner_radius=7,
                border_width=1 if selected else 0,
                border_color=GREEN
            )

            row.pack(
                fill="x",
                pady=5
            )

            info = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            info.pack(
                side="left",
                fill="both",
                expand=True,
                padx=12,
                pady=10
            )

            self.label(
                info,
                str(item.get("book_title", "Untitled book")),
                12,
                TEXT,
                True
            ).pack(anchor="w")

            reader = str(
                item.get("reader_name", "-")
            )

            transaction_id = str(
                item.get("id", "-")
            )

            self.label(
                info,
                f"Reader: {reader} | ID: {transaction_id}",
                10,
                MUTED
            ).pack(
                anchor="w",
                pady=(4, 0)
            )

            self.label(
                info,
                "Due date: "
                + display_date(item.get("due_date")),
                10,
                MUTED
            ).pack(
                anchor="w",
                pady=(3, 0)
            )

            ctk.CTkButton(
                row,
                text="Selected" if selected else "Select",
                width=90,
                height=32,
                fg_color=(
                    GREEN if selected else WHITE
                ),
                text_color=(
                    WHITE if selected else GREEN
                ),
                border_width=0 if selected else 1,
                border_color=GREEN,
                hover_color=DARK_GREEN if selected else "#DCECE3",
                command=lambda record=item: self.select_transaction(
                    record
                )
            ).pack(
                side="right",
                padx=12
            )

    # ======================================
    # RENEWAL DETAILS
    # ======================================

    def build_details(self):
        card = self.card(self.main)

        card.grid(
            row=3,
            column=0,
            sticky="ew"
        )

        self.label(
            card,
            "Renewal details",
            14,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 12)
        )

        self.details_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
            height=160
        )

        self.details_frame.pack(
            fill="x",
            padx=15
        )

        self.label(
            card,
            "New due date",
            11,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(12, 6)
        )

        self.date_picker = DatePicker(card)
        self.date_picker.pack(
            fill="x",
            padx=15,
            pady=(0, 12)
        )

        self.message_label = self.label(
            card,
            "",
            10,
            RED
        )

        self.message_label.pack(
            anchor="w",
            padx=15,
            pady=(0, 8)
        )

        self.confirm_button = ctk.CTkButton(
            card,
            text="✓  Confirm renewal",
            height=38,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            state="disabled",
            command=self.confirm_renewal
        )

        self.confirm_button.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        self.render_details()

    def render_details(self):
        self.clear_frame(self.details_frame)

        item = self.selected_transaction

        if item is None:
            empty = ctk.CTkFrame(
                self.details_frame,
                fg_color="transparent",
                height=145
            )

            empty.pack(fill="x")
            empty.pack_propagate(False)

            self.label(
                empty,
                "Select a borrowed book to view renewal details",
                12,
                MUTED
            ).place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            self.confirm_button.configure(
                state="disabled"
            )
            return

        fields = [
            ("Transaction ID", item.get("id", "-")),
            ("Reader", item.get("reader_name", "-")),
            ("Book title", item.get("book_title", "-")),
            (
                "Borrowed date",
                display_date(item.get("borrowed_date"))
            ),
            (
                "Current due date",
                display_date(item.get("due_date"))
            )
        ]

        for title, value in fields:
            line = ctk.CTkFrame(
                self.details_frame,
                fg_color="transparent"
            )

            line.pack(
                fill="x",
                pady=3
            )

            self.label(
                line,
                title,
                11,
                MUTED,
                width=150,
                anchor="w"
            ).pack(side="left")

            self.label(
                line,
                str(value),
                11,
                TEXT,
                True,
                anchor="w"
            ).pack(side="left")

        self.confirm_button.configure(
            state=(
                "normal"
                if self.on_renew is not None
                else "disabled"
            )
        )

    # ======================================
    # DATA
    # ======================================

    def set_transactions(self, transactions):
        self.transactions = list(
            transactions or []
        )

        self.selected_transaction = None
        self.date_picker.clear()
        self.message_label.configure(text="")

        self.search_transactions()

    def search_transactions(self):
        keyword = (
            self.search_entry.get()
            .strip()
            .lower()
        )

        self.filtered_transactions = [
            item
            for item in self.transactions
            if (
                keyword in str(
                    item.get("reader_name", "")
                ).lower()
                or keyword in str(
                    item.get("book_title", "")
                ).lower()
                or keyword in str(
                    item.get("id", "")
                ).lower()
            )
        ]

        self.render_transactions()

    def select_transaction(self, item):
        self.selected_transaction = item
        self.date_picker.clear()
        self.message_label.configure(text="")

        self.render_transactions()
        self.render_details()

    # ======================================
    # CONFIRM
    # ======================================

    def confirm_renewal(self):
        if self.selected_transaction is None:
            return

        if self.on_renew is None:
            return

        new_date = parse_date(
            self.date_picker.get()
        )

        if new_date is None:
            self.message_label.configure(
                text="Please select a valid new due date."
            )
            return

        old_date = parse_date(
            self.selected_transaction.get("due_date")
        )

        if old_date and new_date <= old_date:
            self.message_label.configure(
                text="New due date must be after the current due date."
            )
            return

        self.message_label.configure(text="")

        # Controller handles renewal eligibility,
        # database updates and final confirmation.
        self.on_renew(
            self.selected_transaction,
            new_date
        )

    def navigate(self, page):
        if self.on_navigate is not None:
            self.on_navigate(page)

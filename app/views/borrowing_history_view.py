
from pathlib import Path
from datetime import date, datetime
from tkinter import Misc, filedialog
import calendar
import csv

import customtkinter as ctk
from PIL import Image, ImageDraw

PAGE_BG = "#F7FAF9"
SIDEBAR_BG = "#2D6857"
SIDEBAR_ITEM = "#397461"
ACTIVE_GREEN = "#70D18F"

GREEN = "#008D3F"
DARK_GREEN = "#007536"
WHITE = "#FFFFFF"

TEXT = "#2D3A40"
MUTED = "#8293A5"
BORDER = "#E5EBE9"
PALE_GREEN = "#F2FBF6"

BLUE = "#2878C8"
BLUE_BG = "#EAF3FF"
RED = "#D94B55"
RED_BG = "#FDEDEF"
GREEN_BG = "#E4F7EB"


class DatePicker(ctk.CTkFrame):
    """Date field with a clickable calendar popup."""

    def __init__(self, master):
        super().__init__(
            master,
            fg_color="transparent"
        )

        self.selected_date = None
        self.popup = None

        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self,
            height=34,
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

        self.calendar_button = ctk.CTkButton(
            self,
            text="",
            width=34,
            height=34,
            corner_radius=6,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            hover_color=PALE_GREEN,
            command=self.open_calendar
        )

        self.calendar_button.grid(
            row=0,
            column=1,
            padx=(4, 0)
        )

        self.calendar_icon = self.create_calendar_icon()

        self.calendar_button.configure(
            image=self.calendar_icon
        )

    @staticmethod
    def create_calendar_icon():
        image = Image.new(
            "RGBA",
            (64, 64),
            (0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(image)

        draw.rounded_rectangle(
            (10, 14, 54, 54),
            radius=6,
            outline=GREEN,
            width=5
        )

        draw.line(
            (10, 27, 54, 27),
            fill=GREEN,
            width=5
        )

        draw.line(
            (23, 8, 23, 20),
            fill=GREEN,
            width=5
        )

        draw.line(
            (41, 8, 41, 20),
            fill=GREEN,
            width=5
        )

        for x in (23, 39):
            for y in (37, 46):
                draw.ellipse(
                    (x - 2, y - 2, x + 2, y + 2),
                    fill=GREEN
                )

        return ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=(17, 17)
        )

    def get(self):
        return self.entry.get()

    def delete(self, start, end):
        self.entry.delete(start, end)
        self.selected_date = None

    def set_date(self, value):
        self.selected_date = value

        self.entry.delete(0, "end")
        self.entry.insert(
            0,
            value.strftime("%d/%m/%Y")
        )

    @staticmethod
    def parse_date(value):
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if not value:
            return None

        value = str(value).strip()

        for fmt in (
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S"
        ):
            try:
                return datetime.strptime(
                    value,
                    fmt
                ).date()
            except ValueError:
                continue

        return None

    def open_calendar(self):
        if (
            self.popup is not None
            and self.popup.winfo_exists()
        ):
            self.popup.lift()
            self.popup.focus_force()
            return

        current = (
            self.parse_date(self.get())
            or date.today()
        )

        year = current.year
        month = current.month

        popup = ctk.CTkToplevel(self)
        self.popup = popup

        popup.title("Select date")
        popup.geometry("330x355")
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())

        popup.update_idletasks()

        x = self.winfo_rootx()
        y = (
            self.winfo_rooty()
            + self.winfo_height()
            + 5
        )

        popup.geometry(f"+{x}+{y}")
        popup.grab_set()

        header = ctk.CTkFrame(
            popup,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=14,
            pady=(14, 8)
        )

        header.grid_columnconfigure(
            1,
            weight=1
        )

        month_label = ctk.CTkLabel(
            header,
            text="",
            text_color=TEXT,
            font=("Segoe UI", 14, "bold")
        )

        month_label.grid(
            row=0,
            column=1
        )

        days_frame = ctk.CTkFrame(
            popup,
            fg_color="transparent"
        )

        days_frame.pack(
            fill="both",
            expand=True,
            padx=14
        )

        for col in range(7):
            days_frame.grid_columnconfigure(
                col,
                weight=1
            )

        def choose_day(day):
            self.set_date(
                date(year, month, day)
            )
            popup.destroy()
            self.popup = None

        def choose_today():
            self.set_date(date.today())
            popup.destroy()
            self.popup = None

        def render_calendar():
            for child in days_frame.winfo_children():
                child.destroy()

            month_label.configure(
                text=(
                    f"{calendar.month_name[month]} "
                    f"{year}"
                )
            )

            weekday_names = [
                "Mo", "Tu", "We",
                "Th", "Fr", "Sa", "Su"
            ]

            for col, name in enumerate(
                weekday_names
            ):
                ctk.CTkLabel(
                    days_frame,
                    text=name,
                    text_color=MUTED,
                    font=("Segoe UI", 10, "bold")
                ).grid(
                    row=0,
                    column=col,
                    pady=(0, 8)
                )

            weeks = calendar.monthcalendar(
                year,
                month
            )

            selected = self.parse_date(
                self.get()
            )

            today = date.today()

            for row_index, week in enumerate(
                weeks,
                start=1
            ):
                for col_index, day in enumerate(
                    week
                ):
                    if day == 0:
                        continue

                    current_day = date(
                        year,
                        month,
                        day
                    )

                    is_selected = (
                        current_day == selected
                    )

                    is_today = (
                        current_day == today
                    )

                    ctk.CTkButton(
                        days_frame,
                        text=str(day),
                        width=35,
                        height=34,
                        corner_radius=6,
                        fg_color=(
                            GREEN
                            if is_selected
                            else "transparent"
                        ),
                        text_color=(
                            WHITE
                            if is_selected
                            else TEXT
                        ),
                        hover_color=(
                            DARK_GREEN
                            if is_selected
                            else PALE_GREEN
                        ),
                        border_width=(
                            1
                            if is_today and not is_selected
                            else 0
                        ),
                        border_color=GREEN,
                        font=("Segoe UI", 11),
                        command=lambda d=day: (
                            choose_day(d)
                        )
                    ).grid(
                        row=row_index,
                        column=col_index,
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

            render_calendar()

        ctk.CTkButton(
            header,
            text="‹",
            width=34,
            height=30,
            fg_color="transparent",
            hover_color=PALE_GREEN,
            text_color=GREEN,
            font=("Segoe UI", 22),
            command=lambda: change_month(-1)
        ).grid(
            row=0,
            column=0
        )

        ctk.CTkButton(
            header,
            text="›",
            width=34,
            height=30,
            fg_color="transparent",
            hover_color=PALE_GREEN,
            text_color=GREEN,
            font=("Segoe UI", 22),
            command=lambda: change_month(1)
        ).grid(
            row=0,
            column=2
        )

        ctk.CTkButton(
            popup,
            text="Today",
            height=30,
            fg_color=PALE_GREEN,
            hover_color="#D8F2E4",
            text_color=GREEN,
            command=choose_today
        ).pack(
            fill="x",
            padx=16,
            pady=(8, 14)
        )

        render_calendar()


# ==================================================
# BORROWING HISTORY VIEW
# ==================================================

class BorrowingHistoryView(ctk.CTkFrame):
    """Borrowing history UI based on Word design."""

    def __init__(
        self,
        master,
        on_navigate=None,
        on_export=None
    ):
        super().__init__(
            master,
            fg_color=PAGE_BG
        )

        self.on_navigate = on_navigate
        self.on_export = on_export

        self.assets = (
            Path(__file__).resolve().parents[1]
            / "assets"
        )

        self.images = []

        self.transactions = []
        self.filtered_transactions = []

        self.current_page = 1
        self.page_size = 8

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()

        self.main = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )

        self.main.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=20,
            pady=20
        )

        self.main.grid_columnconfigure(
            0,
            weight=1
        )
        self.main.grid_rowconfigure(
            2,
            weight=1
        )

        self.build_header()
        self.build_filters()
        self.build_history_table()

    # ==========================================
    # COMMON COMPONENTS
    # ==========================================

    def text(
        self,
        parent,
        value,
        size=12,
        color=TEXT,
        bold=False,
        **kwargs
    ):
        return ctk.CTkLabel(
            parent,
            text=value,
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

    @staticmethod
    def clear(parent):
        for child in parent.winfo_children():
            child.destroy()

    @staticmethod
    def format_date(value):
        if isinstance(value, (date, datetime)):
            return value.strftime("%d/%m/%Y")

        if value is None or value == "":
            return "-"

        return str(value)

    @staticmethod
    def parse_date(value):
        return DatePicker.parse_date(value)

    def load_image(self, filename, size):
        path = self.assets / filename

        if not path.is_file():
            return None

        try:
            with Image.open(path) as source:
                original = source.convert("RGBA")

            result = ctk.CTkImage(
                light_image=original,
                dark_image=original,
                size=size
            )

            self.images.append(result)
            return result

        except (OSError, ValueError):
            return None

    def load_menu_icon(
        self,
        filename,
        active=False
    ):
        path = self.assets / "icons" / filename

        if not path.is_file():
            return None

        try:
            with Image.open(path) as source:
                original = source.convert("RGBA")

            color = (
                (42, 102, 77)
                if active
                else (231, 245, 238)
            )

            tinted = Image.new(
                "RGBA",
                original.size,
                (*color, 255)
            )

            tinted.putalpha(
                original.getchannel("A")
            )

            result = ctk.CTkImage(
                light_image=tinted,
                dark_image=tinted,
                size=(15, 15)
            )

            self.images.append(result)
            return result

        except (OSError, ValueError):
            return None

    def make_avatar(self):
        image = Image.new(
            "RGBA",
            (128, 128),
            (0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(image)

        draw.ellipse(
            (0, 0, 127, 127),
            fill=ACTIVE_GREEN
        )

        avatar = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=(32, 32)
        )

        self.images.append(avatar)
        return avatar

    # ==========================================
    # SIDEBAR
    # ==========================================

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=167,
            fg_color=SIDEBAR_BG,
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
            "logo.png",
            (40, 40)
        )

        if logo is not None:
            ctk.CTkLabel(
                sidebar,
                text="",
                image=logo
            ).pack(
                pady=(20, 5)
            )

        self.text(
            sidebar,
            "Library",
            14,
            WHITE,
            True
        ).pack()

        self.text(
            sidebar,
            "Library System",
            10,
            "#C5DCD4"
        ).pack(
            pady=(2, 26)
        )

        menus = [
            ("dashboard.png", "Dashboard"),
            ("borrow.png", "Borrow Books"),
            ("booklist.png", "Return Books"),
            ("history.png", "Borrowing History"),
        ]

        for filename, title in menus:
            active = title == "Borrowing History"

            icon = self.load_menu_icon(
                filename,
                active
            )

            row = ctk.CTkFrame(
                sidebar,
                height=38,
                fg_color=(
                    ACTIVE_GREEN
                    if active
                    else SIDEBAR_ITEM
                ),
                corner_radius=6
            )

            row.pack(
                fill="x",
                padx=10,
                pady=3
            )

            row.pack_propagate(False)

            ctk.CTkButton(
                row,
                text=title,
                image=icon,
                compound="left",
                anchor="w",
                height=38,
                corner_radius=6,
                fg_color="transparent",
                hover_color=(
                    "#82DB9F"
                    if active
                    else "#477F6D"
                ),
                text_color=(
                    "#285D48"
                    if active
                    else WHITE
                ),
                font=(
                    "Segoe UI",
                    11,
                    "bold" if active else "normal"
                ),
                command=lambda page=title: (
                    self.navigate(page)
                )
            ).pack(
                fill="both",
                expand=True,
                padx=4
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

        footer.pack(
            fill="x",
            pady=(0, 20)
        )

        self.text(
            footer,
            "Librarian",
            11,
            WHITE,
            True
        ).pack()

        self.text(
            footer,
            "Library",
            10,
            "#C5DCD4"
        ).pack(
            pady=(3, 5)
        )

        avatar_image = self.make_avatar()

        avatar_frame = ctk.CTkFrame(
            footer,
            width=32,
            height=32,
            fg_color="transparent"
        )

        avatar_frame.pack()
        avatar_frame.pack_propagate(False)

        ctk.CTkLabel(
            avatar_frame,
            text="LG",
            image=avatar_image,
            compound="center",
            width=32,
            height=32,
            text_color="#326A50",
            font=("Segoe UI", 10, "bold")
        ).pack()

    # ==========================================
    # HEADER
    # ==========================================

    def build_header(self):
        header = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(10, 20)
        )

        self.text(
            header,
            "Borrowing history",
            21,
            TEXT,
            True
        ).pack(anchor="w")

        self.text(
            header,
            "View and manage book borrowing history",
            11,
            MUTED
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

    # ==========================================
    # FILTERS
    # ==========================================

    def build_filters(self):
        card = self.card(self.main)

        card.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 16)
        )

        self.text(
            card,
            "Filters",
            14,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 14)
        )

        filters = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        filters.pack(
            fill="x",
            padx=15
        )

        for column in range(5):
            filters.grid_columnconfigure(
                column,
                weight=1,
                uniform="filters"
            )

        self.reader_entry = self.filter_entry(
            filters,
            0,
            "Reader",
            "Reader name..."
        )

        self.book_entry = self.filter_entry(
            filters,
            1,
            "Book",
            "Book title..."
        )

        # ======================================
        # STATUS - FIXED DROPDOWN ARROW
        # ======================================

        status_box = ctk.CTkFrame(
            filters,
            fg_color="transparent"
        )

        status_box.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=5
        )

        self.text(
            status_box,
            "Status",
            11,
            TEXT,
            True
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        self.status_combo = ctk.CTkComboBox(
            status_box,
            height=34,
            values=[
                "All statuses",
                "Pending",
                "Approved",
                "Borrowed",
                "Rejected",
                "ReturnRequested",
                "Returned",
                "Overdue"
            ],
            state="readonly",
            fg_color=WHITE,
            border_color=BORDER,
            button_color="#F1F5F3",
            button_hover_color="#E3EFE8",
            dropdown_fg_color=WHITE,
            dropdown_hover_color=PALE_GREEN,
            text_color=TEXT,
            font=("Segoe UI", 11),
            corner_radius=6,
            border_width=1
        )

        self.status_combo.pack(fill="x")
        self.status_combo.set("All statuses")

        # ======================================
        # FROM DATE
        # ======================================

        from_box = ctk.CTkFrame(
            filters,
            fg_color="transparent"
        )

        from_box.grid(
            row=0,
            column=3,
            sticky="ew",
            padx=5
        )

        self.text(
            from_box,
            "From date",
            11,
            TEXT,
            True
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        self.from_entry = DatePicker(from_box)
        self.from_entry.pack(fill="x")

        # ======================================
        # TO DATE
        # ======================================

        to_box = ctk.CTkFrame(
            filters,
            fg_color="transparent"
        )

        to_box.grid(
            row=0,
            column=4,
            sticky="ew",
            padx=5
        )

        self.text(
            to_box,
            "To date",
            11,
            TEXT,
            True
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        self.to_entry = DatePicker(to_box)
        self.to_entry.pack(fill="x")

        # ======================================
        # BUTTONS
        # ======================================

        actions = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        actions.pack(
            fill="x",
            padx=15,
            pady=(16, 12)
        )

        ctk.CTkButton(
            actions,
            text="Apply filters",
            width=125,
            height=34,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            command=self.apply_filters
        ).pack(
            side="left",
            padx=(0, 8)
        )

        ctk.CTkButton(
            actions,
            text="Reset",
            width=90,
            height=34,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            hover_color=PAGE_BG,
            command=self.reset_filters
        ).pack(side="left")

        ctk.CTkButton(
            actions,
            text="Export data",
            width=120,
            height=34,
            fg_color=WHITE,
            border_width=1,
            border_color=GREEN,
            text_color=GREEN,
            hover_color=PALE_GREEN,
            command=self.export_data
        ).pack(side="right")

        self.filter_message = self.text(
            card,
            "",
            10,
            RED
        )

        self.filter_message.pack(
            anchor="w",
            padx=15,
            pady=(0, 8)
        )

    def filter_entry(
        self,
        parent,
        column,
        title,
        placeholder
    ):
        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=5
        )

        self.text(
            frame,
            title,
            11,
            TEXT,
            True
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        entry = ctk.CTkEntry(
            frame,
            height=34,
            placeholder_text=placeholder,
            fg_color=WHITE,
            border_color=BORDER,
            text_color=TEXT,
            font=("Segoe UI", 11)
        )

        entry.pack(fill="x")
        return entry

    # ==========================================
    # HISTORY TABLE
    # ==========================================

    def build_history_table(self):
        card = self.card(self.main)

        card.grid(
            row=2,
            column=0,
            sticky="nsew"
        )

        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        heading = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        heading.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=15,
            pady=(15, 12)
        )

        self.text(
            heading,
            "Transaction history",
            14,
            TEXT,
            True
        ).pack(side="left")

        self.total_label = self.text(
            heading,
            "0 transactions",
            10,
            MUTED
        )

        self.total_label.pack(side="right")

        self.table_container = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            corner_radius=0
        )

        self.table_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=15
        )

        pagination = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        pagination.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=15,
            pady=(12, 15)
        )

        self.previous_button = ctk.CTkButton(
            pagination,
            text="Previous",
            width=90,
            height=32,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            hover_color=PAGE_BG,
            command=self.previous_page
        )

        self.previous_button.pack(side="left")

        self.page_label = self.text(
            pagination,
            "Page 1 of 1",
            11,
            MUTED
        )

        self.page_label.pack(
            side="left",
            padx=15
        )

        self.next_button = ctk.CTkButton(
            pagination,
            text="Next",
            width=90,
            height=32,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            hover_color=PAGE_BG,
            command=self.next_page
        )

        self.next_button.pack(side="left")

        self.render_table()

    # ==========================================
    # RENDER TABLE
    # ==========================================

    def render_table(self):
        self.clear(self.table_container)

        total = len(self.filtered_transactions)

        self.total_label.configure(
            text=f"{total} transactions"
        )

        total_pages = max(
            1,
            (total + self.page_size - 1)
            // self.page_size
        )

        self.current_page = min(
            self.current_page,
            total_pages
        )

        start = (
            (self.current_page - 1)
            * self.page_size
        )

        page_items = self.filtered_transactions[
            start:start + self.page_size
        ]

        columns = (
            ("ID", 48),
            ("Reader", 90),
            ("Book title", 115),
            ("Borrowed", 95),
            ("Due date", 95),
            ("Returned", 95),
            ("Status", 100)
        )
        self.table_container.grid_columnconfigure(1, weight=1)
        self.table_container.grid_columnconfigure(2, weight=3)

        ctk.CTkFrame(
            self.table_container,
            fg_color=PALE_GREEN,
            corner_radius=6,
            height=42
        ).grid(row=0, column=0, columnspan=len(columns), sticky="nsew")

        for column, (title, width) in enumerate(columns):
            self.text(
                self.table_container,
                title,
                11,
                TEXT,
                True,
                bg_color=PALE_GREEN,
                width=width,
                anchor="w"
            ).grid(row=0, column=column, sticky="ew", padx=5, pady=7)

        if not page_items:
            empty = ctk.CTkFrame(
                self.table_container,
                fg_color="transparent",
                height=210
            )
            empty.grid(row=1, column=0, columnspan=len(columns), sticky="ew")

            self.text(
                empty,
                "No transactions found",
                13,
                MUTED
            ).place(relx=0.5, rely=0.45, anchor="center")

            self.text(
                empty,
                "Apply filters to view borrowing history",
                11,
                MUTED
            ).place(relx=0.5, rely=0.58, anchor="center")

        for row, item in enumerate(page_items, start=1):
            self.render_row(item, 2 * row - 1, len(columns))

        self.page_label.configure(
            text=(
                f"Page {self.current_page}"
                f" of {total_pages}"
            )
        )

        self.previous_button.configure(
            state=(
                "normal"
                if self.current_page > 1
                else "disabled"
            )
        )

        self.next_button.configure(
            state=(
                "normal"
                if self.current_page < total_pages
                else "disabled"
            )
        )

    def render_row(self, item, row, column_count):
        status = str(
            item.get("status", "")
        ).strip()

        values = [
            str(item.get("id", "")),
            str(item.get("reader_name", "")),
            str(item.get("book_title", "")),
            self.format_date(
                item.get("borrowed_date")
            ),
            self.format_date(
                item.get("due_date")
            ),
            self.format_date(
                item.get("returned_date")
            )
        ]

        for column, value in enumerate(values):
            wraps = column in (1, 2)
            cell = self.text(
                self.table_container,
                value,
                10,
                TEXT,
                anchor="w",
                justify="left",
                wraplength=100 if wraps else 0
            )
            cell.grid(row=row, column=column, sticky="ew", padx=5, pady=10)
            if wraps:
                Misc.bind(cell, "<Configure>", self.wrap_table_cell, add="+")

        status_colors = {
            "returned": (GREEN, GREEN_BG),
            "borrowed": (BLUE, BLUE_BG),
            "approved": (BLUE, BLUE_BG),
            "rejected": (RED, RED_BG),
            "overdue": (RED, RED_BG)
        }

        color, background = status_colors.get(
            status.lower(),
            (MUTED, PAGE_BG)
        )

        self.text(
            self.table_container,
            status or "-",
            10,
            color,
            True,
            fg_color=background,
            corner_radius=5,
            width=100,
            height=26
        ).grid(row=row, column=6, sticky="w", padx=5, pady=10)

        ctk.CTkFrame(
            self.table_container,
            height=1,
            fg_color=BORDER
        ).grid(row=row + 1, column=0, columnspan=column_count, sticky="ew")

    @staticmethod
    def wrap_table_cell(event):
        cell = event.widget
        width = event.width / ctk.ScalingTracker.get_widget_scaling(cell)
        if cell.cget("wraplength") != width:
            cell.configure(wraplength=width)

    # ==========================================
    # DATA AND FILTERING
    # ==========================================

    def set_transactions(self, transactions):
        self.transactions = list(
            transactions or []
        )

        self.filtered_transactions = list(
            self.transactions
        )

        self.current_page = 1
        self.render_table()

    def apply_filters(self):
        reader = (
            self.reader_entry.get()
            .strip()
            .lower()
        )

        book = (
            self.book_entry.get()
            .strip()
            .lower()
        )

        status = (
            self.status_combo.get()
            .strip()
            .lower()
        )

        from_text = self.from_entry.get().strip()
        to_text = self.to_entry.get().strip()

        from_date = (
            self.parse_date(from_text)
            if from_text
            else None
        )

        to_date = (
            self.parse_date(to_text)
            if to_text
            else None
        )

        if (
            (from_text and from_date is None)
            or (to_text and to_date is None)
        ):
            self.filter_message.configure(
                text="Invalid date. Use DD/MM/YYYY."
            )
            return

        if (
            from_date is not None
            and to_date is not None
            and from_date > to_date
        ):
            self.filter_message.configure(
                text="From date must be before To date."
            )
            return

        self.filter_message.configure(text="")

        results = []

        for item in self.transactions:
            item_reader = str(
                item.get("reader_name", "")
            ).lower()

            item_book = str(
                item.get("book_title", "")
            ).lower()

            item_status = str(
                item.get("status", "")
            ).lower()

            borrowed = self.parse_date(
                item.get("borrowed_date")
            )

            if reader not in item_reader:
                continue

            if book not in item_book:
                continue

            if (
                status != "all statuses"
                and status != item_status
            ):
                continue

            if from_date is not None:
                if (
                    borrowed is None
                    or borrowed < from_date
                ):
                    continue

            if to_date is not None:
                if (
                    borrowed is None
                    or borrowed > to_date
                ):
                    continue

            results.append(item)

        self.filtered_transactions = results
        self.current_page = 1

        self.render_table()

    def reset_filters(self):
        for entry in [
            self.reader_entry,
            self.book_entry,
            self.from_entry,
            self.to_entry
        ]:
            entry.delete(0, "end")

        self.status_combo.set(
            "All statuses"
        )

        self.filter_message.configure(text="")

        self.filtered_transactions = list(
            self.transactions
        )

        self.current_page = 1
        self.render_table()

    # ==========================================
    # PAGINATION
    # ==========================================

    def previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_table()

    def next_page(self):
        total_pages = max(
            1,
            (
                len(self.filtered_transactions)
                + self.page_size - 1
            ) // self.page_size
        )

        if self.current_page < total_pages:
            self.current_page += 1
            self.render_table()

    # ==========================================
    # EXPORT CSV
    # ==========================================

    def export_data(self):
        if self.on_export is not None:
            self.on_export(
                list(self.filtered_transactions)
            )
            return

        if not self.filtered_transactions:
            self.filter_message.configure(
                text="No data available to export."
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv")
            ],
            initialfile="borrowing_history.csv"
        )

        if not path:
            return

        columns = [
            ("id", "ID"),
            ("reader_name", "Reader"),
            ("book_title", "Book title"),
            ("borrowed_date", "Borrowed"),
            ("due_date", "Due date"),
            ("returned_date", "Returned"),
            ("status", "Status")
        ]

        with open(
            path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:
            writer = csv.writer(file)

            writer.writerow([
                title
                for _, title in columns
            ])

            for item in self.filtered_transactions:
                writer.writerow([
                    self.format_date(item.get(key))
                    if key in (
                        "borrowed_date",
                        "due_date",
                        "returned_date"
                    )
                    else item.get(key, "")
                    for key, _ in columns
                ])

    # ==========================================
    # NAVIGATION
    # ==========================================

    def navigate(self, page_name):
        if self.on_navigate is not None:
            self.on_navigate(page_name)

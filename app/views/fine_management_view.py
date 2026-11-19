
from pathlib import Path
from datetime import date, datetime
from tkinter import filedialog
import csv

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
RED_BG = "#FDEDEF"
BLUE = "#2878C8"
BLUE_BG = "#EAF3FF"
GREEN_BG = "#E4F7EB"


def format_date(value):
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")

    if not value:
        return "-"

    text = str(value)

    try:
        return datetime.strptime(
            text[:10], "%Y-%m-%d"
        ).strftime("%d/%m/%Y")
    except ValueError:
        return text


def format_money(value):
    try:
        amount = float(value)
        return f"{amount:,.0f} VND"
    except (TypeError, ValueError):
        return "-"


# ==========================================
# FINE MANAGEMENT VIEW
# ==========================================

class FineManagementView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_navigate=None,
        on_pay=None
    ):
        super().__init__(master, fg_color=BG)

        self.on_navigate = on_navigate
        self.on_pay = on_pay

        self.assets = (
            Path(__file__).resolve().parents[1]
            / "assets"
        )
        self.images = []

        self.fines = []
        self.filtered_fines = []
        self.selected_fine = None

        self.page = 1
        self.page_size = 8

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
        self.build_summary()
        self.build_filters()
        self.build_table()
        self.build_details()

    # ======================================
    # COMMON COMPONENTS
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
                colored.putalpha(image.getchannel("A"))
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

    @staticmethod
    def clear_frame(frame):
        for widget in frame.winfo_children():
            widget.destroy()

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
            icon = self.load_image(
                self.assets / "icons" / filename,
                (16, 16),
                (231, 245, 238)
            )

            ctk.CTkButton(
                sidebar,
                text=name,
                image=icon,
                compound="left",
                anchor="w",
                height=38,
                corner_radius=6,
                fg_color=MENU_BG,
                hover_color="#477F6D",
                text_color=WHITE,
                font=("Segoe UI", 11),
                command=lambda page=name: self.navigate(page)
            ).pack(
                fill="x",
                padx=10,
                pady=3
            )

        ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        ).pack(fill="both", expand=True)

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
            "Fine management",
            22,
            TEXT,
            True
        ).pack(anchor="w")

        self.label(
            header,
            "View and manage library fines and payments",
            11,
            MUTED
        ).pack(anchor="w", pady=(3, 0))

    # ======================================
    # SUMMARY
    # ======================================

    def build_summary(self):
        frame = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )
        frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 16)
        )

        for col in range(3):
            frame.grid_columnconfigure(
                col,
                weight=1,
                uniform="summary"
            )

        self.total_value = self.summary_card(
            frame, 0, "Total fines", "0"
        )
        self.unpaid_value = self.summary_card(
            frame, 1, "Unpaid fines", "0"
        )
        self.amount_value = self.summary_card(
            frame, 2, "Outstanding amount", "0 VND"
        )

    def summary_card(self, parent, column, title, value):
        card = self.card(parent)
        card.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=5
        )

        self.label(
            card,
            title,
            11,
            MUTED
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 7)
        )

        value_label = self.label(
            card,
            value,
            21,
            TEXT,
            True
        )
        value_label.pack(
            anchor="w",
            padx=15,
            pady=(0, 15)
        )
        return value_label

    def update_summary(self):
        total = len(self.fines)

        unpaid = [
            item for item in self.fines
            if str(
                item.get("status", "")
            ).strip().lower() == "unpaid"
        ]

        amount = 0

        for item in unpaid:
            try:
                amount += float(
                    item.get("amount", 0)
                )
            except (TypeError, ValueError):
                pass

        self.total_value.configure(
            text=str(total)
        )
        self.unpaid_value.configure(
            text=str(len(unpaid))
        )
        self.amount_value.configure(
            text=format_money(amount)
        )

    # ======================================
    # FILTERS
    # ======================================

    def build_filters(self):
        card = self.card(self.main)
        card.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 16)
        )

        self.label(
            card,
            "Search and filters",
            14,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 12)
        )

        row = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        row.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        self.search_entry = ctk.CTkEntry(
            row,
            height=36,
            placeholder_text=(
                "Search reader, book or fine ID..."
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
            lambda event: self.apply_filters()
        )

        self.status_combo = ctk.CTkOptionMenu(
            row,
            width=160,
            height=36,
            values=[
                "All statuses",
                "Unpaid",
                "Paid"
            ],
            fg_color=WHITE,
            button_color="#EAF3EE",
            button_hover_color="#DCECE3",
            text_color=TEXT,
            dropdown_fg_color=WHITE,
            dropdown_hover_color=LIGHT,
            dropdown_text_color=TEXT,
            font=("Segoe UI", 11),
            anchor="w",
            dynamic_resizing=False
        )
        self.status_combo.set("All statuses")
        self.status_combo.pack(
            side="left",
            padx=(0, 10)
        )

        ctk.CTkButton(
            row,
            text="Search",
            width=95,
            height=36,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            command=self.apply_filters
        ).pack(
            side="left",
            padx=(0, 8)
        )

        ctk.CTkButton(
            row,
            text="Reset",
            width=75,
            height=36,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            hover_color=BG,
            command=self.reset_filters
        ).pack(side="left")

    # ======================================
    # FINE TABLE
    # ======================================

    def build_table(self):
        card = self.card(self.main)
        card.grid(
            row=3,
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
            pady=(15, 12)
        )

        self.label(
            top,
            "Fine list",
            14,
            TEXT,
            True
        ).pack(side="left")

        self.count_label = self.label(
            top,
            "0 fines",
            10,
            MUTED
        )
        self.count_label.pack(side="right")

        self.table_frame = ctk.CTkScrollableFrame(
            card,
            height=290,
            fg_color="transparent",
            orientation="horizontal"
        )
        self.table_frame.pack(
            fill="x",
            padx=15
        )

        bottom = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        bottom.pack(
            fill="x",
            padx=15,
            pady=(12, 15)
        )

        self.prev_button = ctk.CTkButton(
            bottom,
            text="Previous",
            width=90,
            height=32,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            hover_color=BG,
            command=self.previous_page
        )
        self.prev_button.pack(side="left")

        self.page_label = self.label(
            bottom,
            "Page 1 of 1",
            11,
            MUTED
        )
        self.page_label.pack(
            side="left",
            padx=15
        )

        self.next_button = ctk.CTkButton(
            bottom,
            text="Next",
            width=90,
            height=32,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            hover_color=BG,
            command=self.next_page
        )
        self.next_button.pack(side="left")

        self.render_table()

    def render_table(self):
        self.clear_frame(self.table_frame)

        total = len(self.filtered_fines)
        pages = max(
            1,
            (total + self.page_size - 1)
            // self.page_size
        )

        self.page = min(self.page, pages)

        self.count_label.configure(
            text=f"{total} fines"
        )
        self.page_label.configure(
            text=f"Page {self.page} of {pages}"
        )

        self.prev_button.configure(
            state=(
                "normal"
                if self.page > 1
                else "disabled"
            )
        )
        self.next_button.configure(
            state=(
                "normal"
                if self.page < pages
                else "disabled"
            )
        )

        columns = [
            ("Fine ID", 90),
            ("Reader", 150),
            ("Book title", 220),
            ("Reason", 150),
            ("Amount", 130),
            ("Created", 110),
            ("Status", 100),
            ("Action", 90)
        ]

        header = ctk.CTkFrame(
            self.table_frame,
            fg_color=LIGHT,
            corner_radius=6,
            height=42
        )
        header.pack(anchor="w")
        header.pack_propagate(False)

        for title, width in columns:
            self.label(
                header,
                title,
                11,
                TEXT,
                True,
                width=width,
                anchor="w"
            ).pack(
                side="left",
                padx=5
            )

        start = (
            (self.page - 1)
            * self.page_size
        )

        items = self.filtered_fines[
            start:start + self.page_size
        ]

        if not items:
            empty = ctk.CTkFrame(
                self.table_frame,
                fg_color="transparent",
                width=950,
                height=180
            )
            empty.pack(anchor="w")
            empty.pack_propagate(False)

            self.label(
                empty,
                "No fines found",
                13,
                MUTED
            ).place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )
            return

        for item in items:
            row = ctk.CTkFrame(
                self.table_frame,
                fg_color=WHITE,
                height=48
            )
            row.pack(anchor="w")
            row.pack_propagate(False)

            values = [
                str(item.get("id", "-")),
                str(item.get("reader_name", "-")),
                str(item.get("book_title", "-")),
                str(item.get("reason", "-")),
                format_money(item.get("amount")),
                format_date(item.get("created_date"))
            ]

            widths = [
                90, 150, 220, 150, 130, 110
            ]

            for value, width in zip(values, widths):
                self.label(
                    row,
                    value,
                    10,
                    TEXT,
                    width=width,
                    anchor="w"
                ).pack(
                    side="left",
                    padx=5
                )

            status = str(
                item.get("status", "")
            )

            is_paid = status.lower() == "paid"

            self.label(
                row,
                status or "-",
                10,
                GREEN if is_paid else RED,
                True,
                width=90,
                height=26,
                fg_color=(
                    GREEN_BG if is_paid else RED_BG
                ),
                corner_radius=5
            ).pack(
                side="left",
                padx=5
            )

            ctk.CTkButton(
                row,
                text="View",
                width=80,
                height=28,
                fg_color=WHITE,
                border_width=1,
                border_color=GREEN,
                text_color=GREEN,
                hover_color=LIGHT,
                command=lambda fine=item: self.select_fine(fine)
            ).pack(
                side="left",
                padx=10
            )

            ctk.CTkFrame(
                self.table_frame,
                height=1,
                fg_color=BORDER
            ).pack(fill="x")

    # ======================================
    # FINE DETAILS
    # ======================================

    def build_details(self):
        card = self.card(self.main)
        card.grid(
            row=4,
            column=0,
            sticky="ew"
        )

        self.label(
            card,
            "Fine details",
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
            fg_color="transparent"
        )
        self.details_frame.pack(
            fill="x",
            padx=15
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
            pady=(8, 5)
        )

        self.pay_button = ctk.CTkButton(
            card,
            text="Confirm payment",
            height=38,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            state="disabled",
            command=self.confirm_payment
        )
        self.pay_button.pack(
            fill="x",
            padx=15,
            pady=(5, 15)
        )

        self.render_details()

    def render_details(self):
        self.clear_frame(self.details_frame)

        fine = self.selected_fine

        if fine is None:
            empty = ctk.CTkFrame(
                self.details_frame,
                fg_color="transparent",
                height=120
            )
            empty.pack(fill="x")
            empty.pack_propagate(False)

            self.label(
                empty,
                "Select a fine to view details",
                12,
                MUTED
            ).place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            self.pay_button.configure(
                state="disabled"
            )
            return

        fields = [
            ("Fine ID", fine.get("id", "-")),
            ("Reader", fine.get("reader_name", "-")),
            ("Book title", fine.get("book_title", "-")),
            ("Reason", fine.get("reason", "-")),
            ("Amount", format_money(fine.get("amount"))),
            ("Created date", format_date(fine.get("created_date"))),
            ("Status", fine.get("status", "-"))
        ]

        for title, value in fields:
            row = ctk.CTkFrame(
                self.details_frame,
                fg_color="transparent"
            )
            row.pack(
                fill="x",
                pady=3
            )

            self.label(
                row,
                title,
                11,
                MUTED,
                width=150,
                anchor="w"
            ).pack(side="left")

            self.label(
                row,
                str(value),
                11,
                TEXT,
                True,
                anchor="w"
            ).pack(side="left")

        unpaid = str(
            fine.get("status", "")
        ).strip().lower() == "unpaid"

        self.pay_button.configure(
            state=(
                "normal"
                if unpaid and self.on_pay is not None
                else "disabled"
            )
        )

    # ======================================
    # DATA AND ACTIONS
    # ======================================

    def set_fines(self, fines):
        self.fines = list(fines or [])
        self.filtered_fines = list(self.fines)
        self.selected_fine = None
        self.page = 1

        self.update_summary()
        self.render_table()
        self.render_details()

    def apply_filters(self):
        keyword = (
            self.search_entry.get()
            .strip()
            .lower()
        )
        status = (
            self.status_combo.get()
            .strip()
            .lower()
        )

        results = []

        for item in self.fines:
            search_text = " ".join([
                str(item.get("id", "")),
                str(item.get("reader_name", "")),
                str(item.get("book_title", ""))
            ]).lower()

            if keyword not in search_text:
                continue

            if (
                status != "all statuses"
                and status != str(
                    item.get("status", "")
                ).strip().lower()
            ):
                continue

            results.append(item)

        self.filtered_fines = results
        self.page = 1
        self.render_table()

    def reset_filters(self):
        self.search_entry.delete(0, "end")
        self.status_combo.set("All statuses")

        self.filtered_fines = list(self.fines)
        self.page = 1
        self.render_table()

    def select_fine(self, fine):
        self.selected_fine = fine
        self.message_label.configure(text="")
        self.render_details()

    def confirm_payment(self):
        if self.selected_fine is None:
            return

        if self.on_pay is None:
            return

        if str(
            self.selected_fine.get("status", "")
        ).strip().lower() != "unpaid":
            return

        # Payment processing is handled by the controller.
        self.on_pay(self.selected_fine)

    def previous_page(self):
        if self.page > 1:
            self.page -= 1
            self.render_table()

    def next_page(self):
        pages = max(
            1,
            (len(self.filtered_fines) + self.page_size - 1)
            // self.page_size
        )
        if self.page < pages:
            self.page += 1
            self.render_table()

    def navigate(self, page):
        if self.on_navigate is not None:
            self.on_navigate(page)

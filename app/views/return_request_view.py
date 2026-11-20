
from pathlib import Path
from datetime import date, datetime

import customtkinter as ctk
from PIL import Image

from app.config.theme import BG_GREEN, WHITE


BG = "#F5F7F8"
TEXT = "#20312C"
MUTED = "#788A84"
BORDER = "#E1E9E5"
GREEN = "#008B45"
DARK_GREEN = "#006F38"
LIGHT_GREEN = "#78D69B"
PALE_GREEN = "#F1FAF5"
RED = "#D83B48"


class ReturnRequestView(ctk.CTkFrame):

    def __init__(
        self,
        master,
        on_navigate=None,
        on_return_selected=None,
        on_return_all=None,
        on_refresh=None
    ):
        super().__init__(master, fg_color=BG)

        self.on_navigate = on_navigate
        self.on_return_selected = on_return_selected
        self.on_return_all = on_return_all
        self.on_refresh = on_refresh

        self.assets = (
            Path(__file__).resolve().parents[1] / "assets"
        )
        self.images = []

        self.transactions = []
        self.filtered_transactions = []
        self.selected_ids = set()
        self.checkboxes = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()

        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            corner_radius=0
        )
        self.content.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.build_header()
        self.build_search_panel()
        self.build_transactions_panel()

    # ==========================================
    # COMMON
    # ==========================================

    def label(
        self,
        parent,
        text,
        size=13,
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

    def panel(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color=WHITE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )

    @staticmethod
    def clear(frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def load_icon(self, name, active=False):
        path = (
            self.assets / "icons" / f"{name}.png"
        )

        if not path.exists():
            return None

        with Image.open(path) as source:
            original = source.convert("RGBA")

        color = (
            (37, 92, 73)
            if active
            else (255, 255, 255)
        )

        tinted = Image.new(
            "RGBA",
            original.size,
            (*color, 255)
        )
        tinted.putalpha(
            original.getchannel("A")
        )

        icon = ctk.CTkImage(
            light_image=tinted,
            dark_image=tinted,
            size=(19, 19)
        )

        self.images.append(icon)
        return icon

    @staticmethod
    def transaction_key(transaction):
        value = transaction.get("id")

        if value is None:
            value = transaction.get("transaction_id")

        return str(value) if value is not None else ""

    @staticmethod
    def format_date(value):
        if isinstance(value, (date, datetime)):
            return value.strftime("%d/%m/%Y")

        if value is None:
            return ""

        return str(value)

    @staticmethod
    def format_money(amount):
        return (
            f"{int(amount):,}".replace(",", ".")
            + " VND"
        )

    # ==========================================
    # SIDEBAR
    # ==========================================

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=235,
            fg_color=BG_GREEN,
            corner_radius=0
        )
        sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )
        sidebar.grid_propagate(False)

        # Logo
        logo_path = self.assets / "logo.png"

        if logo_path.exists():
            with Image.open(logo_path) as source:
                logo = source.convert("RGBA")

            logo_image = ctk.CTkImage(
                light_image=logo,
                dark_image=logo,
                size=(65, 65)
            )

            self.images.append(logo_image)

            ctk.CTkLabel(
                sidebar,
                text="",
                image=logo_image
            ).pack(pady=(24, 6))

        self.label(
            sidebar,
            "Library",
            17,
            WHITE,
            True
        ).pack()

        self.label(
            sidebar,
            "Library System",
            11,
            "#C6DCD3"
        ).pack(pady=(2, 36))

        menus = [
            ("dashboard", "Dashboard"),
            ("borrow", "Borrow Books"),
            ("booklist", "Return Books"),
            ("history", "Borrowing History"),
        ]

        for icon_name, title in menus:
            active = title == "Return Books"

            ctk.CTkButton(
                sidebar,
                text=title,
                image=self.load_icon(
                    icon_name,
                    active
                ),
                compound="left",
                anchor="w",
                height=43,
                corner_radius=7,
                fg_color=(
                    LIGHT_GREEN
                    if active
                    else "#3D7361"
                ),
                hover_color=(
                    "#8EE1AB"
                    if active
                    else "#4A806D"
                ),
                text_color=(
                    "#245A46"
                    if active
                    else WHITE
                ),
                font=(
                    "Segoe UI",
                    13,
                    "bold" if active else "normal"
                ),
                command=lambda page=title: (
                    self.navigate(page)
                )
            ).pack(
                fill="x",
                padx=14,
                pady=4
            )

        # Push footer to bottom
        ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        ).pack(
            fill="both",
            expand=True
        )

        # ======================================
        # LIBRARIAN FOOTER - ORIGINAL LG
        # ======================================

        footer = ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        )
        footer.pack(
            fill="x",
            padx=18,
            pady=(0, 22)
        )

        avatar = ctk.CTkLabel(
            footer,
            text="LG",
            width=44,
            height=44,
            corner_radius=22,
            fg_color=LIGHT_GREEN,
            text_color="#245A46",
            font=("Segoe UI", 13, "bold")
        )
        avatar.pack(side="left")

        user_info = ctk.CTkFrame(
            footer,
            fg_color="transparent"
        )
        user_info.pack(
            side="left",
            padx=(12, 0),
            fill="x",
            expand=True
        )

        ctk.CTkLabel(
            user_info,
            text="Librarian",
            font=("Segoe UI", 13, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            user_info,
            text="Library",
            font=("Segoe UI", 11),
            text_color="#C6DCD3",
            anchor="w"
        ).pack(
            fill="x",
            pady=(2, 0)
        )

    # ==========================================
    # HEADER
    # ==========================================

    def build_header(self):
        header = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        header.pack(
            fill="x",
            padx=25,
            pady=(24, 20)
        )

        if self.on_refresh is not None:
            ctk.CTkButton(header, text="Refresh", width=100, command=self.on_refresh).pack(side="right")

        self.label(
            header,
            "Return books",
            26,
            TEXT,
            True
        ).pack(anchor="w")

        self.label(
            header,
            "Select a loan approved by the library to request a return.",
            13,
            MUTED
        ).pack(
            anchor="w",
            pady=(4, 0)
        )

        self.loan_status_label = self.label(header, "", 12, MUTED)
        self.loan_status_label.pack(anchor="w", pady=(4, 0))

    def set_pending_counts(self, borrowing, returning):
        self.loan_status_label.configure(
            text=f"Awaiting borrow approval: {borrowing}  |  Awaiting return confirmation: {returning}"
        )

    # ==========================================
    # SEARCH TRANSACTIONS
    # ==========================================

    def build_search_panel(self):
        card = self.panel(self.content)
        card.pack(
            fill="x",
            padx=25,
            pady=(0, 18)
        )

        self.label(
            card,
            "Search transactions",
            16,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 4)
        )

        self.label(
            card,
            "Search by reader name, book title or book code",
            12,
            MUTED
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 14)
        )

        search_row = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        search_row.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        self.search_entry = ctk.CTkEntry(
            search_row,
            height=40,
            placeholder_text=(
                "Enter reader name, book title or code..."
            ),
            fg_color=WHITE,
            border_color=BORDER,
            text_color=TEXT
        )
        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )

        ctk.CTkButton(
            search_row,
            text="Search",
            width=110,
            height=40,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            command=self.search_transactions
        ).pack(side="right")

        self.search_entry.bind(
            "<Return>",
            lambda event: self.search_transactions()
        )

    # ==========================================
    # BORROWED BOOKS PANEL
    # ==========================================

    def build_transactions_panel(self):
        card = self.panel(self.content)
        card.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 25)
        )

        top = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        top.pack(
            fill="x",
            padx=18,
            pady=(18, 14)
        )

        title_area = ctk.CTkFrame(
            top,
            fg_color="transparent"
        )
        title_area.pack(side="left")

        self.label(
            title_area,
            "Borrowed books",
            16,
            TEXT,
            True
        ).pack(anchor="w")

        self.count_label = self.label(
            title_area,
            "0 transactions | 0 selected",
            12,
            MUTED
        )
        self.count_label.pack(
            anchor="w",
            pady=(4, 0)
        )

        actions = ctk.CTkFrame(
            top,
            fg_color="transparent"
        )
        actions.pack(side="right")

        self.return_selected_button = ctk.CTkButton(
            actions,
            text="Return selected (0)",
            width=165,
            height=39,
            fg_color=WHITE,
            text_color=GREEN,
            border_width=1,
            border_color=GREEN,
            hover_color=PALE_GREEN,
            state="disabled",
            command=self.return_selected
        )
        self.return_selected_button.pack(
            side="left",
            padx=(0, 10)
        )

        self.return_all_button = ctk.CTkButton(
            actions,
            text="Return all",
            width=115,
            height=39,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            state="disabled",
            command=self.return_all
        )
        self.return_all_button.pack(side="left")

        self.transactions_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
            height=270
        )
        self.transactions_frame.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 14)
        )

        self.summary_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        self.summary_frame.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        self.render_transactions()

    # ==========================================
    # RENDER TRANSACTIONS
    # ==========================================

    def render_transactions(self):
        self.clear(self.transactions_frame)
        self.checkboxes = {}

        if not self.filtered_transactions:
            empty = ctk.CTkFrame(
                self.transactions_frame,
                fg_color="transparent",
                height=270
            )
            empty.pack(
                fill="both",
                expand=True
            )
            empty.pack_propagate(False)

            self.label(
                empty,
                "▣",
                38,
                "#B5C5BE"
            ).place(
                relx=0.5,
                rely=0.34,
                anchor="center"
            )

            self.label(
                empty,
                "No loans available to return",
                15,
                MUTED
            ).place(
                relx=0.5,
                rely=0.53,
                anchor="center"
            )

            self.label(
                empty,
                ("No borrowed books match your search." if self.transactions
                 else "Check Borrow Status for requests awaiting approval."),
                12,
                MUTED
            ).place(
                relx=0.5,
                rely=0.64,
                anchor="center"
            )

            self.update_selection_ui()
            return

        for transaction in self.filtered_transactions:
            key = self.transaction_key(transaction)
            selected = key in self.selected_ids

            row = ctk.CTkFrame(
                self.transactions_frame,
                fg_color=PALE_GREEN,
                corner_radius=8,
                border_width=1,
                border_color=(
                    GREEN
                    if selected
                    else "#D5EEDF"
                )
            )
            row.pack(
                fill="x",
                pady=(0, 10)
            )

            checkbox = ctk.CTkCheckBox(
                row,
                text="",
                width=25,
                checkbox_width=21,
                checkbox_height=21,
                fg_color=GREEN,
                hover_color=DARK_GREEN,
                border_color="#A9C8B7",
                command=lambda k=key: (
                    self.toggle_selection(k)
                )
            )
            checkbox.pack(
                side="left",
                padx=(15, 6)
            )

            if selected:
                checkbox.select()

            self.checkboxes[key] = checkbox

            info = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )
            info.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 12),
                pady=12
            )

            self.label(
                info,
                str(transaction.get("book_title", "")),
                14,
                TEXT,
                True
            ).pack(anchor="w")

            reader = transaction.get(
                "reader_name", ""
            )
            code = transaction.get(
                "book_code", ""
            )

            self.label(
                info,
                f"Reader: {reader} | Code: {code}",
                12,
                MUTED
            ).pack(
                anchor="w",
                pady=(4, 0)
            )

            borrowed = self.format_date(
                transaction.get("borrowed_date")
            )
            due = self.format_date(
                transaction.get("due_date")
            )

            self.label(
                info,
                (
                    f"Borrowed: {borrowed}"
                    f"  |  Due date: {due}"
                ),
                11,
                MUTED
            ).pack(
                anchor="w",
                pady=(4, 0)
            )

        self.update_selection_ui()

    # ==========================================
    # SELECTION AND SUMMARY
    # ==========================================

    def toggle_selection(self, key):
        if key in self.selected_ids:
            self.selected_ids.remove(key)
        else:
            self.selected_ids.add(key)

        self.render_transactions()

    def update_selection_ui(self):
        total = len(self.filtered_transactions)
        selected = len(self.selected_ids)

        self.count_label.configure(
            text=(
                f"{total} transactions"
                f" | {selected} selected"
            )
        )

        self.return_selected_button.configure(
            text=f"Return selected ({selected})",
            state=(
                "normal"
                if (
                    selected > 0
                    and self.on_return_selected
                )
                else "disabled"
            )
        )

        self.return_all_button.configure(
            state=(
                "normal"
                if (
                    total > 0
                    and self.on_return_all
                )
                else "disabled"
            )
        )

        self.render_summary()

    def render_summary(self):
        self.clear(self.summary_frame)

        if not self.selected_ids:
            return

        selected_transactions = [
            transaction
            for transaction in self.filtered_transactions
            if (
                self.transaction_key(transaction)
                in self.selected_ids
            )
        ]

        known_fines = [
            transaction.get("fine_amount")
            for transaction in selected_transactions
        ]

        fine_available = all(
            amount is not None
            for amount in known_fines
        )

        summary = ctk.CTkFrame(
            self.summary_frame,
            fg_color=PALE_GREEN,
            border_width=1,
            border_color="#D5EEDF",
            corner_radius=8
        )
        summary.pack(fill="x")

        self.label(
            summary,
            "Summary",
            14,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(12, 4)
        )

        if fine_available:
            total_fine = sum(
                float(amount)
                for amount in known_fines
            )
            fine_text = self.format_money(
                total_fine
            )
        else:
            fine_text = "Not calculated"

        self.label(
            summary,
            (
                f"Requests: {len(selected_transactions)}"
                f"  |  Total fine: {fine_text}"
            ),
            12,
            MUTED
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 12)
        )

    # ==========================================
    # SEARCH AND DATA
    # ==========================================

    def set_transactions(self, transactions):
        """Receive real borrowing transactions."""
        self.transactions = list(
            transactions or []
        )
        self.filtered_transactions = list(
            self.transactions
        )

        self.selected_ids.clear()
        self.render_transactions()

    def search_transactions(self):
        keyword = (
            self.search_entry.get().strip().lower()
        )

        self.filtered_transactions = [
            transaction
            for transaction in self.transactions
            if keyword in (
                str(
                    transaction.get("reader_name", "")
                ) + " " +
                str(
                    transaction.get("book_title", "")
                ) + " " +
                str(
                    transaction.get("book_code", "")
                )
            ).lower()
        ]

        self.selected_ids.clear()
        self.render_transactions()

    def return_selected(self):
        if (
            not self.selected_ids
            or self.on_return_selected is None
        ):
            return

        selected = [
            transaction
            for transaction in self.filtered_transactions
            if (
                self.transaction_key(transaction)
                in self.selected_ids
            )
        ]

        if selected:
            self.on_return_selected(selected)

    def return_all(self):
        if (
            not self.filtered_transactions
            or self.on_return_all is None
        ):
            return

        self.on_return_all(
            list(self.filtered_transactions)
        )

    def navigate(self, page_name):
        if self.on_navigate:
            self.on_navigate(page_name)

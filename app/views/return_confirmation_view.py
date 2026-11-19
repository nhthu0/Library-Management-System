
from pathlib import Path
from datetime import date, datetime

import customtkinter as ctk
from PIL import Image, ImageDraw


# ==========================================
# COLORS
# ==========================================

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


class ReturnConfirmationView(ctk.CTkFrame):
    """
    Return books interface.

    UI only:
    - No database connection
    - No fake transactions
    - No automatic return processing
    """

    def __init__(
        self,
        master,
        on_navigate=None,
        on_return_selected=None,
        on_return_all=None
    ):
        super().__init__(
            master,
            fg_color=PAGE_BG
        )

        self.on_navigate = on_navigate
        self.on_return_selected = on_return_selected
        self.on_return_all = on_return_all

        self.assets = (
            Path(__file__).resolve().parents[1]
            / "assets"
        )

        self.images = []

        self.transactions = []
        self.filtered_transactions = []
        self.selected_ids = set()
        self.check_vars = {}

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

        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        self.build_header()
        self.build_search_panel()
        self.build_borrowed_panel()

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
        for widget in parent.winfo_children():
            widget.destroy()

    @staticmethod
    def format_date(value):
        if isinstance(value, (date, datetime)):
            return value.strftime("%d/%m/%Y")

        if value is None:
            return "-"

        return str(value)

    @staticmethod
    def format_money(value):
        return (
            f"{float(value):,.0f}".replace(",", ".")
            + " VND"
        )

    @staticmethod
    def transaction_key(transaction):
        value = transaction.get("id")

        if value is None:
            value = transaction.get("transaction_id")

        return str(value) if value is not None else ""

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

    def load_menu_icon(self, filename, active=False):
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

            icon = ctk.CTkImage(
                light_image=tinted,
                dark_image=tinted,
                size=(15, 15)
            )

            self.images.append(icon)
            return icon

        except (OSError, ValueError):
            return None

    def make_circle_image(self):
        scale = 4
        diameter = 32

        image = Image.new(
            "RGBA",
            (diameter * scale, diameter * scale),
            (0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(image)

        draw.ellipse(
            (
                0,
                0,
                diameter * scale - 1,
                diameter * scale - 1
            ),
            fill=ACTIVE_GREEN
        )

        result = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=(diameter, diameter)
        )

        self.images.append(result)
        return result

    # ==========================================
    # SIDEBAR - FIXED
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

        # Logo
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
        else:
            self.text(
                sidebar,
                "Library",
                15,
                WHITE,
                True
            ).pack(
                pady=(30, 8)
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

        # Real PNG icons
        menus = [
            ("dashboard.png", "Home"),
            ("borrow.png", "Borrow books"),
            ("booklist.png", "Return books"),
            ("history.png", "History"),
            ("management.png", "Manage books"),
            ("statistics.png", "Statistics")
        ]

        for filename, title in menus:
            active = title == "Return books"

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

            # ONLY ONE LABEL PER MENU
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

        # Push footer to bottom
        ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        ).pack(
            fill="both",
            expand=True
        )

        # Librarian / Library / LG
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

        avatar = ctk.CTkFrame(
            footer,
            width=32,
            height=32,
            fg_color="transparent"
        )

        avatar.pack()
        avatar.pack_propagate(False)

        circle = self.make_circle_image()

        ctk.CTkLabel(
            avatar,
            text="LG",
            image=circle,
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
            "Return books",
            21,
            TEXT,
            True
        ).pack(anchor="w")

        self.text(
            header,
            "Manage book return transactions",
            11,
            MUTED
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

    # ==========================================
    # SEARCH TRANSACTIONS
    # ==========================================

    def build_search_panel(self):
        card = self.card(self.main)

        card.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 16)
        )

        self.text(
            card,
            "Search transactions",
            14,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 4)
        )

        self.text(
            card,
            "Search by reader name, book title or book code",
            10,
            MUTED
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 12)
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
            height=34,
            placeholder_text=(
                "Enter reader name, book title or book code..."
            ),
            fg_color=WHITE,
            border_color=BORDER,
            text_color=TEXT,
            font=("Segoe UI", 11)
        )

        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        ctk.CTkButton(
            search_row,
            text="Search",
            width=95,
            height=34,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            command=self.search_transactions
        ).pack(
            side="right",
            padx=(8, 0)
        )

        self.search_entry.bind(
            "<Return>",
            lambda event: self.search_transactions()
        )

    # ==========================================
    # BORROWED BOOKS PANEL
    # ==========================================

    def build_borrowed_panel(self):
        card = self.card(self.main)

        card.grid(
            row=2,
            column=0,
            sticky="nsew"
        )

        heading = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        heading.pack(
            fill="x",
            padx=15,
            pady=(15, 12)
        )

        heading.grid_columnconfigure(
            0,
            weight=1
        )

        title_area = ctk.CTkFrame(
            heading,
            fg_color="transparent"
        )

        title_area.grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.text(
            title_area,
            "Borrowed books",
            14,
            TEXT,
            True
        ).pack(anchor="w")

        self.count_label = self.text(
            title_area,
            "0 transactions | 0 selected",
            10,
            MUTED
        )

        self.count_label.pack(
            anchor="w",
            pady=(4, 0)
        )

        actions = ctk.CTkFrame(
            heading,
            fg_color="transparent"
        )

        actions.grid(
            row=0,
            column=1,
            sticky="e"
        )

        self.selected_button = ctk.CTkButton(
            actions,
            text="Return selected (0)",
            width=150,
            height=34,
            fg_color=WHITE,
            border_width=1,
            border_color=GREEN,
            text_color=GREEN,
            hover_color=PALE_GREEN,
            state="disabled",
            command=self.return_selected
        )

        self.selected_button.pack(
            side="left",
            padx=(0, 8)
        )

        self.all_button = ctk.CTkButton(
            actions,
            text="Return all",
            width=105,
            height=34,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            state="disabled",
            command=self.return_all
        )

        self.all_button.pack(side="left")

        self.list_frame = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            corner_radius=0
        )

        self.list_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 10)
        )

        self.summary_container = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        self.summary_container.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        self.render_transactions()

    # ==========================================
    # DATA
    # ==========================================

    def set_transactions(self, transactions):
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
            self.search_entry.get()
            .strip()
            .lower()
        )

        self.filtered_transactions = [
            item
            for item in self.transactions
            if keyword in (
                str(item.get("reader_name", ""))
                + " "
                + str(item.get("book_title", ""))
                + " "
                + str(item.get("book_code", ""))
            ).lower()
        ]

        self.selected_ids.clear()
        self.render_transactions()

    # ==========================================
    # TRANSACTION LIST
    # ==========================================

    def render_transactions(self):
        self.clear(self.list_frame)
        self.check_vars = {}

        if not self.filtered_transactions:
            empty = ctk.CTkFrame(
                self.list_frame,
                fg_color="transparent",
                height=250
            )

            empty.pack(
                fill="both",
                expand=True
            )

            empty.pack_propagate(False)

            self.text(
                empty,
                "No transactions found",
                13,
                MUTED
            ).place(
                relx=0.5,
                rely=0.45,
                anchor="center"
            )

            self.text(
                empty,
                "Search to display borrowed books",
                11,
                MUTED
            ).place(
                relx=0.5,
                rely=0.56,
                anchor="center"
            )

            self.update_selection()
            return

        for item in self.filtered_transactions:
            key = self.transaction_key(item)

            row = ctk.CTkFrame(
                self.list_frame,
                fg_color=PALE_GREEN,
                corner_radius=7,
                border_width=1,
                border_color="#D8F2E4"
            )

            row.pack(
                fill="x",
                pady=(0, 9)
            )

            checked = ctk.BooleanVar(
                value=key in self.selected_ids
            )

            self.check_vars[key] = checked

            checkbox = ctk.CTkCheckBox(
                row,
                text="",
                variable=checked,
                width=25,
                checkbox_width=19,
                checkbox_height=19,
                fg_color=GREEN,
                hover_color=DARK_GREEN,
                border_color="#9DBEAA",
                command=lambda k=key: (
                    self.toggle_selection(k)
                )
            )

            checkbox.pack(
                side="left",
                padx=(12, 5)
            )

            info = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            info.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 10),
                pady=12
            )

            self.text(
                info,
                str(item.get("book_title", "")),
                12,
                TEXT,
                True
            ).pack(anchor="w")

            self.text(
                info,
                (
                    f"Reader: {item.get('reader_name', '')}"
                    f" | Code: {item.get('book_code', '')}"
                ),
                10,
                MUTED
            ).pack(
                anchor="w",
                pady=(5, 0)
            )

            self.text(
                info,
                (
                    "Borrowed: "
                    + self.format_date(
                        item.get("borrowed_date")
                    )
                    + " | Due date: "
                    + self.format_date(
                        item.get("due_date")
                    )
                ),
                10,
                MUTED
            ).pack(
                anchor="w",
                pady=(5, 0)
            )

        self.update_selection()

    # ==========================================
    # SELECTION
    # ==========================================

    def toggle_selection(self, key):
        checked = self.check_vars[key].get()

        if checked:
            self.selected_ids.add(key)
        else:
            self.selected_ids.discard(key)

        self.update_selection()

    def update_selection(self):
        total = len(
            self.filtered_transactions
        )

        selected = len(
            self.selected_ids
        )

        self.count_label.configure(
            text=(
                f"{total} transactions"
                f" | {selected} selected"
            )
        )

        self.selected_button.configure(
            text=f"Return selected ({selected})",
            state=(
                "normal"
                if (
                    selected > 0
                    and self.on_return_selected is not None
                )
                else "disabled"
            )
        )

        self.all_button.configure(
            state=(
                "normal"
                if (
                    total > 0
                    and self.on_return_all is not None
                )
                else "disabled"
            )
        )

        self.render_summary()

    # ==========================================
    # SUMMARY
    # ==========================================

    def render_summary(self):
        self.clear(
            self.summary_container
        )

        if not self.selected_ids:
            return

        selected_items = [
            item
            for item in self.filtered_transactions
            if (
                self.transaction_key(item)
                in self.selected_ids
            )
        ]

        summary = ctk.CTkFrame(
            self.summary_container,
            fg_color=PALE_GREEN,
            corner_radius=7,
            border_width=1,
            border_color="#D8F2E4"
        )

        summary.pack(fill="x")

        self.text(
            summary,
            "Summary",
            12,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=12,
            pady=(10, 3)
        )

        fines = [
            item.get("fine_amount")
            for item in selected_items
        ]

        if all(
            value is not None
            for value in fines
        ):
            fine_text = self.format_money(
                sum(
                    float(value)
                    for value in fines
                )
            )
        else:
            fine_text = "Not calculated"

        self.text(
            summary,
            (
                f"Books: {len(selected_items)}"
                f" | Total fine: {fine_text}"
            ),
            11,
            MUTED
        ).pack(
            anchor="w",
            padx=12,
            pady=(0, 10)
        )

    # ==========================================
    # CALLBACKS
    # ==========================================

    def return_selected(self):
        if self.on_return_selected is None:
            return

        selected_items = [
            item
            for item in self.filtered_transactions
            if (
                self.transaction_key(item)
                in self.selected_ids
            )
        ]

        if selected_items:
            self.on_return_selected(
                selected_items
            )

    def return_all(self):
        if (
            self.on_return_all is not None
            and self.filtered_transactions
        ):
            self.on_return_all(
                list(self.filtered_transactions)
            )

    def navigate(self, page_name):
        if self.on_navigate is not None:
            self.on_navigate(page_name)

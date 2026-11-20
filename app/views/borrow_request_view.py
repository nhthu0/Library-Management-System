
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from app.config.theme import WHITE


# ==========================================
# COLORS
# ==========================================

PAGE_BG = "#F7FAF9"
SIDEBAR_BG = "#2D6857"
SIDEBAR_ITEM = "#397461"
ACTIVE_GREEN = "#70D18F"

GREEN = "#008D3F"
DARK_GREEN = "#007536"

TEXT = "#2D3A40"
MUTED = "#8293A5"
BORDER = "#E5EBE9"
PALE_GREEN = "#F2FBF6"
RED = "#EF3E4A"


class BorrowRequestView(ctk.CTkFrame):
    """Borrow books screen matching the original UI."""

    def __init__(
        self,
        master,
        on_navigate=None,
        on_search_readers=None,
        on_search_books=None,
        on_confirm_borrow=None,
        on_request_borrow=None,
        on_load_history=None,
        selected_books=None
    ):
        super().__init__(
            master,
            fg_color=PAGE_BG
        )

        self.on_navigate = on_navigate
        self.on_search_readers = on_search_readers
        self.on_search_books = on_search_books
        self.on_confirm_borrow = on_confirm_borrow
        self.on_request_borrow = on_request_borrow
        self.on_load_history = on_load_history

        self.assets = (
            Path(__file__).resolve().parents[1]
            / "assets"
        )

        self.images = []

        self.readers = []
        self.books = []

        self.selected_reader = None
        self.selected_books = selected_books if selected_books is not None else []

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

        if self.on_request_borrow is not None:
            self.main.grid_columnconfigure(0, weight=3, uniform="borrow")
            self.main.grid_columnconfigure(1, weight=2, uniform="borrow")
            self.main.grid_rowconfigure(1, weight=1)
        else:
            self.main.grid_columnconfigure(0, weight=1)
            self.main.grid_rowconfigure(2, weight=1)

        self.build_header()
        self.build_search_section()
        self.build_borrowing_list()

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
            font=(
                "Segoe UI",
                size,
                "bold" if bold else "normal"
            ),
            text_color=color,
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
        """
        Load real PNG icons from app/assets/icons.
        Recolor them to match the original sidebar.
        """
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

        # --------------------------------------
        # LOGO
        # --------------------------------------

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
                "▣",
                21,
                SIDEBAR_BG,
                True,
                width=40,
                height=40,
                fg_color=ACTIVE_GREEN,
                corner_radius=20
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

        # --------------------------------------
        # MENU - REAL PNG ICONS
        # --------------------------------------

        menus = [
            ("dashboard.png", "Home"),
            ("borrow.png", "Borrow books"),
            ("booklist.png", "Return books"),
            ("history.png", "History"),
            ("management.png", "Manage books"),
            ("statistics.png", "Statistics")
        ]

        if self.on_request_borrow is not None:
            menus = [
                ("dashboard.png", "Dashboard"),
                ("booklist.png", "Browse Books"),
                ("borrow.png", "Borrow books"),
                ("booklist.png", "Return Books"),
                ("history.png", "Borrow Status"),
                ("history.png", "Borrowing History"),
            ]

        for icon_filename, title in menus:
            active = title == "Borrow books"

            icon = self.load_menu_icon(
                icon_filename,
                active=active
            )

            menu_row = ctk.CTkFrame(
                sidebar,
                height=45 if active else 34,
                fg_color=(
                    ACTIVE_GREEN
                    if active
                    else SIDEBAR_ITEM
                ),
                corner_radius=6
            )

            menu_row.pack(
                fill="x",
                padx=10,
                pady=3
            )

            menu_row.pack_propagate(False)

            button = ctk.CTkButton(
                menu_row,
                text=title,
                image=icon,
                compound="left",
                anchor="w",
                height=30 if active else 34,
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
            )

            button.pack(
                fill="x",
                padx=4
            )

            if active:
                self.text(
                    menu_row,
                    "Borrow books",
                    9,
                    "#42745C"
                ).place(
                    x=37,
                    y=27
                )

                self.text(
                    menu_row,
                    "•",
                    16,
                    "#39765A"
                ).place(
                    relx=0.94,
                    rely=0.42,
                    anchor="center"
                )

        # --------------------------------------
        # PUSH PROFILE TO BOTTOM
        # --------------------------------------

        ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        ).pack(
            fill="both",
            expand=True
        )

        # --------------------------------------
        # ORIGINAL PROFILE:
        # Librarian
        # Library
        # LG
        # --------------------------------------

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

        self.text(
            footer,
            "LG",
            11,
            "#326A50",
            True,
            width=32,
            height=32,
            fg_color=ACTIVE_GREEN,
            corner_radius=16
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
            columnspan=2 if self.on_request_borrow is not None else 1,
            sticky="ew",
            pady=(10, 20)
        )

        self.text(
            header,
            "Borrow books",
            21,
            TEXT,
            True
        ).pack(anchor="w")

        self.text(
            header,
            "Choose a book and send a borrowing request" if self.on_request_borrow is not None
            else "Manage book borrowing transactions",
            11,
            MUTED
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

    # ==========================================
    # SEARCH SECTION
    # ==========================================

    def build_search_section(self):
        section = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )

        section.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 16)
        )

        if self.on_request_borrow is not None:
            section.grid_configure(sticky="nsew", padx=(0, 12), pady=0)
            section.grid_columnconfigure(0, weight=1)
            section.grid_rowconfigure(0, weight=1)
            self.book_card = self.card(section)
            self.book_card.grid(row=0, column=0, sticky="nsew")
            self.build_book_search()
            return

        section.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="search"
        )

        self.reader_card = self.card(section)

        self.reader_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        self.book_card = self.card(section)

        self.book_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0)
        )

        self.build_reader_search()
        self.build_book_search()

    # ==========================================
    # FIND READER
    # ==========================================

    def build_reader_search(self):
        card = self.reader_card

        self.text(
            card,
            "♙  Find reader",
            13,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(16, 3)
        )

        self.text(
            card,
            "Search by membership card number or reader name",
            10,
            MUTED
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 12)
        )

        search = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        search.pack(
            fill="x",
            padx=15
        )

        self.reader_entry = ctk.CTkEntry(
            search,
            height=32,
            placeholder_text=(
                "Enter reader name or card number"
            ),
            fg_color=WHITE,
            border_color=BORDER,
            text_color=TEXT,
            font=("Segoe UI", 11)
        )

        self.reader_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        ctk.CTkButton(
            search,
            text="⌕",
            width=32,
            height=32,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            font=("Segoe UI", 18),
            command=self.search_readers
        ).pack(
            side="right",
            padx=(5, 0)
        )

        self.reader_entry.bind(
            "<Return>",
            lambda event: self.search_readers()
        )

        self.reader_results = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        self.reader_results.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(14, 15)
        )

        self.render_readers()

    # ==========================================
    # FIND BOOKS
    # ==========================================

    def build_book_search(self):
        card = self.book_card

        self.text(
            card,
            "◫  Find books",
            13,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(16, 3)
        )

        self.text(
            card,
            "Search by book code or title",
            10,
            MUTED
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 12)
        )

        search = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        search.pack(
            fill="x",
            padx=15
        )

        self.book_entry = ctk.CTkEntry(
            search,
            height=32,
            placeholder_text=(
                "Enter book code or title"
            ),
            fg_color=WHITE,
            border_color=BORDER,
            text_color=TEXT,
            font=("Segoe UI", 11)
        )

        self.book_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        ctk.CTkButton(
            search,
            text="⌕",
            width=32,
            height=32,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            font=("Segoe UI", 18),
            command=self.search_books
        ).pack(
            side="right",
            padx=(5, 0)
        )

        self.book_entry.bind(
            "<Return>",
            lambda event: self.search_books()
        )

        if self.on_request_borrow is not None:
            self.book_results = ctk.CTkScrollableFrame(
                card, height=95, fg_color="transparent"
            )
        else:
            self.book_results = ctk.CTkFrame(card, fg_color="transparent")

        self.book_results.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(14, 15)
        )

        self.render_books()

    # ==========================================
    # READER RESULTS
    # ==========================================

    def set_readers(self, readers):
        self.readers = list(readers or [])
        self.render_readers()

    def render_readers(self):
        self.clear(self.reader_results)

        if not self.readers:
            self.text(
                self.reader_results,
                "No reader selected",
                11,
                MUTED
            ).pack(
                anchor="w",
                pady=15
            )
            return

        for reader in self.readers:
            row = ctk.CTkFrame(
                self.reader_results,
                fg_color=PALE_GREEN,
                corner_radius=7,
                border_width=1,
                border_color="#D8F2E4"
            )

            row.pack(
                fill="x",
                pady=(0, 6)
            )

            name = str(
                reader.get("name", "")
            )

            card_number = str(
                reader.get("card_number", "")
            )

            borrowed = reader.get(
                "borrowed_count",
                0
            )

            selected = (
                self.selected_reader is not None
                and str(
                    self.selected_reader.get(
                        "card_number"
                    )
                ) == card_number
            )

            info = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            info.pack(
                side="left",
                fill="x",
                expand=True,
                padx=12,
                pady=10
            )

            self.text(
                info,
                name,
                12,
                TEXT,
                True
            ).pack(anchor="w")

            self.text(
                info,
                f"Card number: {card_number}",
                10,
                MUTED
            ).pack(
                anchor="w",
                pady=(5, 0)
            )

            self.text(
                info,
                f"Currently borrowed: {borrowed}",
                10,
                MUTED
            ).pack(
                anchor="w",
                pady=(4, 0)
            )

            ctk.CTkButton(
                row,
                text=(
                    "Selected"
                    if selected
                    else "Select"
                ),
                width=65,
                height=24,
                fg_color=(
                    "#E1F7E9"
                    if selected
                    else GREEN
                ),
                text_color=(
                    GREEN
                    if selected
                    else WHITE
                ),
                hover_color=(
                    "#D5F1DF"
                    if selected
                    else DARK_GREEN
                ),
                font=(
                    "Segoe UI",
                    10,
                    "bold"
                ),
                command=lambda r=reader: (
                    self.select_reader(r)
                )
            ).pack(
                side="right",
                padx=12
            )

    def select_reader(self, reader):
        self.selected_reader = reader

        self.render_readers()
        self.update_confirm_button()

    def search_readers(self):
        keyword = (
            self.reader_entry.get().strip()
        )

        if self.on_search_readers:
            self.on_search_readers(keyword)

    # ==========================================
    # BOOK RESULTS
    # ==========================================

    def set_books(self, books):
        self.books = list(books or [])
        self.render_books()

    def render_books(self):
        self.clear(self.book_results)

        if not self.books:
            self.text(
                self.book_results,
                "No books found",
                11,
                MUTED
            ).pack(
                anchor="w",
                pady=15
            )
            return

        for book in self.books:
            row = ctk.CTkFrame(
                self.book_results,
                fg_color=PALE_GREEN,
                corner_radius=7
            )

            row.pack(
                fill="x",
                pady=(0, 6)
            )

            title = str(
                book.get("title", "")
            )

            author = str(
                book.get("author", "")
            )

            code = str(
                book.get("code", "")
            )

            available = book.get(
                "available_quantity",
                0
            )

            info = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            info.pack(
                side="left",
                fill="x",
                expand=True,
                padx=12,
                pady=10
            )

            self.text(
                info,
                title,
                12,
                TEXT,
                True
            ).pack(anchor="w")

            self.text(
                info,
                (
                    f"Author: {author}"
                    f" | Code: {code}"
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
                    "Available"
                    if available > 0
                    else "Unavailable"
                ),
                10,
                (
                    GREEN
                    if available > 0
                    else RED
                ),
                True
            ).pack(
                anchor="w",
                pady=(5, 0)
            )

            already_selected = any(
                str(item.get("code")) == code
                for item in self.selected_books
            )

            ctk.CTkButton(
                row,
                text="+",
                width=30,
                height=30,
                fg_color=GREEN,
                hover_color=DARK_GREEN,
                font=("Segoe UI", 19),
                state=(
                    "normal"
                    if (
                        available > 0
                        and not already_selected
                    )
                    else "disabled"
                ),
                command=lambda b=book: (
                    self.add_book(b)
                )
            ).pack(
                side="right",
                padx=12
            )

    def search_books(self):
        keyword = (
            self.book_entry.get().strip()
        )

        if self.on_request_borrow is not None:
            if self.on_search_books is None:
                return
            result = self.on_search_books(keyword)
            if not result["success"]:
                messagebox.showerror("Book search", result["message"], parent=self)
                return
            self.set_books([
                {**book, "code": str(book["book_id"])}
                for book in result["data"]
            ])
        elif self.on_search_books:
            self.on_search_books(keyword)

    # ==========================================
    # BORROWING LIST
    # ==========================================

    def build_borrowing_list(self):
        card = self.card(self.main)

        reader_mode = self.on_request_borrow is not None
        card.grid(
            row=1 if reader_mode else 2,
            column=1 if reader_mode else 0,
            sticky="nsew"
        )

        self.text(
            card,
            "Borrowing list",
            14,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 3)
        )

        self.count_label = self.text(
            card,
            "0 books selected",
            10,
            MUTED
        )

        self.count_label.pack(
            anchor="w",
            padx=15,
            pady=(0, 12)
        )

        self.borrowing_items = (
            ctk.CTkScrollableFrame(
                card,
                height=64,
                fg_color="transparent",
                corner_radius=0
            )
        )

        footer = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        footer.pack(
            side="bottom",
            fill="x",
            padx=15,
            pady=(0, 10)
        )

        self.borrowing_items.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 6)
        )

        ctk.CTkFrame(
            footer,
            height=1,
            fg_color="#EDF0EE"
        ).pack(
            fill="x",
            pady=(0, 6)
        )

        self.confirm_button = ctk.CTkButton(
            footer,
            text="✓  Confirm borrowing",
            height=32,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            font=(
                "Segoe UI",
                11,
                "bold"
            ),
            state="disabled",
            command=self.confirm_borrowing
        )

        self.confirm_button.pack(
            fill="x"
        )

        self.render_borrowing_list()

    # ==========================================
    # ADD / REMOVE BOOK
    # ==========================================

    def add_book(self, book):
        code = str(
            book.get("code", "")
        )

        if any(
            str(item.get("code")) == code
            for item in self.selected_books
        ):
            return

        if book.get(
            "available_quantity",
            0
        ) <= 0:
            return

        if self.on_request_borrow is not None:
            if len(self.selected_books) >= 3:
                messagebox.showinfo("Borrow books", "You can select up to 3 books.", parent=self)
                return
            book = {**book, "requested_quantity": 1}

        self.selected_books.append(book)

        self.render_borrowing_list()
        self.render_books()

    def remove_book(self, code):
        self.selected_books[:] = [
            book
            for book in self.selected_books
            if str(
                book.get("code", "")
            ) != str(code)
        ]

        self.render_borrowing_list()
        self.render_books()

    # ==========================================
    # RENDER BORROWING LIST
    # ==========================================

    def render_borrowing_list(self):
        self.clear(
            self.borrowing_items
        )

        count = len(
            self.selected_books
        )

        self.count_label.configure(
            text=(
                f"{count} book selected"
                if count == 1
                else f"{count} books selected"
            )
        )

        for book in self.selected_books:
            row = ctk.CTkFrame(
                self.borrowing_items,
                fg_color=PALE_GREEN,
                corner_radius=7,
                border_width=1,
                border_color="#E2F4E9"
            )

            row.pack(
                fill="x",
                pady=(0, 8)
            )

            info = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            info.pack(
                side="left",
                fill="x",
                expand=True,
                padx=12,
                pady=10
            )

            self.text(
                info,
                str(
                    book.get("title", "")
                ),
                12,
                TEXT,
                True
            ).pack(
                anchor="w"
            )

            self.text(
                info,
                (
                    f"Author: {book.get('author', '')}"
                    f" | Code: {book.get('code', '')}"
                ),
                10,
                MUTED
            ).pack(
                anchor="w",
                pady=(7, 0)
            )

            ctk.CTkButton(
                row,
                text="✕",
                width=30,
                height=30,
                fg_color=RED,
                hover_color="#D72E3B",
                command=lambda code=book.get("code"): (
                    self.remove_book(code)
                )
            ).pack(
                side="right",
                padx=12
            )

            if self.on_request_borrow is not None:
                maximum = min(3, book["available_quantity"])
                quantity = ctk.CTkOptionMenu(
                    row, width=60, values=[str(value) for value in range(1, maximum + 1)],
                    command=lambda value, item=book: item.update(requested_quantity=int(value))
                )
                quantity.set(str(book["requested_quantity"]))
                quantity.pack(side="right", padx=(0, 8))
                self.text(row, "Quantity", 11, MUTED).pack(side="right")

        self.update_confirm_button()

    # ==========================================
    # CONFIRM BORROWING
    # ==========================================

    def update_confirm_button(self):
        count = len(
            self.selected_books
        )

        if self.on_request_borrow is not None:
            self.confirm_button.configure(
                text="Send borrowing requests",
                state="normal" if count else "disabled"
            )
            return

        self.confirm_button.configure(
            text=(
                f"✓  Confirm borrowing {count} "
                + (
                    "book"
                    if count == 1
                    else "books"
                )
            ),
            state=(
                "normal"
                if (
                    self.selected_reader is not None
                    and count > 0
                    and self.on_confirm_borrow is not None
                )
                else "disabled"
            )
        )

    def confirm_borrowing(self):
        if self.on_request_borrow is not None:
            if not self.selected_books:
                return
            total = sum(book["requested_quantity"] for book in self.selected_books)
            if total > 3:
                messagebox.showerror(
                    "Borrow books", "Select a total of at most 3 copies.", parent=self
                )
                return

            if self.on_load_history is not None:
                history = self.on_load_history()
                if not history["success"]:
                    messagebox.showerror("Borrow books", history["message"], parent=self)
                    return
                active = sum(
                    row["quantity"] - row["returned_quantity"]
                    for row in history["data"]
                    if row["status"] in ("Borrowed", "ReturnRequested")
                )
                if active + total > 3:
                    messagebox.showerror(
                        "Borrow books",
                        f"You already have {active} active copies. You can request at most {max(0, 3 - active)} more.",
                        parent=self
                    )
                    return

            remaining = []
            messages = []
            for book in self.selected_books:
                result = self.on_request_borrow(book["book_id"], book["requested_quantity"])
                if not result["success"]:
                    remaining.append(book)
                status = "Pending admin approval" if result["success"] else result["message"]
                messages.append(f"{book['title']}: {status}")

            self.selected_books[:] = remaining
            self.render_borrowing_list()
            self.render_books()
            dialog = messagebox.showwarning if remaining else messagebox.showinfo
            dialog("Borrow books", "\n".join(messages), parent=self)
            if not remaining and self.on_navigate is not None:
                self.navigate("Borrow Status")
            return

        if (
            self.selected_reader is None
            or not self.selected_books
            or self.on_confirm_borrow is None
        ):
            return

        self.on_confirm_borrow(
            self.selected_reader,
            list(self.selected_books)
        )

    # ==========================================
    # NAVIGATION
    # ==========================================

    def navigate(self, page_name):
        if self.on_navigate:
            self.on_navigate(page_name)


import customtkinter as ctk
from pathlib import Path
from PIL import Image

from app.config.theme import BG_GREEN, WHITE


BG = "#F5F7F8"
TEXT = "#20312C"
MUTED = "#788A84"
BORDER = "#E1E9E5"
GREEN = "#008B45"
LIGHT_GREEN = "#78D69B"


class BookSearchView(ctk.CTkFrame):
    """Book Search UI - no backend connection."""

    def __init__(self, master, on_navigate=None):
        super().__init__(master, fg_color=BG)

        self.on_navigate = on_navigate
        self.assets = Path(__file__).resolve().parents[1] / "assets"
        self.images = []
        self.books = []
        self.filtered_books = []

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
        self.build_books_panel()

    # ==========================================
    # COMMON
    # ==========================================

    def label(
        self, parent, text,
        size=13, color=TEXT,
        bold=False, **kwargs
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

    def load_icon(self, name, active=False):
        path = self.assets / "icons" / f"{name}.png"

        if not path.exists():
            return None

        with Image.open(path) as source:
            image = source.convert("RGBA")

        color = (
            (37, 92, 73)
            if active
            else (255, 255, 255)
        )

        tinted = Image.new(
            "RGBA",
            image.size,
            (*color, 255)
        )
        tinted.putalpha(image.getchannel("A"))

        result = ctk.CTkImage(
            light_image=tinted,
            dark_image=tinted,
            size=(19, 19)
        )

        self.images.append(result)
        return result

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
            ("management", "Book Management"),
            ("statistics", "Statistics")
        ]

        for icon_name, title in menus:
            active = title == "Borrow Books"

            icon = self.load_icon(
                icon_name,
                active
            )

            button = ctk.CTkButton(
                sidebar,
                text=title,
                image=icon,
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
            )

            button.pack(
                fill="x",
                padx=14,
                pady=4
            )

        ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        ).pack(
            fill="both",
            expand=True
        )

        self.label(
            sidebar,
            "Librarian",
            12,
            WHITE,
            True
        ).pack(pady=(0, 2))

        self.label(
            sidebar,
            "Library",
            11,
            "#C6DCD3"
        ).pack(pady=(0, 8))

        avatar = ctk.CTkFrame(
            sidebar,
            width=42,
            height=42,
            corner_radius=21,
            fg_color=LIGHT_GREEN
        )
        avatar.pack(pady=(0, 22))
        avatar.pack_propagate(False)

        self.label(
            avatar,
            "LG",
            12,
            "#245A46",
            True
        ).place(
            relx=0.5,
            rely=0.5,
            anchor="center"
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

        self.label(
            header,
            "Find books",
            26,
            TEXT,
            True
        ).pack(anchor="w")

        self.label(
            header,
            "Search and select books from the library",
            13,
            MUTED
        ).pack(
            anchor="w",
            pady=(4, 0)
        )

    # ==========================================
    # SEARCH PANEL
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
            "Search books",
            16,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=18,
            pady=(17, 4)
        )

        self.label(
            card,
            "Search by book code, title, author or category",
            12,
            MUTED
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 14)
        )

        controls = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        controls.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        controls.grid_columnconfigure(
            0,
            weight=1
        )

        self.search_entry = ctk.CTkEntry(
            controls,
            height=40,
            placeholder_text="Enter book code or title...",
            fg_color=WHITE,
            border_color=BORDER,
            text_color=TEXT
        )
        self.search_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 10)
        )

        self.search_button = ctk.CTkButton(
            controls,
            text="⌕  Search",
            width=115,
            height=40,
            fg_color=GREEN,
            hover_color="#00763C",
            command=self.search_books
        )
        self.search_button.grid(
            row=0,
            column=1
        )

        self.search_entry.bind(
            "<Return>",
            lambda event: self.search_books()
        )

    # ==========================================
    # BOOK RESULTS
    # ==========================================

    def build_books_panel(self):
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
            pady=(18, 12)
        )

        self.label(
            top,
            "Available books",
            16,
            TEXT,
            True
        ).pack(side="left")

        self.count_label = self.label(
            top,
            "0 books",
            12,
            MUTED
        )
        self.count_label.pack(side="right")

        self.results_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        self.results_frame.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 18)
        )

        self.render_books()

    def render_books(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.count_label.configure(
            text=f"{len(self.filtered_books)} books"
        )

        if not self.filtered_books:
            empty = ctk.CTkFrame(
                self.results_frame,
                fg_color=WHITE,
                height=320
            )
            empty.pack(
                fill="both",
                expand=True
            )
            empty.pack_propagate(False)

            self.label(
                empty,
                "▤",
                38,
                "#B5C5BE"
            ).place(
                relx=0.5,
                rely=0.39,
                anchor="center"
            )

            self.label(
                empty,
                "No books found",
                15,
                MUTED
            ).place(
                relx=0.5,
                rely=0.55,
                anchor="center"
            )

            self.label(
                empty,
                "Search to display available books",
                12,
                MUTED
            ).place(
                relx=0.5,
                rely=0.64,
                anchor="center"
            )
            return

        for book in self.filtered_books:
            row = ctk.CTkFrame(
                self.results_frame,
                fg_color="#F1FAF5",
                corner_radius=8,
                border_width=1,
                border_color="#E1F1E8"
            )
            row.pack(
                fill="x",
                pady=(0, 10)
            )

            info = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )
            info.pack(
                side="left",
                fill="both",
                expand=True,
                padx=16,
                pady=12
            )

            title = str(book.get("title", ""))
            author = str(book.get("author", ""))
            code = str(book.get("code", ""))
            category = str(book.get("category", ""))

            self.label(
                info,
                title,
                14,
                TEXT,
                True
            ).pack(anchor="w")

            self.label(
                info,
                f"Author: {author} | Code: {code}",
                12,
                MUTED
            ).pack(
                anchor="w",
                pady=(4, 0)
            )

            self.label(
                info,
                f"Category: {category}",
                11,
                MUTED
            ).pack(
                anchor="w",
                pady=(2, 0)
            )

            ctk.CTkButton(
                row,
                text="Select",
                width=95,
                height=34,
                fg_color=GREEN,
                hover_color="#00763C",
                command=lambda b=book: self.select_book(b)
            ).pack(
                side="right",
                padx=16
            )

    # ==========================================
    # UI DATA METHODS
    # ==========================================

    def set_books(self, books):
        """Receive real book data from controller later."""
        self.books = list(books or [])
        self.filtered_books = list(self.books)
        self.render_books()

    def search_books(self):
        keyword = self.search_entry.get().strip().lower()

        if not keyword:
            self.filtered_books = list(self.books)
        else:
            self.filtered_books = [
                book for book in self.books
                if keyword in " ".join(
                    str(book.get(field, ""))
                    for field in (
                        "code",
                        "title",
                        "author",
                        "category"
                    )
                ).lower()
            ]

        self.render_books()

    def select_book(self, book):
        if self.on_navigate:
            self.on_navigate("Borrow Books")

    def navigate(self, page_name):
        if self.on_navigate:
            self.on_navigate(page_name)

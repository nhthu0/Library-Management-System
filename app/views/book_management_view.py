
import customtkinter as ctk
from pathlib import Path
from PIL import Image

from app.config.theme import BG_GREEN, WHITE

BG = "#F5F7F8"
TEXT = "#20312C"
MUTED = "#788A84"
BORDER = "#E1E9E5"
GREEN = "#168452"
LIGHT_GREEN = "#D8EED3"

class BookManagementView(ctk.CTkFrame):

    def __init__(self, master, on_navigate=None, on_logout=None):
        super().__init__(master, fg_color=BG)

        self.on_navigate = on_navigate
        self.on_logout = on_logout

        self.assets = Path(__file__).resolve().parents[1] / "assets"
        self.menu_icons = {}
        self.logo_image = None

        self.books = []
        self.dialog = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()

        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            corner_radius=0
        )
        self.content.grid(row=0, column=1, sticky="nsew")

        self.build_header()
        self.build_search()
        self.build_book_list()

    # ==================================================
    # COMMON COMPONENTS
    # ==================================================

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

    def load_icon(self, filename, active=False):
        path = self.assets / "icons" / f"{filename}.png"

        if not path.exists():
            return None

        with Image.open(path) as source:
            original = source.convert("RGBA")

        color = (
            (47, 91, 75)
            if active
            else (255, 255, 255)
        )

        tinted = Image.new(
            "RGBA",
            original.size,
            (*color, 255)
        )
        tinted.putalpha(original.getchannel("A"))

        return ctk.CTkImage(
            light_image=tinted,
            dark_image=tinted,
            size=(20, 20)
        )
    def create_dropdown(
        self,
        parent,
        values,
        default,
        command=None,
        height=40
    ):
        container = ctk.CTkFrame(
            parent,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            corner_radius=6,
            height=height
        )

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)
        container.grid_propagate(False)

        selected = ctk.StringVar(value=default)
        current_values = list(values)
        import tkinter as tk

        menu = tk.Menu(
            container,
            tearoff=0,
            bg=WHITE,
            fg=TEXT,
            activebackground=LIGHT_GREEN,
            activeforeground=TEXT,
            font=("Segoe UI", 12),
            relief="flat",
            borderwidth=1
        )

        def choose(value):
            selected.set(value)

            if command is not None:
                command(value)

        def rebuild_menu():
            menu.delete(0, "end")

            for value in current_values:
                menu.add_command(
                    label=value,
                    command=lambda v=value: choose(v)
                )

        def open_menu():
            rebuild_menu()

            container.update_idletasks()

            x = container.winfo_rootx()
            y = (
                container.winfo_rooty()
                + container.winfo_height()
            )

            try:
                menu.tk_popup(x, y)
            finally:
                menu.grab_release()

        # Ô hiển thị giá trị đang chọn
        text_button = ctk.CTkButton(
            container,
            textvariable=selected,
            anchor="w",
            height=height - 4,
            fg_color=WHITE,
            hover_color="#F5F8F6",
            text_color=TEXT,
            corner_radius=5,
            font=("Segoe UI", 13),
            command=open_menu
        )
        text_button.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(4, 0),
            pady=1
        )

        arrow_button = ctk.CTkButton(
            container,
            text="▼",
            width=35,
            height=height - 4,
            fg_color=WHITE,
            hover_color="#F5F8F6",
            text_color=TEXT,
            corner_radius=5,
            font=("Arial", 13, "bold"),
            command=open_menu
        )
        arrow_button.grid(
            row=0,
            column=1,
            sticky="ns",
            padx=(0, 3),
            pady=1
        )

        def set_value(value):
            selected.set(value)

        def set_values(new_values):
            current_values.clear()
            current_values.extend(new_values)

        container.get = selected.get
        container.set = set_value
        container.set_values = set_values

        return container

    # ==================================================
    # SIDEBAR
    # ==================================================

    def build_sidebar(self):
        side = ctk.CTkFrame(
            self,
            width=235,
            fg_color=BG_GREEN,
            corner_radius=0
        )
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)

        logo_path = self.assets / "logo.png"

        if logo_path.exists():
            with Image.open(logo_path) as source:
                logo = source.convert("RGBA")

            self.logo_image = ctk.CTkImage(
                light_image=logo,
                dark_image=logo,
                size=(75, 75)
            )

            ctk.CTkLabel(
                side,
                text="",
                image=self.logo_image
            ).pack(pady=(22, 6))

        self.label(
            side,
            "Library",
            14,
            "#D9E9E0"
        ).pack()

        self.label(
            side,
            "Library System",
            23,
            WHITE,
            True
        ).pack(pady=(0, 30))

        self.label(
            side,
            "MANAGEMENT MENU",
            11,
            "#B9D5C9",
            True
        ).pack(
            anchor="w",
            padx=22,
            pady=(0, 12)
        )

        menus = [
            ("dashboard", "Dashboard"),
            ("borrow", "Borrow Books"),
            ("booklist", "Booklist"),
            ("history", "History"),
            ("management", "Book Management"),
            ("statistics", "Statistics"),
        ]

        for icon_name, name in menus:
            active = name == "Book Management"
            icon = self.load_icon(icon_name, active)

            if icon is not None:
                self.menu_icons[name] = icon

            ctk.CTkButton(
                side,
                text=name,
                image=icon,
                compound="left",
                anchor="w",
                height=44,
                corner_radius=7,
                fg_color=(
                    LIGHT_GREEN
                    if active
                    else "transparent"
                ),
                hover_color="#497A69",
                text_color=(
                    BG_GREEN
                    if active
                    else WHITE
                ),
                font=(
                    "Segoe UI",
                    13,
                    "bold" if active else "normal"
                ),
                command=lambda page=name: self.navigate(page)
            ).pack(
                fill="x",
                padx=15,
                pady=4
            )

        ctk.CTkFrame(
            side,
            fg_color="transparent"
        ).pack(
            fill="both",
            expand=True
        )

        help_box = ctk.CTkFrame(
            side,
            fg_color="#416E5D",
            corner_radius=9
        )
        help_box.pack(
            fill="x",
            padx=15,
            pady=(8, 12)
        )

        self.label(
            help_box,
            "Need help?",
            14,
            WHITE,
            True
        ).pack(
            anchor="w",
            padx=14,
            pady=(12, 3)
        )

        self.label(
            help_box,
            "Contact the library support team.",
            11,
            "#D9E9E0",
            wraplength=180,
            justify="left"
        ).pack(
            anchor="w",
            padx=14,
            pady=(0, 12)
        )

        ctk.CTkButton(
            side,
            text="Administrator",
            anchor="w",
            height=44,
            fg_color="transparent",
            hover_color="#497A69",
            text_color=WHITE,
            font=("Segoe UI", 13, "bold"),
            command=self.logout
        ).pack(
            fill="x",
            padx=15,
            pady=(0, 16)
        )

    # ==================================================
    # HEADER
    # ==================================================

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
            "Book management",
            26,
            bold=True
        ).pack(anchor="w")

        self.label(
            header,
            "Add, edit, delete and manage book information",
            13,
            MUTED
        ).pack(
            anchor="w",
            pady=(4, 0)
        )

    # ==================================================
    # SEARCH AND FILTERS
    # ==================================================

    def build_search(self):
        card = self.panel(self.content)
        card.pack(
            fill="x",
            padx=25,
            pady=(0, 18)
        )

        heading = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        heading.pack(
            fill="x",
            padx=18,
            pady=(16, 12)
        )

        left = ctk.CTkFrame(
            heading,
            fg_color="transparent"
        )
        left.pack(side="left")

        self.label(
            left,
            "Search and filters",
            15,
            bold=True
        ).pack(anchor="w")

        self.label(
            left,
            "Search books by title, author or book code",
            12,
            MUTED
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

        ctk.CTkButton(
            heading,
            text="+   Add new book",
            width=150,
            height=38,
            fg_color=GREEN,
            hover_color="#126A43",
            command=self.open_add_dialog
        ).pack(side="right")

        filters = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        filters.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        filters.grid_columnconfigure(0, weight=3)
        filters.grid_columnconfigure(1, weight=2)
        filters.grid_columnconfigure(2, weight=2)

        self.search_entry = ctk.CTkEntry(
            filters,
            height=40,
            placeholder_text="Search books...",
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

        self.search_entry.bind(
            "<KeyRelease>",
            lambda event: self.render_books()
        )

        # CATEGORY FILTER ▼
        self.category_filter = self.create_dropdown(
            filters,
            values=["All categories"],
            default="All categories",
            command=lambda value: self.render_books()
        )
        self.category_filter.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 10)
        )

        # STATUS FILTER ▼
        self.status_filter = self.create_dropdown(
            filters,
            values=[
                "All statuses",
                "Available",
                "Unavailable"
            ],
            default="All statuses",
            command=lambda value: self.render_books()
        )
        self.status_filter.grid(
            row=0,
            column=2,
            sticky="ew"
        )

    # ==================================================
    # BOOK LIST
    # ==================================================

    def build_book_list(self):
        card = self.panel(self.content)
        card.pack(
            fill="x",
            padx=25,
            pady=(0, 25)
        )

        self.label(
            card,
            "Book list",
            17,
            bold=True
        ).pack(
            anchor="w",
            padx=20,
            pady=(18, 2)
        )

        self.count_label = self.label(
            card,
            "0 books",
            12,
            MUTED
        )
        self.count_label.pack(
            anchor="w",
            padx=20,
            pady=(0, 15)
        )

        self.table = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        self.table.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        self.render_books()

    def render_books(self):
        for child in self.table.winfo_children():
            child.destroy()

        columns = [
            "Code",
            "Book title",
            "Author",
            "Category",
            "Quantity",
            "Status",
            "Actions"
        ]

        weights = [1, 4, 2, 2, 1, 2, 2]

        for index, weight in enumerate(weights):
            self.table.grid_columnconfigure(
                index,
                weight=weight,
                minsize=70
            )

        for col, title in enumerate(columns):
            self.label(
                self.table,
                title,
                12,
                TEXT,
                True,
                anchor="w"
            ).grid(
                row=0,
                column=col,
                sticky="nsew",
                padx=8,
                pady=(13, 13)
            )

        query = self.search_entry.get().strip().lower()
        category = self.category_filter.get()
        status = self.status_filter.get()

        filtered = [
            book for book in self.books
            if (
                not query
                or any(
                    query in str(book.get(key, "")).lower()
                    for key in ("code", "title", "author")
                )
            )
            and (
                category == "All categories"
                or book.get("category") == category
            )
            and (
                status == "All statuses"
                or book.get("status") == status
            )
        ]

        self.count_label.configure(
            text=f"{len(filtered)} books"
        )

        if not filtered:
            self.label(
                self.table,
                "No books available",
                13,
                MUTED,
                height=200
            ).grid(
                row=1,
                column=0,
                columnspan=7,
                sticky="nsew"
            )
            return

        for row_index, book in enumerate(filtered, start=1):
            fields = [
                "code",
                "title",
                "author",
                "category",
                "quantity",
                "status"
            ]

            for col, field in enumerate(fields):
                self.label(
                    self.table,
                    str(book.get(field, "—")),
                    12,
                    GREEN if field == "status" else TEXT,
                    anchor="w"
                ).grid(
                    row=row_index,
                    column=col,
                    sticky="ew",
                    padx=8,
                    pady=12
                )

            actions = ctk.CTkFrame(
                self.table,
                fg_color="transparent"
            )
            actions.grid(
                row=row_index,
                column=6,
                sticky="w",
                padx=4
            )

            buttons = [
                (
                    "View",
                    lambda b=book: self.open_book_dialog("view", b),
                    "#6E8379"
                ),
                (
                    "Edit",
                    lambda b=book: self.open_book_dialog("edit", b),
                    GREEN
                ),
                (
                    "Delete",
                    lambda b=book: self.open_delete_dialog(b),
                    "#D83F4F"
                )
            ]

            for title, callback, color in buttons:
                ctk.CTkButton(
                    actions,
                    text=title,
                    width=48,
                    height=29,
                    fg_color=color,
                    command=callback
                ).pack(
                    side="left",
                    padx=2
                )

    def update_books(self, books):
        # Dùng khi kết nối controller sau này
        self.books = list(books)

        categories = sorted({
            str(book.get("category"))
            for book in self.books
            if book.get("category")
        })

        self.category_filter.set_values(
            ["All categories"] + categories
        )
        self.category_filter.set("All categories")

        self.render_books()

    # ==================================================
    # DIALOG
    # ==================================================

    def open_add_dialog(self):
        self.open_book_dialog("add")

    def create_dialog(
        self,
        title,
        subtitle,
        width=430,
        height=520
    ):
        if (
            self.dialog is not None
            and self.dialog.winfo_exists()
        ):
            self.dialog.focus()
            return None

        window = ctk.CTkToplevel(self)
        self.dialog = window

        window.title(title)
        window.geometry(f"{width}x{height}")
        window.resizable(False, False)
        window.transient(self.winfo_toplevel())
        window.grab_set()
        window.configure(fg_color="#F8FAF9")

        window.protocol(
            "WM_DELETE_WINDOW",
            self.close_dialog
        )

        window.after(
            30,
            lambda: self.center_dialog(
                window,
                width,
                height
            )
        )

        self.label(
            window,
            title,
            19,
            bold=True
        ).pack(
            anchor="w",
            padx=22,
            pady=(20, 2)
        )

        self.label(
            window,
            subtitle,
            12,
            MUTED
        ).pack(
            anchor="w",
            padx=22,
            pady=(0, 14)
        )

        return window

    def center_dialog(self, window, width, height):
        root = self.winfo_toplevel()

        x = root.winfo_rootx() + max(
            0,
            (root.winfo_width() - width) // 2
        )

        y = root.winfo_rooty() + max(
            0,
            (root.winfo_height() - height) // 2
        )

        window.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def close_dialog(self):
        if (
            self.dialog is not None
            and self.dialog.winfo_exists()
        ):
            self.dialog.grab_release()
            self.dialog.destroy()

        self.dialog = None

    # ==================================================
    # ADD / EDIT / VIEW BOOK
    # ==================================================

    def open_book_dialog(self, mode, book=None):
        titles = {
            "add": (
                "Add new book",
                "Enter the new book information"
            ),
            "edit": (
                "Edit book information",
                "Update book information in the system"
            ),
            "view": (
                "Book information",
                "View book details"
            )
        }

        title, subtitle = titles[mode]
        window = self.create_dialog(title, subtitle)

        if window is None:
            return

        form = ctk.CTkFrame(
            window,
            fg_color="transparent"
        )
        form.pack(
            fill="both",
            expand=True,
            padx=22
        )

        entries = {}

        fields = [
            ("Book title", "title"),
            ("Author", "author"),
            ("Category", "category"),
            ("Quantity", "quantity")
        ]

        for label_text, key in fields:
            self.label(
                form,
                label_text,
                12,
                bold=True
            ).pack(
                anchor="w",
                pady=(9, 4)
            )

            if key == "category":
                # CATEGORY DROPDOWN ▼
                control = self.create_dropdown(
                    form,
                    values=[
                        "Select category",
                        "Programming",
                        "AI/ML",
                        "DevOps",
                        "Database",
                        "Networking",
                        "Other"
                    ],
                    default=(
                        str(book.get("category", "Select category"))
                        if book
                        else "Select category"
                    ),
                    height=37
                )

            else:
                control = ctk.CTkEntry(
                    form,
                    height=37,
                    fg_color=WHITE,
                    border_color=BORDER,
                    text_color=TEXT
                )

                if book is not None:
                    control.insert(
                        0,
                        str(book.get(key, ""))
                    )

            control.pack(fill="x")
            entries[key] = control

            if mode == "view" and isinstance(control, ctk.CTkEntry):
                control.configure(state="disabled")

        footer = ctk.CTkFrame(
            window,
            fg_color="transparent"
        )
        footer.pack(
            fill="x",
            padx=22,
            pady=(15, 22)
        )

        ctk.CTkButton(
            footer,
            text=(
                "Close"
                if mode == "view"
                else "Cancel"
            ),
            width=85,
            height=38,
            fg_color="#E9EFEB",
            hover_color="#D9E5DE",
            text_color=TEXT,
            command=self.close_dialog
        ).pack(
            side="right",
            padx=(8, 0)
        )

        if mode != "view":
            # Chưa kết nối backend nên chưa lưu
            ctk.CTkButton(
                footer,
                text=(
                    "Add book"
                    if mode == "add"
                    else "Save changes"
                ),
                width=110,
                height=38,
                fg_color=GREEN,
                state="disabled"
            ).pack(side="right")

    # ==================================================
    # DELETE CONFIRMATION
    # ==================================================

    def open_delete_dialog(self, book):
        window = self.create_dialog(
            "Confirm book deletion",
            "Are you sure you want to delete this book?",
            width=430,
            height=200
        )

        if window is None:
            return

        footer = ctk.CTkFrame(
            window,
            fg_color="transparent"
        )
        footer.pack(
            side="bottom",
            fill="x",
            padx=22,
            pady=20
        )

        ctk.CTkButton(
            footer,
            text="Delete book",
            width=105,
            height=38,
            fg_color=GREEN,
            state="disabled"
        ).pack(side="right")

        ctk.CTkButton(
            footer,
            text="Cancel",
            width=85,
            height=38,
            fg_color="#E9EFEB",
            hover_color="#D9E5DE",
            text_color=TEXT,
            command=self.close_dialog
        ).pack(
            side="right",
            padx=(0, 10)
        )

    # ==================================================
    # NAVIGATION
    # ==================================================

    def navigate(self, page_name):
        if (
            page_name != "Book Management"
            and self.on_navigate
        ):
            self.on_navigate(page_name)

    def logout(self):
        if self.on_logout:
            self.on_logout()

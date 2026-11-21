
import customtkinter as ctk
from pathlib import Path
from PIL import Image

from app.config.theme import BG_GREEN, WHITE


BG = "#F5F7F8"
TEXT = "#20312C"
MUTED = "#788A84"
BORDER = "#E1E9E5"
GREEN = "#168452"


class ReaderDashboardView(ctk.CTkFrame):
    def __init__(self, master, on_navigate=None, on_logout=None, transactions=None):
        super().__init__(master, fg_color=BG)

        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.transactions = transactions or []
        self.current_borrowings = [
            row for row in self.transactions
            if row["status"] in ("Approved", "Overdue", "ReturnRequested")
        ]

        self.assets = Path(__file__).resolve().parents[1] / "assets"
        self.menu_icons = {}
        self.logo_image = None

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
        self.build_statistics()
        self.build_quick_actions()
        self.build_current_borrowings()
        self.build_reminders()

    # ---------------- COMMON COMPONENTS ----------------

    def create_label(
        self, parent, text, size=13,
        color=TEXT, bold=False, **kwargs
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

    def create_panel(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color=WHITE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )

    def create_section_title(self, parent, title, subtitle=None):
        header = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        header.pack(
            fill="x",
            padx=20,
            pady=(17, 12)
        )

        self.create_label(
            header, title, 17, bold=True
        ).pack(anchor="w")

        if subtitle:
            self.create_label(
                header, subtitle, 12, MUTED
            ).pack(anchor="w", pady=(3, 0))

    # ---------------- SIDEBAR ----------------

    def load_icon(self, name, active=False):
        path = self.assets / "icons" / f"{name}.png"

        if not path.exists():
            return None

        image = Image.open(path).convert("RGBA")

        color = (
            (47, 91, 75)
            if active else
            (255, 255, 255)
        )

        colored = Image.new(
            "RGBA",
            image.size,
            (*color, 255)
        )
        colored.putalpha(image.getchannel("A"))

        return ctk.CTkImage(
            light_image=colored,
            dark_image=colored,
            size=(20, 20)
        )

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
            logo = Image.open(logo_path).convert("RGBA")
            self.logo_image = ctk.CTkImage(
                light_image=logo,
                dark_image=logo,
                size=(75, 75)
            )

            ctk.CTkLabel(
                sidebar,
                text="",
                image=self.logo_image
            ).pack(pady=(22, 6))

        self.create_label(
            sidebar,
            "Library",
            14,
            "#D9E9E0"
        ).pack()

        self.create_label(
            sidebar,
            "Library System",
            23,
            WHITE,
            True
        ).pack(pady=(0, 30))

        self.create_label(
            sidebar,
            "READER MENU",
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
            ("booklist", "Browse Books"),
            ("borrow", "Borrow Books"),
            ("booklist", "Return Books"),
            ("history", "Borrowing History"),
            ("history", "Borrow Status"),
            ("history", "Return History"),
            ("history", "Notifications"),
            ("statistics", "My Fines"),
            ("management", "My Profile")
        ]

        menu = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", height=180)
        menu.pack(fill="both", expand=True, padx=(7, 3))

        for icon_name, name in menus:
            active = name == "Dashboard"
            icon = self.load_icon(icon_name, active)

            if icon:
                self.menu_icons[name] = icon

            button = ctk.CTkButton(
                menu,
                text=name,
                image=icon,
                compound="left",
                anchor="w",
                height=44,
                corner_radius=7,
                fg_color=(
                    "#D8EED3"
                    if active else
                    "transparent"
                ),
                hover_color="#497A69",
                text_color=(
                    BG_GREEN if active else WHITE
                ),
                font=(
                    "Segoe UI",
                    13,
                    "bold" if active else "normal"
                ),
                command=lambda n=name: self.navigate(n)
            )
            button.pack(
                fill="x",
                padx=15,
                pady=4
            )

        help_box = ctk.CTkFrame(
            sidebar,
            fg_color="#416E5D",
            corner_radius=9
        )
        help_box.pack(
            fill="x",
            padx=15,
            pady=(8, 12)
        )

        self.create_label(
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

        self.create_label(
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
            sidebar,
            text="Reader Account",
            anchor="w",
            height=44,
            fg_color="transparent",
            hover_color="#497A69",
            text_color=WHITE,
            font=("Segoe UI", 13, "bold"),
            command=lambda: self.navigate("My Profile")
        ).pack(
            fill="x",
            padx=15,
            pady=(0, 5)
        )

        ctk.CTkButton(
            sidebar,
            text="Logout",
            anchor="w",
            height=40,
            fg_color="transparent",
            hover_color="#497A69",
            text_color=WHITE,
            command=self.logout
        ).pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

    # ---------------- HEADER ----------------

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

        left = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )
        left.pack(side="left")

        self.create_label(
            left,
            "Reader Dashboard",
            26,
            bold=True
        ).pack(anchor="w")

        self.create_label(
            left,
            "Welcome to your library account",
            13,
            MUTED
        ).pack(anchor="w", pady=(4, 0))

        self.create_label(
            header,
            "Library Management System",
            12,
            MUTED
        ).pack(side="right")

    # ---------------- STATISTICS ----------------

    def build_statistics(self):
        container = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        container.pack(
            fill="x",
            padx=25,
            pady=(0, 20)
        )

        statistics = [
            ("Currently Borrowed", sum(row["quantity"] - row["returned_quantity"] for row in self.current_borrowings), "Maximum 3 books"),
            ("Pending Requests", sum(row["status"] == "Pending" for row in self.transactions), "Awaiting approval"),
            ("Books Returned", sum(row["returned_quantity"] for row in self.transactions), "Completed returns"),
            ("Overdue Books", sum(row["quantity"] - row["returned_quantity"] for row in self.current_borrowings if row["status"] == "Overdue"), "Check your due dates")
        ]

        for i, (title, value, description) in enumerate(statistics):
            container.grid_columnconfigure(
                i,
                weight=1,
                uniform="stats"
            )

            card = self.create_panel(container)
            card.grid(
                row=0,
                column=i,
                sticky="nsew",
                padx=(0, 10) if i < 3 else 0
            )

            self.create_label(
                card,
                title,
                13,
                MUTED,
                True
            ).pack(
                anchor="w",
                padx=16,
                pady=(17, 8)
            )

            self.create_label(
                card,
                value,
                32,
                bold=True
            ).pack(
                anchor="w",
                padx=16
            )

            self.create_label(
                card,
                description,
                12,
                MUTED
            ).pack(
                anchor="w",
                padx=16,
                pady=(4, 18)
            )

    # ---------------- QUICK ACTIONS ----------------

    def build_quick_actions(self):
        panel = self.create_panel(self.content)
        panel.pack(
            fill="x",
            padx=25,
            pady=(0, 20)
        )

        self.create_section_title(
            panel,
            "Quick Actions",
            "Access frequently used library functions"
        )

        actions = [
            ("Browse Books", "Browse Books"),
            ("Borrow a Book", "Borrow Books"),
            ("Return a Book", "Return Books"),
            ("View History", "Borrowing History")
        ]

        action_frame = ctk.CTkFrame(
            panel,
            fg_color="transparent"
        )
        action_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        for i, (label, destination) in enumerate(actions):
            action_frame.grid_columnconfigure(
                i,
                weight=1,
                uniform="actions"
            )

            ctk.CTkButton(
                action_frame,
                text=label,
                height=46,
                corner_radius=8,
                fg_color=GREEN,
                hover_color="#126A43",
                text_color=WHITE,
                font=("Segoe UI", 13, "bold"),
                command=lambda d=destination: self.navigate(d)
            ).grid(
                row=0,
                column=i,
                sticky="ew",
                padx=(0, 10) if i < 3 else 0
            )

    # ---------------- CURRENT BORROWINGS ----------------

    def build_current_borrowings(self):
        panel = self.create_panel(self.content)
        panel.pack(
            fill="x",
            padx=25,
            pady=(0, 20)
        )

        self.create_section_title(
            panel,
            "My Current Borrowings",
            "Books you are currently borrowing"
        )

        table = ctk.CTkFrame(
            panel,
            fg_color="transparent"
        )
        table.pack(
            fill="x",
            padx=20,
            pady=(0, 18)
        )

        columns = [
            "Book Title",
            "Borrow Date",
            "Due Date",
            "Status"
        ]

        for i, heading in enumerate(columns):
            table.grid_columnconfigure(
                i,
                weight=1,
                uniform="borrowings"
            )

            self.create_label(
                table,
                heading,
                12,
                MUTED,
                True,
                anchor="w"
            ).grid(
                row=0,
                column=i,
                sticky="ew",
                padx=8,
                pady=(10, 14)
            )

        ctk.CTkFrame(
            table,
            height=1,
            fg_color=BORDER
        ).grid(
            row=1,
            column=0,
            columnspan=4,
            sticky="ew"
        )

        for index, record in enumerate(self.current_borrowings[:5], start=2):
            values = (record["book_title"], record["borrowed_date"], record["due_date"], record["status"])
            for column, value in enumerate(values):
                self.create_label(table, value, anchor="w", wraplength=200).grid(
                    row=index, column=column, sticky="ew", padx=8, pady=6
                )

        if not self.current_borrowings:
            self.create_label(
                table,
                "No borrowing records available",
                13,
                MUTED,
                height=155
            ).grid(
                row=2,
                column=0,
                columnspan=4,
                sticky="nsew"
            )

        footer = ctk.CTkFrame(
            panel,
            fg_color="transparent"
        )
        footer.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        ctk.CTkButton(
            footer,
            text="View All Borrowings",
            width=170,
            height=38,
            fg_color=GREEN,
            hover_color="#126A43",
            command=lambda: self.navigate("Borrowing History")
        ).pack(side="right")

    # ---------------- REMINDERS ----------------

    def build_reminders(self):
        panel = self.create_panel(self.content)
        panel.pack(
            fill="x",
            padx=25,
            pady=(0, 25)
        )

        self.create_section_title(
            panel,
            "Library Reminders",
            "Important borrowing information"
        )

        reminders = [
            "You can borrow up to 3 books at the same time.",
            "Borrowing requests require administrator approval.",
            "Check your due dates to avoid overdue fines.",
            "Overdue fines are calculated at 2,000 VND per book per day."
        ]

        for reminder in reminders:
            row = ctk.CTkFrame(
                panel,
                fg_color="#F6F9F7",
                corner_radius=7
            )
            row.pack(
                fill="x",
                padx=20,
                pady=5
            )

            self.create_label(
                row,
                reminder,
                13,
                TEXT,
                wraplength=850,
                justify="left"
            ).pack(
                anchor="w",
                padx=15,
                pady=11
            )

        ctk.CTkFrame(
            panel,
            fg_color="transparent",
            height=12
        ).pack()

    # ---------------- NAVIGATION ----------------

    def navigate(self, page_name):
        if page_name == "Dashboard":
            return

        if self.on_navigate:
            self.on_navigate(page_name)

    def logout(self):
        if self.on_logout:
            self.on_logout()
0

import tkinter as tk
from pathlib import Path
import customtkinter as ctk
from PIL import Image

from app.config.theme import BG_GREEN, WHITE
PAGE_BG = "#F5F7F8"
TEXT = "#20312C"
MUTED = "#788A84"
BORDER = "#E1E9E5"
GREEN = "#168452"

class AdminDashboardView(ctk.CTkFrame):
    def __init__(self, master, on_navigate=None, on_logout=None):
        super().__init__(master, fg_color=PAGE_BG)

        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.logo_image = None
        self.menu_icons = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()

        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color=PAGE_BG,
            corner_radius=0
        )
        self.content.grid(row=0, column=1, sticky="nsew")

        self.build_header()
        self.build_statistics()
        self.build_charts()
        self.build_tables()

    # ================= SIDEBAR =================

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=235,
            fg_color=BG_GREEN,
            corner_radius=0
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Logo
        logo_path = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "logo.png"
        )

        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
            self.logo_image = ctk.CTkImage(
                light_image=logo,
                dark_image=logo,
                size=(75, 75)
            )

            ctk.CTkLabel(
                sidebar,
                image=self.logo_image,
                text=""
            ).pack(pady=(22, 6))

        ctk.CTkLabel(
            sidebar,
            text="Library",
            font=("Segoe UI", 14),
            text_color="#D9E9E0",
            height=22
        ).pack()

        ctk.CTkLabel(
            sidebar,
            text="Library System",
            font=("Segoe UI", 23, "bold"),
            text_color=WHITE,
            height=32
        ).pack(pady=(0, 30))

        ctk.CTkLabel(
            sidebar,
            text="MANAGEMENT MENU",
            font=("Segoe UI", 11, "bold"),
            text_color="#B9D5C9"
        ).pack(anchor="w", padx=22, pady=(0, 12))

        # Menu sử dụng 6 icon PNG
        menus = [
            ("dashboard", "Dashboard"),
            ("borrow", "Borrow Books"),
            ("booklist", "Booklist"),
            ("history", "History"),
            ("management", "Book Management"),
            ("statistics", "Statistics"),
        ]

        icons_dir = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "icons"
        )

        for icon_name, name in menus:
            active = name == "Dashboard"
            icon_path = icons_dir / f"{icon_name}.png"
            icon_image = None

            if icon_path.exists():
                original = Image.open(icon_path).convert("RGBA")
                alpha = original.getchannel("A")

                icon_color = (
                    (47, 91, 75) if active
                    else (255, 255, 255)
                )

                colored = Image.new(
                    "RGBA",
                    original.size,
                    (*icon_color, 255)
                )
                colored.putalpha(alpha)

                icon_image = ctk.CTkImage(
                    light_image=colored,
                    dark_image=colored,
                    size=(20, 20)
                )

                self.menu_icons[name] = icon_image

            ctk.CTkButton(
                sidebar,
                text=name,
                image=icon_image,
                compound="left",
                anchor="w",
                height=44,
                corner_radius=7,
                fg_color="#D8EED3" if active else "transparent",
                hover_color="#497A69",
                text_color=BG_GREEN if active else WHITE,
                font=(
                    "Segoe UI",
                    13,
                    "bold" if active else "normal"
                ),
                command=lambda n=name: self.navigate(n)
            ).pack(fill="x", padx=15, pady=4)

        # Đẩy phần dưới xuống cuối Sidebar
        ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        ).pack(fill="both", expand=True)

        help_box = ctk.CTkFrame(
            sidebar,
            fg_color="#416E5D",
            corner_radius=9
        )
        help_box.pack(fill="x", padx=15, pady=(8, 12))

        ctk.CTkLabel(
            help_box,
            text="Need help?",
            font=("Segoe UI", 14, "bold"),
            text_color=WHITE
        ).pack(anchor="w", padx=14, pady=(12, 3))

        ctk.CTkLabel(
            help_box,
            text="Contact the library support team.",
            font=("Segoe UI", 11),
            text_color="#D9E9E0",
            wraplength=180,
            justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 12))

        ctk.CTkButton(
            sidebar,
            text="Administrator",
            anchor="w",
            height=44,
            fg_color="transparent",
            hover_color="#497A69",
            text_color=WHITE,
            font=("Segoe UI", 13, "bold"),
            command=self.logout
        ).pack(fill="x", padx=15, pady=(0, 16))

    # ================= HEADER =================

    def build_header(self):
        header = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        header.pack(fill="x", padx=25, pady=(24, 20))

        left = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )
        left.pack(side="left")

        ctk.CTkLabel(
            left,
            text="Dashboard - System Overview",
            font=("Segoe UI", 25, "bold"),
            text_color=TEXT
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="Overview of library activities",
            font=("Segoe UI", 13),
            text_color=MUTED
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            header,
            text="Library Management System",
            font=("Segoe UI", 12),
            text_color=MUTED
        ).pack(side="right", padx=8)

    # ================= STATISTICS =================

    def build_statistics(self):
        row = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        row.pack(fill="x", padx=25, pady=(0, 20))

        for i in range(4):
            row.grid_columnconfigure(
                i,
                weight=1,
                uniform="stats"
            )

        # Không sử dụng icon trong 4 ô thống kê
        cards = [
            ("Total Borrowings", GREEN),
            ("Books Borrowed", "#388CC7"),
            ("Active Readers", GREEN),
            ("Overdue Books", "#D95858"),
        ]

        for i, (title, color) in enumerate(cards):
            card = self.create_panel(row)
            card.grid(
                row=0,
                column=i,
                sticky="nsew",
                padx=(0, 10) if i < 3 else 0
            )

            top = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )
            top.pack(fill="x", padx=16, pady=(15, 5))

            ctk.CTkLabel(
                top,
                text=title,
                font=("Segoe UI", 13, "bold"),
                text_color=MUTED
            ).pack(side="left")

            ctk.CTkLabel(
                card,
                text="—",
                font=("Segoe UI", 32, "bold"),
                text_color=TEXT
            ).pack(anchor="w", padx=16)

            ctk.CTkLabel(
                card,
                text="No data available",
                font=("Segoe UI", 12),
                text_color=MUTED
            ).pack(
                anchor="w",
                padx=16,
                pady=(0, 18)
            )

    # ================= CHARTS =================

    def build_charts(self):
        row = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        row.pack(fill="x", padx=25, pady=(0, 20))
        row.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="charts"
        )

        # Biểu đồ mượn sách
        left = self.create_panel(row)
        left.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 9)
        )
        self.panel_title(
            left,
            "Borrowings by Month",
            "Total borrowings"
        )

        line_canvas = tk.Canvas(
            left,
            height=250,
            bg=WHITE,
            highlightthickness=0
        )
        line_canvas.pack(
            fill="x",
            padx=16,
            pady=(0, 15)
        )
        line_canvas.bind(
            "<Configure>",
            lambda event: self.draw_line_placeholder(line_canvas)
        )

        # Biểu đồ trạng thái sách
        right = self.create_panel(row)
        right.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(9, 0)
        )
        self.panel_title(
            right,
            "Book Status",
            "Distribution of library books"
        )

        donut_canvas = tk.Canvas(
            right,
            height=250,
            bg=WHITE,
            highlightthickness=0
        )
        donut_canvas.pack(
            fill="x",
            padx=16,
            pady=(0, 15)
        )
        donut_canvas.bind(
            "<Configure>",
            lambda event: self.draw_donut_placeholder(donut_canvas)
        )

    def draw_line_placeholder(self, canvas):
        canvas.delete("all")

        w = canvas.winfo_width()
        h = canvas.winfo_height()

        if w < 80:
            return

        left, right = 38, w - 15
        top, bottom = 20, h - 35

        for i in range(5):
            y = top + i * (bottom - top) / 4
            canvas.create_line(
                left,
                y,
                right,
                y,
                fill="#E8EFEB",
                dash=(3, 3)
            )

        months = [
            "Jan", "Feb", "Mar", "Apr",
            "May", "Jun", "Jul", "Aug",
            "Sep", "Oct", "Nov", "Dec"
        ]

        for i, month in enumerate(months):
            x = left + i * (right - left) / 11
            canvas.create_text(
                x,
                bottom + 17,
                text=month,
                fill=MUTED,
                font=("Segoe UI", 10)
            )

        canvas.create_text(
            w / 2,
            h / 2,
            text="No borrowing data available",
            fill=MUTED,
            font=("Segoe UI", 13)
        )

    def draw_donut_placeholder(self, canvas):
        canvas.delete("all")

        w = canvas.winfo_width()
        h = canvas.winfo_height()

        if w < 80:
            return

        cx, cy = w * 0.32, h * 0.51
        radius = min(85, h * 0.38, w * 0.23)

        canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            fill="#EDF2EF",
            outline=""
        )

        inner = radius * 0.64
        canvas.create_oval(
            cx - inner,
            cy - inner,
            cx + inner,
            cy + inner,
            fill=WHITE,
            outline=""
        )

        canvas.create_text(
            cx,
            cy - 7,
            text="—",
            font=("Segoe UI", 28, "bold"),
            fill=TEXT
        )

        canvas.create_text(
            cx,
            cy + 20,
            text="Total Books",
            font=("Segoe UI", 11),
            fill=MUTED
        )

        label_x = w * 0.61

        for y, label in [
            (cy - 32, "Available"),
            (cy + 34, "Borrowed")
        ]:
            canvas.create_oval(
                label_x,
                y - 5,
                label_x + 10,
                y + 5,
                fill="#D5E2DA",
                outline=""
            )

            canvas.create_text(
                label_x + 18,
                y,
                text=f"{label}: —",
                anchor="w",
                font=("Segoe UI", 12),
                fill=MUTED
            )

    # ================= TABLES =================

    def build_tables(self):
        row = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        row.pack(fill="x", padx=25, pady=(0, 25))
        row.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="tables"
        )

        recent = self.create_panel(row)
        recent.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 9)
        )
        self.panel_title(
            recent,
            "Recent Borrowings"
        )
        self.empty_table(
            recent,
            ["Reader", "Book Title", "Date", "Status"]
        )

        overdue = self.create_panel(row)
        overdue.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(9, 0)
        )
        self.panel_title(
            overdue,
            "Overdue Books"
        )
        self.empty_table(
            overdue,
            ["Reader", "Book Title", "Overdue", "Fine"]
        )

    def empty_table(self, parent, headings):
        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        frame.pack(
            fill="x",
            padx=14,
            pady=(0, 14)
        )

        for i in range(len(headings)):
            frame.grid_columnconfigure(
                i,
                weight=1,
                uniform="table"
            )

        for i, heading in enumerate(headings):
            ctk.CTkLabel(
                frame,
                text=heading,
                font=("Segoe UI", 12, "bold"),
                text_color=MUTED,
                anchor="w"
            ).grid(
                row=0,
                column=i,
                sticky="ew",
                padx=5,
                pady=(7, 12)
            )

        ctk.CTkFrame(
            frame,
            height=1,
            fg_color=BORDER
        ).grid(
            row=1,
            column=0,
            columnspan=len(headings),
            sticky="ew"
        )

        ctk.CTkLabel(
            frame,
            text="No records to display",
            font=("Segoe UI", 13),
            text_color=MUTED,
            height=190
        ).grid(
            row=2,
            column=0,
            columnspan=len(headings),
            sticky="nsew"
        )

    # ================= COMMON COMPONENTS =================

    def create_panel(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color=WHITE,
            corner_radius=11,
            border_width=1,
            border_color=BORDER
        )

    def panel_title(self, parent, title, subtitle=None):
        header = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        header.pack(
            fill="x",
            padx=17,
            pady=(15, 10)
        )

        ctk.CTkLabel(
            header,
            text=title,
            font=("Segoe UI", 16, "bold"),
            text_color=TEXT
        ).pack(anchor="w")

        if subtitle:
            ctk.CTkLabel(
                header,
                text=subtitle,
                font=("Segoe UI", 12),
                text_color=MUTED
            ).pack(
                anchor="w",
                pady=(2, 0)
            )

    # ================= UI CALLBACKS =================

    def navigate(self, name):
        if name != "Dashboard" and self.on_navigate:
            self.on_navigate(name)

    def logout(self):
        if self.on_logout:
            self.on_logout()

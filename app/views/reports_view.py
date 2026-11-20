
import customtkinter as ctk
from pathlib import Path
from PIL import Image, ImageDraw
from tkinter import messagebox

from collections import Counter
from datetime import date

from app.views.borrowing_history_view import DatePicker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.config.theme import WHITE

BG = "#F5F7F8"
TEXT = "#20312C"
MUTED = "#788A84"
BORDER = "#E1E9E5"

GREEN = "#168452"
LIGHT_GREEN = "#70D998"

SIDEBAR_BG = "#2D6857"
SIDEBAR_ITEM = "#397461"

BLUE = "#4387F5"
RED = "#F45B69"

class ReportsView(ctk.CTkFrame):
    """Statistics and Reports UI."""

    def __init__(
        self,
        master,
        on_navigate=None,
        on_logout=None,
        on_export_pdf=None,
        on_export_excel=None,
        catalog=None,
        readers=None,
        status=None,
        transactions=None,
        report_types=None,
        on_preview=None,
        on_export_csv=None
    ):
        super().__init__(
            master,
            fg_color=BG
        )

        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.on_export_pdf = on_export_pdf
        self.on_export_excel = on_export_excel
        self.report_types = report_types or []
        self.on_preview = on_preview
        self.on_export_csv = on_export_csv

        self.assets = (
            Path(__file__).resolve().parents[1]
            / "assets"
        )

        self.logo_image = None
        self.avatar_image = None
        self.menu_icons = {}
        self.chart_canvases = []
        self.catalog = catalog or {}
        self.readers = readers or {}
        self.status = status or {}
        self.transactions = transactions or []

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
            sticky="nsew",
            padx=(10, 15),
            pady=10
        )

        self.build_header()
        self.build_statistics()
        for label, value in {
            "Total books": self.catalog.get("total_quantity"),
            "Books on loan": self.status.get("currently_borrowed"),
            "Active readers": self.readers.get("active_readers"),
            "Overdue books": self.status.get("overdue"),
        }.items():
            if value is not None:
                self.stat_labels[label].configure(text=value)
        self.build_report_period()
        self.from_date.set_date(date.today().replace(day=1))
        self.build_charts()

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

    # ==========================================
    # LOAD PNG ICON
    # ==========================================

    def load_icon(
        self,
        filename,
        active=False
    ):
        path = (
            self.assets
            / "icons"
            / f"{filename}.png"
        )

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

        tinted.putalpha(
            original.getchannel("A")
        )

        return ctk.CTkImage(
            light_image=tinted,
            dark_image=tinted,
            size=(16, 16)
        )

    # ==========================================
    # SIDEBAR
    # ==========================================

    def build_sidebar(self):

        side = ctk.CTkFrame(
            self,
            width=190,
            fg_color=SIDEBAR_BG,
            corner_radius=16
        )

        side.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(15, 0),
            pady=15
        )

        side.grid_propagate(False)

        # LOGO
        logo_box = ctk.CTkFrame(
            side,
            fg_color="transparent"
        )

        logo_box.pack(
            fill="x",
            pady=(22, 38)
        )

        logo_path = (
            self.assets / "logo.png"
        )

        if logo_path.exists():

            with Image.open(logo_path) as source:
                logo = source.convert("RGBA").copy()

            self.logo_image = ctk.CTkImage(
                light_image=logo,
                dark_image=logo,
                size=(36, 36)
            )

            ctk.CTkLabel(
                logo_box,
                text="",
                image=self.logo_image
            ).pack()

        else:

            ctk.CTkLabel(
                logo_box,
                text="▣",
                width=36,
                height=36,
                fg_color=LIGHT_GREEN,
                text_color=SIDEBAR_BG,
                corner_radius=18,
                font=("Segoe UI", 17)
            ).pack()

        self.label(
            logo_box,
            "Library",
            14,
            WHITE,
            True
        ).pack(
            pady=(8, 0)
        )

        self.label(
            logo_box,
            "Library System",
            10,
            "#C5DCD4"
        ).pack(
            pady=(1, 0)
        )

        # MENU
        menus = [
            ("dashboard", "Dashboard"),
            ("borrow", "Borrow books"),
            ("booklist", "Return books"),
            ("history", "Borrowing history"),
            ("management", "Book management"),
            ("statistics", "Statistics")
        ]

        for filename, title in menus:

            active = (
                title == "Statistics"
            )

            icon = self.load_icon(
                filename,
                active
            )

            if icon is not None:
                self.menu_icons[title] = icon

            row = ctk.CTkFrame(
                side,
                height=38,
                fg_color=(
                    LIGHT_GREEN
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
                    (
                        "bold"
                        if active
                        else "normal"
                    )
                ),
                command=lambda page=title: (
                    self.navigate(page)
                )
            ).pack(
                fill="both",
                expand=True,
                padx=4
            )

            if active:
                self.label(
                    row,
                    "●",
                    10,
                    "#397461"
                ).place(
                    relx=0.95,
                    rely=0.5,
                    anchor="center"
                )

        # SPACER
        ctk.CTkFrame(
            side,
            fg_color="transparent"
        ).pack(
            fill="both",
            expand=True
        )

        # FOOTER
        footer = ctk.CTkFrame(
            side,
            fg_color="transparent"
        )

        footer.pack(
            fill="x",
            pady=(0, 20)
        )

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
        ).pack(
            pady=(3, 5)
        )

        avatar_pil = Image.new(
            "RGBA",
            (96, 96),
            (0, 0, 0, 0)
        )

        ImageDraw.Draw(
            avatar_pil
        ).ellipse(
            (0, 0, 95, 95),
            fill=LIGHT_GREEN
        )

        self.avatar_image = ctk.CTkImage(
            light_image=avatar_pil,
            dark_image=avatar_pil,
            size=(32, 32)
        )

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
            image=self.avatar_image,
            compound="center",
            width=32,
            height=32,
            text_color="#326A50",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack()
    def build_header(self):

        header = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=25,
            pady=(22, 18)
        )

        self.label(
            header,
            "Statistics and reports",
            26,
            bold=True
        ).pack(anchor="w")

        self.label(
            header,
            "Analyze and report on library activities",
            13,
            MUTED
        ).pack(
            anchor="w",
            pady=(4, 0)
        )
    def build_statistics(self):

        section = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        section.pack(
            fill="x",
            padx=25,
            pady=(0, 18)
        )

        for i in range(4):
            section.grid_columnconfigure(
                i,
                weight=1,
                uniform="statistics"
            )

        cards = [
            ("Total books", "#F0F9F3"),
            ("Books on loan", "#EFF4FF"),
            ("Active readers", "#F0FAF4"),
            ("Overdue books", "#FFF3F4")
        ]

        self.stat_labels = {}

        for i, (
            title,
            background
        ) in enumerate(cards):

            card = ctk.CTkFrame(
                section,
                fg_color=background,
                corner_radius=10,
                border_width=1,
                border_color=BORDER
            )

            card.grid(
                row=0,
                column=i,
                sticky="nsew",
                padx=(
                    0 if i == 0 else 6,
                    0 if i == 3 else 6
                )
            )

            self.label(
                card,
                title,
                12,
                TEXT,
                True
            ).pack(
                anchor="w",
                padx=16,
                pady=(14, 5)
            )

            value_label = self.label(
                card,
                "—",
                28,
                TEXT,
                True
            )

            value_label.pack(
                anchor="w",
                padx=16
            )

            self.stat_labels[
                title
            ] = value_label

    def build_report_period(self):

        card = self.panel(
            self.content
        )

        card.pack(
            fill="x",
            padx=25,
            pady=(0, 18)
        )

        self.label(
            card,
            "Select report period",
            15,
            bold=True
        ).pack(
            anchor="w",
            padx=18,
            pady=(14, 2)
        )

        self.label(
            card,
            "View statistics and export reports for a selected period",
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

        controls.grid_columnconfigure(
            1,
            weight=1
        )

        # FROM DATE
        from_box = ctk.CTkFrame(
            controls,
            fg_color="transparent"
        )

        from_box.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 12)
        )

        self.label(
            from_box,
            "From date",
            12,
            bold=True
        ).pack(
            anchor="w",
            pady=(0, 5)
        )

        self.from_date = (
            self.create_date_picker(
                from_box
            )
        )

        # TO DATE
        to_box = ctk.CTkFrame(
            controls,
            fg_color="transparent"
        )

        to_box.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 12)
        )

        self.label(
            to_box,
            "To date",
            12,
            bold=True
        ).pack(
            anchor="w",
            pady=(0, 5)
        )

        self.to_date = (
            self.create_date_picker(
                to_box
            )
        )

        if self.report_types:
            report_actions = ctk.CTkFrame(card, fg_color="transparent")
            report_actions.pack(fill="x", padx=18, pady=(0, 8))
            self.report_type = ctk.CTkOptionMenu(report_actions, values=self.report_types, width=240)
            self.report_type.pack(side="left", padx=(0, 8))
            ctk.CTkButton(report_actions, text="View report", command=self.preview_report).pack(side="left", padx=8)
            ctk.CTkButton(report_actions, text="Export CSV", command=self.export_csv).pack(side="left")
            self.report_preview = ctk.CTkTextbox(card, height=145, wrap="word", state="disabled")
            self.report_preview.pack(fill="x", padx=18, pady=(0, 16))

        # EXPORT BUTTONS
        export_box = ctk.CTkFrame(
            controls,
            fg_color="transparent"
        )

        export_box.grid(
            row=0,
            column=2,
            sticky="se"
        )

        ctk.CTkButton(
            export_box,
            text="Export PDF",
            width=105,
            height=38,
            fg_color="#EDF2EF",
            text_color=MUTED,
            command=self.export_pdf
        ).pack(
            side="left",
            padx=(0, 8)
        )

        ctk.CTkButton(
            export_box,
            text="Export Excel",
            width=110,
            height=38,
            fg_color=GREEN,
            command=self.export_excel
        ).pack(
            side="left"
        )

    # ==========================================
    # CALENDAR DATE PICKER
    # ==========================================

    def create_date_picker(
        self,
        parent
    ):

        picker = DatePicker(parent)
        picker.pack(fill="x")
        picker.set_date(date.today())

        return picker

    # ==========================================
    # CHARTS
    # ==========================================

    def build_charts(self):

        charts = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        charts.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 25)
        )

        charts.grid_columnconfigure(
            0,
            weight=1,
            uniform="charts"
        )

        charts.grid_columnconfigure(
            1,
            weight=1,
            uniform="charts"
        )

        definitions = [
            (
                0,
                0,
                "Monthly loans and returns",
                "Monthly activity throughout the year",
                "line"
            ),
            (
                0,
                1,
                "Most borrowed books",
                "8 most popular titles",
                "bar"
            ),
            (
                1,
                0,
                "Overdue book breakdown",
                "Distribution by number of days overdue",
                "overdue"
            ),
            (
                1,
                1,
                "Books by category",
                "Total copies across library categories",
                "category"
            )
        ]

        for (
            row,
            column,
            title,
            subtitle,
            chart_type
        ) in definitions:

            self.create_chart_card(
                charts,
                row,
                column,
                title,
                subtitle,
                chart_type
            )

    # ==========================================
    # CREATE CHART CARD
    # ==========================================

    def create_chart_card(
        self,
        parent,
        row,
        column,
        title,
        subtitle,
        chart_type
    ):

        card = self.panel(parent)

        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=(
                (0, 8)
                if column == 0
                else (8, 0)
            ),
            pady=(0, 16)
        )

        self.label(
            card,
            title,
            15,
            bold=True
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 2)
        )

        self.label(
            card,
            subtitle,
            12,
            MUTED
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 8)
        )

        figure = Figure(
            figsize=(5.4, 2.8),
            dpi=100,
            facecolor=WHITE
        )

        ax = figure.add_subplot(
            111
        )

        ax.set_facecolor(WHITE)

        data = self.chart_data(chart_type)
        if chart_type == "line" and data:
            months, loans, returns = data
            ax.plot(months, [float(value) for value in loans], label="Loans", color=GREEN)
            ax.plot(months, [float(value) for value in returns], label="Returns", color=BLUE)
            ax.legend()
            ax.tick_params(axis="x", labelsize=8)
        elif chart_type == "bar" and data:
            labels, counts = zip(*reversed(data))
            ax.barh([str(label)[:30] for label in labels], [float(count) for count in counts], color=GREEN)
            ax.tick_params(axis="y", labelsize=8)
        elif data:
            labels, counts = zip(*data)
            ax.pie([float(count) for count in counts], labels=labels, textprops={"fontsize": 8})
        else:
            ax.axis("off")
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", color=MUTED)

        figure.tight_layout(
            pad=1.5
        )

        canvas = FigureCanvasTkAgg(
            figure,
            master=card
        )

        canvas.draw()

        widget = (
            canvas.get_tk_widget()
        )

        widget.configure(
            bg=WHITE,
            highlightthickness=0
        )

        widget.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12)
        )

        self.chart_canvases.append(
            canvas
        )
    def chart_data(self, chart_type):
        if chart_type == "category":
            return [
                (item["category"] or "Uncategorized", item["total_quantity"])
                for item in self.catalog.get("by_category", []) if item["total_quantity"]
            ]

        if chart_type == "bar":
            titles = Counter()
            for record in self.transactions:
                if record["status"] not in ("Pending", "Rejected"):
                    for book in record["books"]:
                        titles[book["title"]] += book["quantity"]
            return titles.most_common(8)

        if chart_type == "overdue":
            groups = Counter()
            for record in self.transactions:
                if record["status"] == "Overdue":
                    due = DatePicker.parse_date(record["due_date"])
                    if due is not None:
                        days = (date.today() - due).days
                        label = "1–7 days" if days <= 7 else "8–30 days" if days <= 30 else "31+ days"
                        groups[label] += record["quantity"] - record["returned_quantity"]
            return [(label, count) for label, count in groups.items() if count]

        year = str(date.today().year)
        loans = Counter(
            record["borrowed_date"][:7] for record in self.transactions
            if record["borrowed_date"] and record["status"] not in ("Pending", "Rejected")
        )
        returns = Counter(
            record["returned_date"][:7] for record in self.transactions if record["returned_date"]
        )
        if not any(month.startswith(year) for month in loans.keys() | returns.keys()):
            return None
        months = [f"{year}-{month:02}" for month in range(1, 13)]
        return (
            [date.fromisoformat(month + "-01").strftime("%b") for month in months],
            [loans[month] for month in months],
            [returns[month] for month in months],
        )

    def report_period(self):

        start = (
            DatePicker.parse_date(self.from_date.get())
        )

        end = (
            DatePicker.parse_date(self.to_date.get())
        )

        if start is None or end is None:
            messagebox.showerror("Invalid report period", "Enter both dates as DD/MM/YYYY.", parent=self)
            return None

        if start > end:

            messagebox.showerror(
                "Invalid report period",
                "From date must not be after To date."
            )

            return None

        return start, end
    def selected_report(self):
        report_type = self.report_type.get()
        period = self.report_period() if report_type == "Borrowing and returns" else (None, None)
        return (report_type, *period) if period is not None else None

    def preview_report(self):
        selected = self.selected_report()
        if selected is None:
            return
        report = self.on_preview(*selected)
        if report is None:
            return
        lines = []
        for key, value in report.items():
            label = key.replace("_", " ").capitalize()
            if isinstance(value, list):
                lines.append(label)
                lines.extend(
                    "  " + " | ".join(f"{field.replace('_', ' ')}: {cell}" for field, cell in row.items())
                    for row in value
                )
                if not value:
                    lines.append("  No matching records")
            else:
                lines.append(f"{label}: {value}")
        self.report_preview.configure(state="normal")
        self.report_preview.delete("1.0", "end")
        self.report_preview.insert("1.0", "\n".join(lines) or "No matching records")
        self.report_preview.configure(state="disabled")

    def export_csv(self):
        selected = self.selected_report()
        if selected is not None:
            self.on_export_csv(*selected)

    def export_pdf(self):

        period = self.report_period()

        if period is None:
            return

        if self.on_export_pdf is not None:

            self.on_export_pdf(
                *period
            )

        else:

            messagebox.showinfo(
                "Export PDF",
                "PDF export will be connected."
            )
    def export_excel(self):

        period = self.report_period()

        if period is None:
            return

        if self.on_export_excel is not None:

            self.on_export_excel(
                *period
            )

        else:

            messagebox.showinfo(
                "Export Excel",
                "Excel export will be connected."
            )

    def navigate(
        self,
        page_name
    ):

        if (
            page_name != "Statistics"
            and self.on_navigate
        ):
            self.on_navigate(
                page_name
            )

    def logout(self):

        if self.on_logout:
            self.on_logout()

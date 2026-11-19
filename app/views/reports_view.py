
import customtkinter as ctk
from pathlib import Path
from PIL import Image, ImageDraw
from tkinter import messagebox

from tkcalendar import DateEntry
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle

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
        on_export_excel=None
    ):
        super().__init__(
            master,
            fg_color=BG
        )

        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.on_export_pdf = on_export_pdf
        self.on_export_excel = on_export_excel

        self.assets = (
            Path(__file__).resolve().parents[1]
            / "assets"
        )

        self.logo_image = None
        self.avatar_image = None
        self.menu_icons = {}
        self.chart_canvases = []

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
        self.build_report_period()
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
            ("Active borrowers", "#F0FAF4"),
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

            self.label(
                card,
                "No data available",
                11,
                MUTED
            ).pack(
                anchor="w",
                padx=16,
                pady=(4, 15)
            )
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

        picker = DateEntry(
            parent,
            date_pattern="dd/mm/yyyy",
            font=("Segoe UI", 12),
            background=GREEN,
            foreground="white",
            headersbackground=GREEN,
            headersforeground="white",
            selectbackground=GREEN,
            selectforeground="white",
            normalbackground="white",
            normalforeground=TEXT,
            weekendbackground="white",
            weekendforeground=TEXT,
            borderwidth=1,
            relief="solid",
            state="readonly"
        )

        picker.pack(
            fill="x",
            ipady=7
        )

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
                "Total books across library categories",
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

        # LINE CHART
        if chart_type == "line":

            months = [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec"
            ]

            ax.set_xlim(
                -0.5,
                11.5
            )

            ax.set_ylim(
                bottom=0
            )

            ax.set_xticks(
                range(12)
            )

            ax.set_xticklabels(
                months,
                fontsize=8
            )

            ax.set_yticks([])

            ax.grid(
                axis="y",
                color="#EDF0EF"
            )

            ax.set_axisbelow(True)

            ax.plot(
                [],
                [],
                color="#19C56B",
                linewidth=2,
                label="Loans"
            )

            ax.plot(
                [],
                [],
                color=BLUE,
                linewidth=2,
                label="Returns"
            )

            ax.legend(
                loc="lower center",
                bbox_to_anchor=(
                    0.5,
                    -0.27
                ),
                ncol=2,
                frameon=False,
                fontsize=8
            )

        # BAR CHART
        elif chart_type == "bar":

            ax.set_xlim(left=0)

            ax.set_ylim(
                -0.5,
                7.5
            )

            ax.set_xticks([])
            ax.set_yticks([])

            ax.grid(
                axis="x",
                color="#EDF0EF"
            )

            ax.set_axisbelow(True)

        # PIE CHART PLACEHOLDERS
        elif chart_type in (
            "overdue",
            "category"
        ):

            ax.set_xlim(
                -1.2,
                1.2
            )

            ax.set_ylim(
                -1.2,
                1.2
            )

            ax.set_aspect(
                "equal"
            )

            ax.axis("off")

            ax.add_patch(
                Circle(
                    (0, 0),
                    0.82,
                    fill=False,
                    edgecolor=BORDER,
                    linewidth=2
                )
            )

        if chart_type in (
            "line",
            "bar"
        ):

            for spine in (
                ax.spines.values()
            ):
                spine.set_visible(
                    False
                )

            ax.tick_params(
                axis="both",
                length=0,
                labelcolor=MUTED
            )

        # EMPTY STATE
        ax.text(
            0.5,
            0.5,
            "No data available",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=11,
            color=MUTED,
            bbox={
                "facecolor": WHITE,
                "edgecolor": "none",
                "alpha": 0.95
            }
        )

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
    def report_period(self):

        start = (
            self.from_date.get_date()
        )

        end = (
            self.to_date.get_date()
        )

        if start > end:

            messagebox.showerror(
                "Invalid report period",
                "From date must not be after To date."
            )

            return None

        return start, end
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

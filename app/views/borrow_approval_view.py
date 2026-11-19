
from pathlib import Path

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


class BorrowApprovalView(ctk.CTkFrame):
    """Borrowing approval UI - Librarian layout."""

    def __init__(
        self,
        master,
        on_navigate=None,
        on_approve=None,
        on_reject=None
    ):
        super().__init__(master, fg_color=BG)

        self.on_navigate = on_navigate
        self.on_approve = on_approve
        self.on_reject = on_reject

        self.requests = []
        self.filtered_requests = []
        self.selected_request = None

        self.assets = Path(__file__).resolve().parents[1] / "assets"
        self.images = []

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
        self.build_search_panel()
        self.build_requests_panel()
        self.build_details_panel()

    # ==========================================
    # COMMON COMPONENTS
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
        for child in frame.winfo_children():
            child.destroy()

    def load_icon(self, name, active=False):
        path = self.assets / "icons" / f"{name}.png"

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
        tinted.putalpha(original.getchannel("A"))

        result = ctk.CTkImage(
            light_image=tinted,
            dark_image=tinted,
            size=(19, 19)
        )

        self.images.append(result)
        return result

    # ==========================================
    # SIDEBAR - ORIGINAL LG DESIGN
    # ==========================================

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=235,
            fg_color=BG_GREEN,
            corner_radius=0
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
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

            ctk.CTkButton(
                sidebar,
                text=title,
                image=self.load_icon(icon_name, active),
                compound="left",
                anchor="w",
                height=43,
                corner_radius=7,
                fg_color=(
                    LIGHT_GREEN if active else "#3D7361"
                ),
                hover_color=(
                    "#8EE1AB" if active else "#4A806D"
                ),
                text_color=(
                    "#245A46" if active else WHITE
                ),
                font=(
                    "Segoe UI",
                    13,
                    "bold" if active else "normal"
                ),
                command=lambda page=title: self.navigate(page)
            ).pack(
                fill="x",
                padx=14,
                pady=4
            )

        # Keep profile at bottom
        ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        ).pack(fill="both", expand=True)

        # Original LG / Librarian / Library footer
        footer = ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        )
        footer.pack(
            fill="x",
            padx=18,
            pady=(0, 22)
        )

        ctk.CTkLabel(
            footer,
            text="LG",
            width=44,
            height=44,
            corner_radius=22,
            fg_color=LIGHT_GREEN,
            text_color="#245A46",
            font=("Segoe UI", 13, "bold")
        ).pack(side="left")

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

        self.label(
            user_info,
            "Librarian",
            13,
            WHITE,
            True,
            anchor="w"
        ).pack(fill="x")

        self.label(
            user_info,
            "Library",
            11,
            "#C6DCD3",
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

        self.label(
            header,
            "Borrowing approval",
            26,
            TEXT,
            True
        ).pack(anchor="w")

        self.label(
            header,
            "Review and approve book borrowing requests",
            13,
            MUTED
        ).pack(
            anchor="w",
            pady=(4, 0)
        )

    # ==========================================
    # SEARCH REQUESTS
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
            "Search requests",
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
            "Search by request ID, reader name or library card",
            12,
            MUTED
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 14)
        )

        row = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        row.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        self.search_entry = ctk.CTkEntry(
            row,
            height=40,
            placeholder_text="Enter request ID or reader name...",
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
            row,
            text="Search",
            width=110,
            height=40,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            command=self.search_requests
        ).pack(side="right")

        self.search_entry.bind(
            "<Return>",
            lambda event: self.search_requests()
        )

    # ==========================================
    # PENDING REQUESTS
    # ==========================================

    def build_requests_panel(self):
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
            pady=(18, 12)
        )

        self.label(
            heading,
            "Pending requests",
            16,
            TEXT,
            True
        ).pack(side="left")

        self.count_label = self.label(
            heading,
            "0 requests",
            12,
            MUTED
        )
        self.count_label.pack(side="right")

        self.requests_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        self.requests_frame.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        self.render_requests()

    def render_requests(self):
        self.clear(self.requests_frame)

        self.count_label.configure(
            text=f"{len(self.filtered_requests)} requests"
        )

        if not self.filtered_requests:
            empty = ctk.CTkFrame(
                self.requests_frame,
                fg_color="transparent",
                height=170
            )
            empty.pack(fill="x")
            empty.pack_propagate(False)

            self.label(
                empty,
                "▤",
                32,
                "#B5C5BE"
            ).place(
                relx=0.5,
                rely=0.35,
                anchor="center"
            )

            self.label(
                empty,
                "No pending requests found",
                14,
                MUTED
            ).place(
                relx=0.5,
                rely=0.65,
                anchor="center"
            )
            return

        for request in self.filtered_requests:
            row = ctk.CTkFrame(
                self.requests_frame,
                fg_color=PALE_GREEN,
                corner_radius=8,
                border_width=1,
                border_color="#D5EEDF"
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
                fill="x",
                expand=True,
                padx=15,
                pady=12
            )

            self.label(
                info,
                str(request.get("reader_name", "")),
                14,
                TEXT,
                True
            ).pack(anchor="w")

            self.label(
                info,
                (
                    f"Request: {request.get('id', '')}"
                    f"  |  Card: {request.get('card_number', '')}"
                ),
                12,
                MUTED
            ).pack(
                anchor="w",
                pady=(4, 0)
            )

            book_count = len(request.get("books", []))

            self.label(
                info,
                f"{book_count} book(s) requested",
                11,
                GREEN
            ).pack(
                anchor="w",
                pady=(4, 0)
            )

            ctk.CTkButton(
                row,
                text="View details",
                width=105,
                height=35,
                fg_color=GREEN,
                hover_color=DARK_GREEN,
                command=lambda r=request: self.select_request(r)
            ).pack(
                side="right",
                padx=15
            )

    # ==========================================
    # REQUEST DETAILS
    # ==========================================

    def build_details_panel(self):
        card = self.panel(self.content)
        card.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 25)
        )

        self.label(
            card,
            "Request details",
            16,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 14)
        )

        self.details_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
            height=180
        )
        self.details_frame.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 14)
        )

        actions = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        actions.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )

        self.reject_button = ctk.CTkButton(
            actions,
            text="Reject request",
            width=160,
            height=42,
            fg_color=WHITE,
            border_width=1,
            border_color=RED,
            text_color=RED,
            hover_color="#FFF0F1",
            state="disabled",
            command=self.reject_request
        )
        self.reject_button.pack(side="left")

        self.approve_button = ctk.CTkButton(
            actions,
            text="✓  Approve request",
            width=180,
            height=42,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            state="disabled",
            command=self.approve_request
        )
        self.approve_button.pack(side="right")

        self.render_details()

    def render_details(self):
        self.clear(self.details_frame)

        request = self.selected_request

        if request is None:
            self.label(
                self.details_frame,
                "Select a request to view details",
                13,
                MUTED
            ).pack(pady=55)

            self.approve_button.configure(state="disabled")
            self.reject_button.configure(state="disabled")
            return

        info = ctk.CTkFrame(
            self.details_frame,
            fg_color=PALE_GREEN,
            corner_radius=8
        )
        info.pack(fill="x", pady=(0, 12))

        fields = [
            ("Request ID", request.get("id", "")),
            ("Reader", request.get("reader_name", "")),
            ("Library card", request.get("card_number", "")),
            ("Request date", request.get("request_date", "")),
            ("Status", request.get("status", ""))
        ]

        for title, value in fields:
            line = ctk.CTkFrame(
                info,
                fg_color="transparent"
            )
            line.pack(
                fill="x",
                padx=14,
                pady=4
            )

            self.label(
                line,
                f"{title}:",
                12,
                MUTED
            ).pack(side="left")

            self.label(
                line,
                str(value),
                12,
                TEXT,
                True
            ).pack(
                side="left",
                padx=(8, 0)
            )

        self.label(
            self.details_frame,
            "Requested books",
            14,
            TEXT,
            True
        ).pack(
            anchor="w",
            pady=(4, 10)
        )

        books = request.get("books", [])

        if not books:
            self.label(
                self.details_frame,
                "No books in this request",
                12,
                MUTED
            ).pack(anchor="w", pady=(0, 10))

        for book in books:
            book_row = ctk.CTkFrame(
                self.details_frame,
                fg_color=PALE_GREEN,
                corner_radius=7
            )
            book_row.pack(
                fill="x",
                pady=(0, 8)
            )

            self.label(
                book_row,
                str(book.get("title", "")),
                13,
                TEXT,
                True
            ).pack(
                anchor="w",
                padx=14,
                pady=(10, 2)
            )

            self.label(
                book_row,
                (
                    f"Code: {book.get('code', '')}"
                    f" | Author: {book.get('author', '')}"
                ),
                11,
                MUTED
            ).pack(
                anchor="w",
                padx=14,
                pady=(0, 10)
            )

        pending = (
            str(request.get("status", "")).lower()
            == "pending"
        )

        self.approve_button.configure(
            state=(
                "normal"
                if pending and self.on_approve is not None
                else "disabled"
            )
        )

        self.reject_button.configure(
            state=(
                "normal"
                if pending and self.on_reject is not None
                else "disabled"
            )
        )

    # ==========================================
    # DATA AND CALLBACKS
    # ==========================================

    def set_requests(self, requests):
        self.requests = list(requests or [])

        self.filtered_requests = [
            request
            for request in self.requests
            if str(request.get("status", "")).lower() == "pending"
        ]

        self.selected_request = None
        self.render_requests()
        self.render_details()

    def search_requests(self):
        keyword = self.search_entry.get().strip().lower()

        self.filtered_requests = [
            request
            for request in self.requests
            if (
                str(request.get("status", "")).lower()
                == "pending"
            )
            and keyword in (
                str(request.get("id", "")) + " " +
                str(request.get("reader_name", "")) + " " +
                str(request.get("card_number", ""))
            ).lower()
        ]

        self.selected_request = None
        self.render_requests()
        self.render_details()

    def select_request(self, request):
        self.selected_request = request
        self.render_details()

    def approve_request(self):
        if (
            self.selected_request is not None
            and self.on_approve is not None
        ):
            self.on_approve(self.selected_request)

    def reject_request(self):
        if (
            self.selected_request is not None
            and self.on_reject is not None
        ):
            self.on_reject(self.selected_request)

    def navigate(self, page_name):
        if self.on_navigate is not None:
            self.on_navigate(page_name)

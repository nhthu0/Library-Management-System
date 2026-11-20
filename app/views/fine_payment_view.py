
from pathlib import Path
from datetime import date, datetime

import customtkinter as ctk
from PIL import Image, ImageDraw

PAGE_BG = "#F7FAF9"
SIDEBAR_BG = "#2D6857"
SIDEBAR_ITEM = "#397461"
ACTIVE_GREEN = "#70D998"
PALE_GREEN = "#F2FBF6"

GREEN = "#008D3F"
DARK_GREEN = "#007536"

WHITE = "#FFFFFF"
TEXT = "#2D3A40"
MUTED = "#8293A5"
BORDER = "#E5EBE9"

RED = "#D94B55"
RED_BG = "#FDEDEF"
GREEN_BG = "#E4F7EB"


# ==========================================
# HELPERS
# ==========================================

def format_money(value):
    try:
        return f"{float(value):,.0f} VND"
    except (TypeError, ValueError):
        return "-"


def format_date(value):
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")

    if value in (None, ""):
        return "-"

    value = str(value)

    try:
        return datetime.strptime(
            value[:10], "%Y-%m-%d"
        ).strftime("%d/%m/%Y")
    except ValueError:
        return value


# ==========================================
# FINE PAYMENT VIEW
# ==========================================

class FinePaymentView(ctk.CTkFrame):

    def __init__(
        self,
        master,
        on_navigate=None,
        on_payment=None,
        is_admin=False,
        on_check_payment=None
    ):
        super().__init__(
            master,
            fg_color=PAGE_BG,
            corner_radius=0
        )

        self.on_navigate = on_navigate
        self.on_payment = on_payment
        self.on_check_payment = on_check_payment
        self.payment_busy = False
        self.is_admin = is_admin

        self.assets = (
            Path(__file__).resolve().parents[1]
            / "assets"
        )

        self.images = []

        self.fines = []
        self.filtered_fines = []
        self.selected_fine = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()

        self.main = ctk.CTkScrollableFrame(
            self,
            fg_color=PAGE_BG,
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

        self.build_header()
        self.build_summary()
        self.build_fine_list()
        self.build_payment_details()

    # ==========================================
    # COMMON COMPONENTS
    # ==========================================

    def text(
        self,
        parent,
        value,
        size=11,
        color=TEXT,
        bold=False,
        **kwargs
    ):
        return ctk.CTkLabel(
            parent,
            text=str(value),
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

    def load_image(self, path, size):
        if not path.is_file():
            return None

        try:
            with Image.open(path) as src:
                img = src.convert("RGBA").copy()

            result = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=size
            )

            self.images.append(result)
            return result

        except (OSError, ValueError):
            return None

    def load_menu_icon(self, filename, active=False):
        return self.load_image(
            self.assets / "icons" / filename,
            (16, 16)
        )

    def make_avatar(self):
        img = Image.new(
            "RGBA",
            (96, 96),
            (0, 0, 0, 0)
        )

        ImageDraw.Draw(img).ellipse(
            (0, 0, 95, 95),
            fill=ACTIVE_GREEN
        )

        avatar = ctk.CTkImage(
            light_image=img,
            dark_image=img,
            size=(32, 32)
        )

        self.images.append(avatar)
        return avatar

    @staticmethod
    def clear(frame):
        for widget in frame.winfo_children():
            widget.destroy()

    # ==========================================
    # SIDEBAR - SAME AS BORROWING HISTORY
    # ==========================================

    def build_sidebar(self):

        sidebar = ctk.CTkFrame(
            self,
            width=190,
            fg_color=SIDEBAR_BG,
            corner_radius=16
        )

        sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(15, 0),
            pady=15
        )

        sidebar.grid_propagate(False)

        # LOGO
        logo_box = ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        )

        logo_box.pack(
            fill="x",
            pady=(22, 38)
        )

        logo = self.load_image(
            self.assets / "logo.png",
            (36, 36)
        )

        if logo is not None:
            ctk.CTkLabel(
                logo_box,
                image=logo,
                text=""
            ).pack()
        else:
            ctk.CTkLabel(
                logo_box,
                text="▣",
                width=36,
                height=36,
                fg_color=ACTIVE_GREEN,
                text_color=SIDEBAR_BG,
                corner_radius=18,
                font=("Segoe UI", 17)
            ).pack()

        self.text(
            logo_box,
            "Library",
            14,
            WHITE,
            True
        ).pack(pady=(8, 0))

        self.text(
            logo_box,
            "Library System",
            10,
            "#C5DCD4"
        ).pack(pady=(1, 0))

        menus = [
            ("dashboard.png", "Dashboard"),
            ("borrow.png", "Borrow books"),
            ("booklist.png", "Return books"),
            ("history.png", "Borrowing history"),
        ]
        menus += (
            [("management.png", "Fine Management"), ("statistics.png", "Fine Payment")]
            if self.is_admin else [("statistics.png", "My Fines")]
        )

        for filename, title in menus:

            active = title in ("Fine Payment", "My Fines")

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

            if active:
                self.text(
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
            sidebar,
            fg_color="transparent"
        ).pack(
            fill="both",
            expand=True
        )

        # FOOTER
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
        ).pack(pady=(3, 5))

        avatar_image = self.make_avatar()

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
            image=avatar_image,
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
            "Fine Payment",
            21,
            TEXT,
            True
        ).pack(anchor="w")

        self.text(
            header,
            "View and pay your overdue library fines",
            11,
            MUTED
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

    # ==========================================
    # SUMMARY
    # ==========================================

    def build_summary(self):

        frame = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )

        frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 16)
        )

        for col in range(3):
            frame.grid_columnconfigure(
                col,
                weight=1,
                uniform="summary"
            )

        self.total_label = self.summary_card(
            frame,
            0,
            "Total fines",
            "0"
        )

        self.unpaid_label = self.summary_card(
            frame,
            1,
            "Unpaid fines",
            "0"
        )

        self.amount_label = self.summary_card(
            frame,
            2,
            "Outstanding amount",
            "0 VND"
        )

    def summary_card(
        self,
        parent,
        col,
        heading,
        value
    ):

        card = self.card(parent)

        card.grid(
            row=0,
            column=col,
            sticky="ew",
            padx=5
        )

        self.text(
            card,
            heading,
            11,
            MUTED
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 7)
        )

        label = self.text(
            card,
            value,
            20,
            TEXT,
            True
        )

        label.pack(
            anchor="w",
            padx=15,
            pady=(0, 15)
        )

        return label

    def update_summary(self):

        unpaid = [
            fine for fine in self.fines
            if str(
                fine.get("status", "")
            ).lower().strip() == "unpaid"
        ]

        amount = 0

        for fine in unpaid:
            try:
                amount += float(
                    fine.get("amount", 0)
                )
            except (TypeError, ValueError):
                pass

        self.total_label.configure(
            text=str(len(self.fines))
        )

        self.unpaid_label.configure(
            text=str(len(unpaid))
        )

        self.amount_label.configure(
            text=format_money(amount)
        )

    # ==========================================
    # FINE LIST
    # ==========================================

    def build_fine_list(self):

        card = self.card(self.main)

        card.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 16)
        )

        top = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        top.pack(
            fill="x",
            padx=15,
            pady=(15, 12)
        )

        self.text(
            top,
            "My fines",
            14,
            TEXT,
            True
        ).pack(side="left")

        self.status_filter = ctk.CTkComboBox(
            top,
            values=[
                "All statuses",
                "Unpaid",
                "Paid"
            ],
            state="readonly",
            width=150,
            height=34,
            fg_color=WHITE,
            border_color=BORDER,
            button_color="#F1F5F3",
            button_hover_color="#E3EFE8",
            dropdown_fg_color=WHITE,
            dropdown_hover_color=PALE_GREEN,
            text_color=TEXT,
            font=("Segoe UI", 11),
            corner_radius=6,
            command=lambda value: self.apply_filter()
        )

        self.status_filter.set("All statuses")
        self.status_filter.pack(side="right")

        self.list_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        self.list_frame.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        self.render_fines()

    # ==========================================
    # RENDER FINES
    # ==========================================

    def render_fines(self):

        self.clear(self.list_frame)

        if not self.filtered_fines:

            empty = ctk.CTkFrame(
                self.list_frame,
                fg_color=PALE_GREEN,
                height=130,
                corner_radius=8
            )

            empty.pack(fill="x")
            empty.pack_propagate(False)

            self.text(
                empty,
                "No fines found",
                12,
                MUTED
            ).place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            return

        for fine in self.filtered_fines:

            row = ctk.CTkFrame(
                self.list_frame,
                fg_color=PALE_GREEN,
                corner_radius=8
            )

            row.pack(
                fill="x",
                pady=5
            )

            left = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            left.pack(
                side="left",
                fill="both",
                expand=True,
                padx=15,
                pady=12
            )

            self.text(
                left,
                fine.get("book_title", "-"),
                12,
                TEXT,
                True
            ).pack(anchor="w")

            self.text(
                left,
                (
                    f"Fine ID: {fine.get('id', '-')}"
                    f"    |    "
                    f"Reason: {fine.get('reason', '-')}"
                ),
                10,
                MUTED
            ).pack(
                anchor="w",
                pady=(5, 0)
            )

            right = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            right.pack(
                side="right",
                padx=15,
                pady=10
            )

            self.text(
                right,
                format_money(fine.get("amount")),
                13,
                TEXT,
                True
            ).pack(anchor="e")

            status = str(
                fine.get("status", "-")
            )

            paid = status.strip().lower() == "paid"

            self.text(
                right,
                status,
                10,
                GREEN if paid else RED,
                True,
                fg_color=(
                    GREEN_BG if paid else RED_BG
                ),
                corner_radius=5,
                width=75,
                height=24
            ).pack(
                anchor="e",
                pady=(5, 7)
            )

            ctk.CTkButton(
                right,
                text="View details",
                width=105,
                height=30,
                fg_color=WHITE,
                border_width=1,
                border_color=GREEN,
                text_color=GREEN,
                hover_color=PALE_GREEN,
                command=lambda item=fine: (
                    self.select_fine(item)
                )
            ).pack(anchor="e")

    # ==========================================
    # PAYMENT DETAILS
    # ==========================================

    def build_payment_details(self):

        card = self.card(self.main)

        card.grid(
            row=3,
            column=0,
            sticky="ew"
        )

        self.text(
            card,
            "Payment details",
            14,
            TEXT,
            True
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 12)
        )

        self.details_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        self.details_frame.pack(
            fill="x",
            padx=15
        )

        self.message_label = self.text(
            card,
            "",
            11,
            RED
        )

        self.message_label.pack(
            anchor="w",
            padx=15,
            pady=(8, 5)
        )

        actions = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        actions.pack(
            fill="x",
            padx=15,
            pady=(5, 15)
        )

        ctk.CTkButton(
            actions,
            text="Cancel",
            width=120,
            height=38,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            hover_color=PAGE_BG,
            command=self.cancel_payment
        ).pack(side="left")

        self.pay_button = ctk.CTkButton(
            actions,
            text="Record payment" if self.is_admin else "Pay with MoMo Sandbox",
            height=38,
            fg_color=GREEN,
            hover_color=DARK_GREEN,
            state="disabled",
            command=self.confirm_payment
        )

        self.pay_button.pack(
            side="right",
            fill="x",
            expand=True,
            padx=(10, 0)
        )

        self.check_payment_button = None
        if self.on_check_payment is not None:
            self.check_payment_button = ctk.CTkButton(
                actions, text="Check MoMo status", width=135,
                state="disabled", command=self.check_payment
            )
            self.check_payment_button.pack(side="right", padx=(8, 0))

        self.render_details()

    # ==========================================
    # RENDER PAYMENT DETAILS
    # ==========================================

    def render_details(self):

        self.clear(self.details_frame)

        fine = self.selected_fine

        if fine is None:

            empty = ctk.CTkFrame(
                self.details_frame,
                fg_color=PALE_GREEN,
                corner_radius=8,
                height=130
            )

            empty.pack(fill="x")
            empty.pack_propagate(False)

            self.text(
                empty,
                "Select a fine to view payment details",
                12,
                MUTED
            ).place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            self.update_payment_buttons(False)
            return

        fields = [
            ("Fine ID", fine.get("id", "-")),
            ("Book title", fine.get("book_title", "-")),
            ("Reason", fine.get("reason", "-")),
            ("Days overdue", fine.get("days_overdue", "-")),
            (
                "Fine date",
                format_date(
                    fine.get(
                        "created_date",
                        fine.get("fine_date")
                    )
                )
            ),
            (
                "Amount",
                format_money(fine.get("amount"))
            ),
            ("Status", fine.get("status", "-")),
            (
                "Payment date",
                format_date(fine.get("payment_date"))
            )
        ]

        for heading, value in fields:

            row = ctk.CTkFrame(
                self.details_frame,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                pady=5
            )

            self.text(
                row,
                heading,
                11,
                MUTED,
                width=145,
                anchor="w"
            ).pack(side="left")

            self.text(
                row,
                value,
                11,
                TEXT,
                True,
                anchor="w"
            ).pack(side="left")

        self.update_payment_buttons(str(fine.get("status", "")).strip().lower() == "unpaid")

    def update_payment_buttons(self, unpaid):
        available = unpaid and not self.payment_busy
        self.pay_button.configure(state="normal" if available and self.on_payment else "disabled")
        if self.check_payment_button is not None:
            self.check_payment_button.configure(state="normal" if available else "disabled")

    def set_payment_busy(self, busy):
        self.payment_busy = busy
        self.render_details()

    def check_payment(self):
        if self.selected_fine is not None and not self.payment_busy:
            self.on_check_payment(self.selected_fine)

    # ==========================================
    # DATA
    # ==========================================

    def set_fines(self, fines):

        selected = self.selected_fine
        self.fines = list(fines or [])
        self.selected_fine = next(
            (fine for fine in self.fines if selected and fine["id"] == selected["id"]), None
        )

        self.apply_filter()
        self.update_summary()
        self.render_details()

    # ==========================================
    # FILTER
    # ==========================================

    def apply_filter(self):

        status = (
            self.status_filter.get()
            .strip()
            .lower()
        )

        self.filtered_fines = [
            fine for fine in self.fines
            if (
                status == "all statuses"
                or str(
                    fine.get("status", "")
                ).strip().lower() == status
            )
        ]

        self.render_fines()

    # ==========================================
    # ACTIONS
    # ==========================================

    def select_fine(self, fine):

        self.selected_fine = fine

        self.message_label.configure(text="")
        self.render_details()

    def cancel_payment(self):

        self.selected_fine = None

        self.message_label.configure(text="")
        self.render_details()

    def confirm_payment(self):

        fine = self.selected_fine

        if fine is None or self.on_payment is None or self.payment_busy:
            return

        if str(
            fine.get("status", "")
        ).strip().lower() != "unpaid":
            return

        # Controller handles payment processing.
        self.on_payment(fine)

    def navigate(self, page_name):

        if self.on_navigate is not None:
            self.on_navigate(page_name)


# Compatibility with older imports
PaymentView = FinePaymentView


import re
from datetime import datetime, date

import customtkinter as ctk
from PIL import Image, ImageDraw

from app.config.theme import (
    BG_GREEN,
    PRIMARY_GREEN,
    PRIMARY_HOVER,
    WHITE,
    TEXT_DARK,
    TEXT_MUTED,
    ERROR,
)


class RegisterView(ctk.CTkFrame):
    def __init__(self, master, on_register=None, on_back=None):
        super().__init__(master, fg_color=BG_GREEN)

        self.on_register = on_register
        self.on_back = on_back

        self.icon_images = []
        self.agree = ctk.BooleanVar(value=False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main container
        container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        container.grid(
            row=0,
            column=0,
            padx=20,
            pady=20
        )

        # =========================
        # HEADER
        # =========================
        header = ctk.CTkFrame(
            container,
            fg_color="transparent"
        )
        header.pack(pady=(0, 20))

        self.logo_image = self.create_logo()

        ctk.CTkLabel(
            header,
            text="",
            image=self.logo_image,
            width=44,
            height=44
        ).pack(side="left", padx=(0, 10))

        header_text = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )
        header_text.pack(side="left")

        ctk.CTkLabel(
            header_text,
            text="Library System",
            font=("Segoe UI", 22),
            text_color=WHITE,
            height=27
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_text,
            text="Library Management System",
            font=("Segoe UI", 10),
            text_color="#D1E4D9",
            height=16
        ).pack(anchor="w")

        # =========================
        # REGISTER CARD
        # =========================
        card = ctk.CTkFrame(
            container,
            width=650,
            fg_color=WHITE,
            corner_radius=12,
            border_width=1,
            border_color="#E1E7E3"
        )
        card.pack()

        content = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        content.pack(
            fill="both",
            padx=30,
            pady=(22,18)
        )

        # Card title
        title_row = ctk.CTkFrame(
            content,
            fg_color="transparent"
        )
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text="",
            font=("Segoe UI Symbol", 16),
            text_color=TEXT_DARK,
            width=24
        ).pack(side="left")

        ctk.CTkLabel(
            title_row,
            text="Register for library membership",
            font=("Segoe UI", 15, "bold"),
            text_color=TEXT_DARK
        ).pack(side="left")

        ctk.CTkLabel(
            content,
            text="Complete your details to apply for a membership card",
            font=("Segoe UI", 10),
            text_color="#778696",
            anchor="w"
        ).pack(fill="x", pady=(2, 12))

        # =========================
        # FULL NAME
        # =========================
        self.full_name = self.add_entry(
            content,
            label="Full name",
            placeholder="Enter your full name",
            icon="user"
        )

        # =========================
        # DATE OF BIRTH + GENDER
        # =========================
        row = self.create_row(content)

        self.date_of_birth = self.add_entry(
            row,
            label="Date of birth",
            placeholder="DD/MM/YYYY",
            icon="calendar",
            column=0
        )

        gender_box = self.create_column(row, 1)

        self.add_label(gender_box, "Gender")

        gender_border = ctk.CTkFrame(
            gender_box,
            fg_color=WHITE,
            corner_radius=6,
            border_width=2,
            border_color="#A7B5AD"
        )
        gender_border.pack(fill="x")

        self.gender = ctk.CTkOptionMenu(
            gender_border,
            values=[
                "Select gender",
                "Male",
                "Female",
                "Other"
            ],
            height=34,
            corner_radius=4,
            fg_color=WHITE,
            button_color="#E9F0EC",
            button_hover_color="#D6E5DC",
            text_color=TEXT_DARK,
            font=("Segoe UI", 10),
            dropdown_fg_color=WHITE,
            dropdown_text_color=TEXT_DARK
        )
        self.gender.pack(
            fill="x",
            padx=3,
            pady=3
        )
        self.gender.set("Select gender")

        # =========================
        # NATIONAL ID + PHONE
        # =========================
        row = self.create_row(content)

        self.national_id = self.add_entry(
            row,
            label="National ID number",
            placeholder="Enter your national ID number",
            icon="id",
            column=0
        )

        self.phone = self.add_entry(
            row,
            label="Phone number",
            placeholder="Enter your phone number",
            icon="phone",
            column=1
        )

        # =========================
        # EMAIL + ADDRESS
        # =========================
        row = self.create_row(content)

        self.email = self.add_entry(
            row,
            label="Email",
            placeholder="email@example.com",
            icon="mail",
            column=0
        )

        self.address = self.add_entry(
            row,
            label="Contact address",
            placeholder="Enter your full address",
            icon="location",
            column=1
        )

        # =========================
        # PASSWORD + CONFIRM
        # =========================
        row = self.create_row(content)

        self.password = self.add_entry(
            row,
            label="Password",
            placeholder="Password (at least 6 characters)",
            icon="lock",
            secret=True,
            column=0
        )

        self.confirm_password = self.add_entry(
            row,
            label="Confirm password",
            placeholder="Re-enter your password",
            icon="lock",
            secret=True,
            column=1
        )

        # =========================
        # MEMBERSHIP TERMS
        # =========================
        terms = ctk.CTkFrame(
            content,
            fg_color="#F3F7F5",
            corner_radius=7,
            border_width=2,
            border_color="#B5C5BC"
        )
        terms.pack(
            fill="x",
            pady=(15, 10)
        )

        ctk.CTkLabel(
            terms,
            text="Membership terms of use:",
            font=("Segoe UI", 10, "bold"),
            text_color=TEXT_DARK,
            anchor="w"
        ).pack(
            fill="x",
            padx=12,
            pady=(8, 3)
        )

        terms_text = (
            "• Membership cards are personal and non-transferable.\n"
            "• Borrow up to 3 books at a time, for a maximum of 30 days.\n"
            "• Late returns incur a fee of VND 2,000 per book per day.\n"
            "• The library may revoke membership for rule violations."
        )

        ctk.CTkLabel(
            terms,
            text=terms_text,
            font=("Segoe UI", 10),
            text_color="#586A76",
            justify="left",
            anchor="w"
        ).pack(
            fill="x",
            padx=12,
            pady=(0, 9)
        )

        # =========================
        # AGREEMENT
        # =========================
        agree_row = ctk.CTkFrame(
            content,
            fg_color="transparent"
        )
        agree_row.pack(fill="x")

        ctk.CTkCheckBox(
            agree_row,
            text="I have read and agree to the library membership terms",
            variable=self.agree,
            font=("Segoe UI", 10),
            text_color=TEXT_DARK,
            fg_color=PRIMARY_GREEN,
            hover_color=PRIMARY_HOVER,
            border_color="#84968C",
            checkbox_width=16,
            checkbox_height=16
        ).pack(side="left")

        ctk.CTkLabel(
            agree_row,
            text="*",
            font=("Segoe UI", 11, "bold"),
            text_color="#D64545"
        ).pack(side="left", padx=(3, 0))

        # Validation message
        self.message = ctk.CTkLabel(
            content,
            text="",
            height=18,
            font=("Segoe UI", 10),
            text_color=ERROR
        )
        self.message.pack(fill="x", pady=(2, 2))

        # =========================
        # REGISTER BUTTON
        # =========================
        ctk.CTkButton(
            content,
            text=" Register for membership",
            height=37,
            corner_radius=5,
            fg_color=PRIMARY_GREEN,
            hover_color=PRIMARY_HOVER,
            text_color=WHITE,
            font=("Segoe UI", 11, "bold"),
            command=self.handle_register
        ).pack(fill="x")

        # =========================
        # SIGN IN
        # =========================
        bottom = ctk.CTkFrame(
            content,
            fg_color="transparent"
        )
        bottom.pack(pady=(5, 0))

        ctk.CTkLabel(
            bottom,
            text="Already have an account?",
            font=("Segoe UI", 10),
            text_color="#7D8996"
        ).pack(side="left")

        ctk.CTkButton(
            bottom,
            text="Sign in",
            width=48,
            height=24,
            fg_color="transparent",
            hover_color="#EFF5F1",
            text_color=PRIMARY_GREEN,
            font=("Segoe UI", 10, "bold"),
            command=self.handle_back
        ).pack(side="left", padx=(3, 0))

        # =========================
        # FOOTER
        # =========================
        ctk.CTkLabel(
            container,
            text="© 2026 Library Management System. All rights reserved.",
            font=("Segoe UI", 9),
            text_color="#D1E4D9"
        ).pack(pady=(15, 0))

    # =========================
    # LAYOUT HELPERS
    # =========================

    def create_row(self, parent):
        row = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        row.pack(fill="x", pady=(10, 0))

        row.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="fields"
        )
        return row

    def create_column(self, parent, column):
        box = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        box.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=(0, 8) if column == 0 else (8, 0)
        )
        return box

    def add_label(self, parent, label):
        line = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        line.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            line,
            text=label,
            font=("Segoe UI", 10, "bold"),
            text_color=TEXT_DARK,
            height=17
        ).pack(side="left")

        ctk.CTkLabel(
            line,
            text=" *",
            font=("Segoe UI", 10, "bold"),
            text_color="#D64545",
            height=17
        ).pack(side="left")

    def add_entry(
        self,
        parent,
        label,
        placeholder,
        icon,
        secret=False,
        column=None
    ):
        if column is None:
            box = ctk.CTkFrame(
                parent,
                fg_color="transparent"
            )
            box.pack(fill="x")
        else:
            box = self.create_column(parent, column)

        self.add_label(box, label)

        # Viền ô nhập: chỉnh tại đây
        icon_image = self.create_icon(icon)
        entry = ctk.CTkEntry(
    box,
    height=48,
    placeholder_text=placeholder,
    show="*" if secret else "",
    border_width=2,
    border_color="#A7B5AD",
    corner_radius=7,
    fg_color=WHITE,
    text_color=TEXT_DARK,
    font=("Segoe UI", 13)
) 
        entry.pack(fill="x")
        return entry
    # =========================
    # ICONS
    # =========================

    def create_logo(self):
        size = 100
        img = Image.new(
            "RGBA",
            (size, size),
            (0, 0, 0, 0)
        )
        draw = ImageDraw.Draw(img)

        draw.ellipse(
            (3, 3, 97, 97),
            fill="#B8E6C6"
        )

        color = "#176D42"

        # Open book
        draw.line(
            [(20, 29), (40, 26), (50, 34), (60, 26), (80, 29)],
            fill=color,
            width=5,
            joint="curve"
        )
        draw.line(
            [(20, 29), (20, 71), (40, 69), (50, 76)],
            fill=color,
            width=5,
            joint="curve"
        )
        draw.line(
            [(80, 29), (80, 71), (60, 69), (50, 76)],
            fill=color,
            width=5,
            joint="curve"
        )
        draw.line(
            [(50, 34), (50, 76)],
            fill=color,
            width=4
        )

        return ctk.CTkImage(
            light_image=img,
            dark_image=img,
            size=(44, 44)
        )

    def create_icon(self, name):
        img = Image.new(
            "RGBA",
            (40, 40),
            (0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(img)
        color = "#748596"

        if name == "user":
            draw.ellipse(
                (14, 6, 26, 18),
                outline=color,
                width=3
            )
            draw.arc(
                (8, 19, 32, 37),
                180, 360,
                fill=color,
                width=3
            )

        elif name == "calendar":
            draw.rectangle(
                (7, 10, 33, 33),
                outline=color,
                width=3
            )
            draw.line(
                (7, 17, 33, 17),
                fill=color,
                width=3
            )
            draw.line(
                (14, 6, 14, 13),
                fill=color,
                width=3
            )
            draw.line(
                (26, 6, 26, 13),
                fill=color,
                width=3
            )

        elif name == "id":
            draw.rounded_rectangle(
                (5, 10, 35, 30),
                radius=3,
                outline=color,
                width=3
            )
            draw.ellipse(
                (10, 15, 16, 21),
                outline=color,
                width=2
            )
            draw.line(
                (20, 17, 30, 17),
                fill=color,
                width=2
            )
            draw.line(
                (20, 23, 30, 23),
                fill=color,
                width=2
            )

        elif name == "phone":
            draw.arc(
                (8, 6, 32, 34),
                95, 265,
                fill=color,
                width=4
            )
            draw.line(
                (10, 10, 16, 15),
                fill=color,
                width=4
            )
            draw.line(
                (25, 25, 31, 30),
                fill=color,
                width=4
            )

        elif name == "mail":
            draw.rectangle(
                (6, 11, 34, 30),
                outline=color,
                width=3
            )
            draw.line(
                (6, 11, 20, 22, 34, 11),
                fill=color,
                width=2
            )

        elif name == "location":
            draw.ellipse(
                (11, 5, 29, 24),
                outline=color,
                width=3
            )
            draw.ellipse(
                (17, 11, 23, 17),
                outline=color,
                width=2
            )
            draw.line(
                (12, 22, 20, 35, 28, 22),
                fill=color,
                width=3
            )

        elif name == "lock":
            draw.arc(
                (12, 4, 28, 25),
                180, 360,
                fill=color,
                width=3
            )
            draw.rounded_rectangle(
                (9, 17, 31, 34),
                radius=3,
                outline=color,
                width=3
            )

        icon_image = ctk.CTkImage(
            light_image=img,
            dark_image=img,
            size=(16, 16)
        )

        self.icon_images.append(icon_image)
        return icon_image

    # =========================
    # REGISTER VALIDATION
    # =========================

    def handle_register(self):
        data = {
            "full_name": self.full_name.get().strip(),
            "date_of_birth": self.date_of_birth.get().strip(),
            "gender": self.gender.get(),
            "national_id": self.national_id.get().strip(),
            "phone_number": self.phone.get().strip(),
            "email": self.email.get().strip(),
            "contact_address": self.address.get().strip(),
            "password": self.password.get()
        }

        confirm = self.confirm_password.get()

        if (
            not all(data.values())
            or not confirm
            or data["gender"] == "Select gender"
        ):
            self.show_error(
                "Please fill in all required fields."
            )
            return

        try:
            dob = datetime.strptime(
                data["date_of_birth"],
                "%d/%m/%Y"
            ).date()

            if dob >= date.today():
                raise ValueError

        except ValueError:
            self.show_error(
                "Please enter a valid date of birth (DD/MM/YYYY)."
            )
            return

        if not re.fullmatch(
            r"\d{12}",
            data["national_id"]
        ):
            self.show_error(
                "National ID must contain 12 digits."
            )
            return

        if not re.fullmatch(
            r"\d{10,11}",
            data["phone_number"]
        ):
            self.show_error(
                "Please enter a valid phone number."
            )
            return

        if not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            data["email"]
        ):
            self.show_error(
                "Please enter a valid email address."
            )
            return

        if len(data["password"]) < 6:
            self.show_error(
                "Password must contain at least 6 characters."
            )
            return

        if data["password"] != confirm:
            self.show_error(
                "Passwords do not match."
            )
            return

        if not self.agree.get():
            self.show_error(
                "Please agree to the membership terms."
            )
            return

        self.message.configure(
            text="UI demo only. No account was created.",
            text_color=PRIMARY_GREEN
        )

        if self.on_register:
            self.on_register(data)

    def show_error(self, message):
        self.message.configure(
            text=message,
            text_color=ERROR
        )

    def handle_back(self):
        if self.on_back:
            self.on_back()

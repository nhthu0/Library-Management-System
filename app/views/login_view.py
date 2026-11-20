from pathlib import Path

import customtkinter as ctk
from PIL import Image

from app.config.theme import (
    BG_GREEN,
    PRIMARY_GREEN,
    PRIMARY_HOVER,
    WHITE,
    TEXT_DARK,
    TEXT_MUTED,
    BORDER,
    ERROR,
)


class LoginView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_login=None,
        on_register=None,
        on_forgot_password=None
    ):
        super().__init__(master, fg_color=BG_GREEN)

        self.on_login = on_login
        self.on_register = on_register
        self.on_forgot_password = on_forgot_password

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(
            self, fg_color="transparent"
        )
        container.grid(row=0, column=0)

        # Logo and system name
        header = ctk.CTkFrame(
            container, fg_color="transparent"
        )
        header.pack(pady=(0, 45))

        logo_path = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "logo.png"
        )

        self.logo = ctk.CTkImage(
            light_image=Image.open(logo_path),
            dark_image=Image.open(logo_path),
            size=(52, 52)
        )

        ctk.CTkLabel(
            header,
            text="",
            image=self.logo
        ).pack(side="left", padx=(0, 12))

        title_group = ctk.CTkFrame(
            header, fg_color="transparent"
        )
        title_group.pack(side="left")

        ctk.CTkLabel(
            title_group,
            text="Library System",
            font=("Segoe UI", 27, "bold"),
            text_color=WHITE,
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_group,
            text="Library Management System",
            font=("Segoe UI", 11),
            text_color="#D9E9E1",
            anchor="w"
        ).pack(anchor="w")

        # White login card
        card = ctk.CTkFrame(
            container,
            width=520,
            height=470,
            fg_color=WHITE,
            corner_radius=14
        )
        card.pack()
        card.pack_propagate(False)

        content = ctk.CTkFrame(
            card, fg_color="transparent"
        )
        content.pack(
            fill="both",
            expand=True,
            padx=45,
            pady=35
        )

        ctk.CTkLabel(
            content,
            text="Sign in",
            font=("Segoe UI", 22, "bold"),
            text_color=TEXT_DARK,
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            content,
            text="Enter your login details",
            font=("Segoe UI", 12),
            text_color=TEXT_MUTED,
            anchor="w"
        ).pack(fill="x", pady=(4, 22))

        ctk.CTkLabel(
            content,
            text="Username",
            text_color=TEXT_DARK,
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 5))

        self.username = ctk.CTkEntry(
            content,
            height=46,
            placeholder_text="Enter your username",
            border_color=BORDER,
            fg_color=WHITE,
            text_color=TEXT_DARK
        )
        self.username.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            content,
            text="Password",
            text_color=TEXT_DARK,
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 5))

        self.password = ctk.CTkEntry(
            content,
            height=46,
            placeholder_text="Enter your password",
            show="*",
            border_color=BORDER,
            fg_color=WHITE,
            text_color=TEXT_DARK
        )
        self.password.pack(fill="x")

        self.message = ctk.CTkLabel(
            content,
            text="",
            font=("Segoe UI", 11),
            text_color=ERROR,
            height=22
        )
        self.message.pack(fill="x", pady=(5, 0))

        ctk.CTkButton(
            content,
            text="Sign in",
            height=42,
            fg_color=PRIMARY_GREEN,
            hover_color=PRIMARY_HOVER,
            command=self.handle_login
        ).pack(fill="x", pady=(5, 10))

        ctk.CTkButton(
            content,
            text="Forgot password?",
            height=24,
            fg_color="transparent",
            hover_color="#F1F7F3",
            text_color=PRIMARY_GREEN,
            command=self.handle_forgot_password
        ).pack()

        ctk.CTkButton(
            content,
            text="Don't have an account? Register for membership",
            height=25,
            fg_color="transparent",
            hover_color="#F1F7F3",
            text_color=PRIMARY_GREEN,
            font=("Segoe UI", 11),
            command=self.handle_register
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            container,
            text="© 2026 Library Management System. All rights reserved.",
            text_color="#D4E4DB",
            font=("Segoe UI", 10)
        ).pack(pady=(40, 0))

    def handle_login(self):
        username = self.username.get().strip()
        password = self.password.get()

        if not username or not password:
            self.message.configure(
                text="Please enter username and password.",
                text_color=ERROR
            )
            return

        if self.on_login:
            self.on_login(username, password)
        else:
            self.message.configure(
                text="Login UI demo only. Authentication is not connected.",
                text_color=PRIMARY_GREEN
            )

    def handle_register(self):
        if self.on_register:
            self.on_register()
        else:
            self.message.configure(
                text="Register screen is not connected yet.",
                text_color=TEXT_MUTED
            )

    def handle_forgot_password(self):
        if self.on_forgot_password:
            self.on_forgot_password()
        else:
            self.message.configure(
                text="Password recovery is not connected yet.",
                text_color=TEXT_MUTED
            )

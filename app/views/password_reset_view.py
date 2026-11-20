import customtkinter as ctk
from tkinter import messagebox

import mysql.connector


class PasswordResetView(ctk.CTkFrame):
    def __init__(self, master, request, reset, on_back):
        super().__init__(master)
        self.request = request
        self.reset = reset
        self.on_back = on_back
        ctk.CTkLabel(self, text="Reset password", font=("Segoe UI", 24, "bold")).pack(pady=(30, 12))
        self.email = ctk.CTkEntry(self, width=320, placeholder_text="Registered email")
        self.email.pack(pady=6)
        ctk.CTkButton(self, text="Send code", command=self.send).pack(pady=6)
        self.code = ctk.CTkEntry(self, width=320, placeholder_text="Eight-digit code")
        self.code.pack(pady=6)
        self.password = ctk.CTkEntry(self, width=320, placeholder_text="New password", show="*")
        self.password.pack(pady=6)
        self.confirm = ctk.CTkEntry(self, width=320, placeholder_text="Confirm password", show="*")
        self.confirm.pack(pady=6)
        ctk.CTkButton(self, text="Reset password", command=self.submit).pack(pady=8)
        ctk.CTkButton(self, text="Cancel", command=on_back).pack(pady=6)
        self.status = ctk.CTkLabel(self, text="", wraplength=400)
        self.status.pack(pady=6)

    def send(self):
        try:
            self.request(self.email.get())
        except (ValueError, RuntimeError) as error:
            self.status.configure(text=str(error))
        except mysql.connector.Error:
            self.status.configure(text="Password recovery is temporarily unavailable.")
        else:
            self.status.configure(text="If this address is registered, a code will arrive by email.")

    def submit(self):
        if self.password.get() != self.confirm.get():
            self.status.configure(text="Passwords do not match.")
            return
        try:
            self.reset(self.email.get(), self.code.get().strip(), self.password.get())
        except (ValueError, RuntimeError) as error:
            self.status.configure(text=str(error))
        except mysql.connector.Error:
            self.status.configure(text="Password recovery is temporarily unavailable.")
        else:
            messagebox.showinfo("Reset password", "Password updated. You can now sign in.", parent=self)
            self.on_back()

import customtkinter as ctk
from tkinter import messagebox


PROFILE_FIELDS = (("Full name", "full_name"), ("Email", "email"), ("Phone", "phone_number"))


class ProfileView(ctk.CTkFrame):
    def __init__(self, master, on_back, on_save):
        super().__init__(master)
        self.on_save = on_save
        self.profile = None
        ctk.CTkButton(self, text="Dashboard", command=on_back).pack(anchor="w", padx=24, pady=16)
        ctk.CTkLabel(self, text="My Profile", font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=24)
        self.account = ctk.CTkLabel(self, text="")
        self.account.pack(anchor="w", padx=24, pady=(4, 16))
        self.entries = {}
        for label, key in PROFILE_FIELDS:
            ctk.CTkLabel(self, text=label).pack(anchor="w", padx=24)
            entry = ctk.CTkEntry(self, width=340)
            entry.pack(anchor="w", padx=24, pady=(0, 12))
            self.entries[key] = entry
        self.save_button = ctk.CTkButton(self, text="Save changes", command=self.save, state="disabled")
        self.save_button.pack(anchor="w", padx=24, pady=(12, 4))
        self.cancel_button = ctk.CTkButton(
            self, text="Cancel changes", command=lambda: self.set_profile(self.profile), state="disabled"
        )
        self.cancel_button.pack(anchor="w", padx=24, pady=(0, 12))

    def set_profile(self, profile):
        self.profile = profile
        if profile is None:
            self.account.configure(text="Profile unavailable")
            return
        self.account.configure(text=f"{profile['username']}  |  Expires: {profile.get('expiration_date') or '?'}")
        for key, entry in self.entries.items():
            entry.delete(0, "end")
            entry.insert(0, profile.get(key) or "")
        self.save_button.configure(state="normal")
        self.cancel_button.configure(state="normal")

    def save(self):
        fields = {
            key: entry.get().strip()
            for key, entry in self.entries.items()
            if entry.get().strip() != (self.profile.get(key) or "")
        }
        if not fields:
            return
        result = self.on_save(fields)
        if result["success"]:
            self.set_profile(result["data"])
            messagebox.showinfo("My profile", result["message"], parent=self)
        else:
            messagebox.showerror("My profile", result["message"], parent=self)

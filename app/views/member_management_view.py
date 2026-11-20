import customtkinter as ctk
from tkinter import messagebox

from app.views.profile_view import PROFILE_FIELDS


class MemberManagementView(ctk.CTkFrame):
    def __init__(self, master, controller, on_back, on_create):
        super().__init__(master)
        self.controller = controller
        ctk.CTkButton(self, text="Dashboard", command=on_back).pack(anchor="w", padx=24, pady=16)
        ctk.CTkLabel(self, text="Member Management", font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=24)
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=(8, 0))
        self.search = ctk.CTkEntry(actions, placeholder_text="Reader ID, name, username or email")
        self.search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search.bind("<Return>", lambda _: self.refresh())
        ctk.CTkButton(actions, text="Search", command=self.refresh).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Add reader", command=on_create).pack(side="left", padx=4)
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=16)
        self.refresh()

    def refresh(self):
        result = self.controller.get_all_readers()
        if not result["success"]:
            messagebox.showerror("Members", result["message"], parent=self)
            return
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        keyword = self.search.get().strip().casefold()
        readers = [
            reader for reader in result["data"]
            if any(keyword in str(reader[key]).casefold()
                   for key in ("readerID", "username", "full_name", "email"))
        ]
        if not readers:
            ctk.CTkLabel(self.list_frame, text="No readers found").pack(pady=16)
        for reader in readers:
            row = ctk.CTkFrame(self.list_frame)
            row.pack(fill="x", padx=8, pady=4)
            summary = f"{reader['full_name']}  |  {reader['username']}  |  {reader['account_status']}"
            ctk.CTkLabel(row, text=summary).pack(side="left", padx=12, pady=8)
            reader_id = reader["readerID"]
            status = "Locked" if reader["account_status"] == "Active" else "Active"
            ctk.CTkButton(row, text="Delete", width=76,
                          command=lambda key=reader_id: self.delete(key)).pack(side="right", padx=4)
            ctk.CTkButton(row, text="Lock" if status == "Locked" else "Activate", width=82,
                          command=lambda key=reader_id, target=status: self.set_status(key, target)).pack(side="right", padx=4)
            ctk.CTkButton(
                row, text="Edit", width=70, command=lambda member=reader: self.edit(member["readerID"])
            ).pack(side="right", padx=12, pady=8)

    def set_status(self, reader_id, status):
        self.handle_result(self.controller.set_reader_status(reader_id, status))

    def delete(self, reader_id):
        if messagebox.askyesno("Delete reader", f"Delete reader #{reader_id}?", parent=self):
            self.handle_result(self.controller.delete_reader(reader_id))

    def handle_result(self, result):
        if result["success"]:
            self.refresh()
        else:
            messagebox.showerror("Members", result["message"], parent=self)

    def edit(self, reader_id):
        result = self.controller.get_reader_by_id(reader_id)
        if not result["success"]:
            messagebox.showerror("Members", result["message"], parent=self)
            return
        reader = result["data"]
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit {reader['username']}")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        entries = {}
        for label, key in PROFILE_FIELDS:
            ctk.CTkLabel(dialog, text=label).pack(anchor="w", padx=16)
            entry = ctk.CTkEntry(dialog, width=300)
            entry.insert(0, reader.get(key) or "")
            entry.pack(padx=16, pady=(0, 8))
            entries[key] = entry

        def save():
            fields = {
                key: entry.get().strip()
                for key, entry in entries.items()
                if entry.get().strip() != (reader.get(key) or "")
            }
            if fields:
                result = self.controller.update_reader(reader_id, fields)
                if not result["success"]:
                    messagebox.showerror("Members", result["message"], parent=dialog)
                    return
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(dialog, text="Save changes", command=save).pack(padx=16, pady=12)

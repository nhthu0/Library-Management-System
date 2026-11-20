from datetime import date
from tkinter import messagebox

import customtkinter as ctk


class ReturnDetailsDialog(ctk.CTkToplevel):
    def __init__(self, master, rows, on_confirm):
        super().__init__(master)
        self.title("Confirm returned copies")
        self.geometry("660x430")
        self.transient(master.winfo_toplevel())
        self.grab_set()
        ctk.CTkLabel(self, text="Select each copy received and enter its condition.").pack(pady=12)
        self.return_date = ctk.CTkEntry(self, width=165, placeholder_text="YYYY-MM-DD")
        self.return_date.insert(0, date.today().isoformat())
        self.return_date.pack(pady=6)
        body = ctk.CTkScrollableFrame(self)
        body.pack(fill="both", expand=True, padx=14, pady=8)
        self.entries = []
        for loan_id, copies in rows:
            for copy in copies:
                row = ctk.CTkFrame(body)
                row.pack(fill="x", pady=3)
                checked = ctk.BooleanVar(value=True)
                ctk.CTkCheckBox(
                    row, text=f"#{loan_id}  {copy['title']} (copy {copy['detail_id']})",
                    variable=checked, onvalue=True, offvalue=False
                ).pack(side="left", padx=8)
                condition = ctk.CTkEntry(row, placeholder_text="Condition", width=120)
                condition.pack(side="right", padx=8, pady=5)
                self.entries.append((loan_id, copy["detail_id"], checked, condition))
        self.on_confirm = on_confirm
        ctk.CTkButton(self, text="Confirm selected copies", command=self.submit).pack(pady=10)

    def submit(self):
        selected = {}
        try:
            returned_on = date.fromisoformat(self.return_date.get().strip()).isoformat()
            for loan_id, detail_id, checked, condition in self.entries:
                if checked.get():
                    value = condition.get().strip()
                    if not value or len(value) > 100:
                        raise ValueError("Enter a condition for each selected copy (up to 100 characters).")
                    selected.setdefault(loan_id, []).append(
                        {"detail_id": detail_id, "return_date": returned_on, "condition": value}
                    )
            if not selected:
                raise ValueError("Select at least one copy to return.")
        except ValueError as error:
            messagebox.showerror("Return confirmation", str(error), parent=self)
            return
        self.destroy()
        self.on_confirm(selected)

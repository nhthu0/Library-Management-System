import customtkinter as ctk


class WorkflowListView(ctk.CTkFrame):
    def __init__(self, master, title, on_back, on_refresh=None):
        super().__init__(master)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(bar, text="Dashboard", command=on_back).pack(side="left")
        if on_refresh:
            ctk.CTkButton(bar, text="Refresh", command=on_refresh).pack(side="right")
        ctk.CTkLabel(self, text=title, font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=24)
        self.items = ctk.CTkScrollableFrame(self)
        self.items.pack(fill="both", expand=True, padx=24, pady=16)

    def show_rows(self, rows, empty_message):
        for child in self.items.winfo_children():
            child.destroy()
        if not rows:
            ctk.CTkLabel(self.items, text=empty_message).pack(pady=16)
        for text, actions in rows:
            card = ctk.CTkFrame(self.items)
            card.pack(fill="x", padx=8, pady=5)
            for label, action in reversed(actions):
                ctk.CTkButton(card, text=label, width=86, command=action).pack(side="right", padx=6, pady=8)
            ctk.CTkLabel(card, text=text, anchor="w", justify="left", wraplength=650).pack(
                side="left", fill="x", expand=True, padx=12, pady=8
            )

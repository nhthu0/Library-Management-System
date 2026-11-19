import customtkinter as ctk

BG_GREEN = "#315F50"
BG_GREEN_DARK = "#254A3E"
PRIMARY_GREEN = "#008A45"
PRIMARY_HOVER = "#00733A"

WHITE = "#FFFFFF"
PAGE_BG = "#F6F8F7"
TEXT_DARK = "#1F2933"
TEXT_MUTED = "#718078"
BORDER = "#DFE6E1"
ERROR = "#D64545"


def apply_theme():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")
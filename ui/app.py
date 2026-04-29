"""
ui/app.py
Root CustomTkinter window: sidebar + page container.
"""

import os, tempfile
import tkinter as tk
import customtkinter as ctk

from constants import (
    APP_TITLE, APP_WIDTH, APP_HEIGHT, APP_MIN_W, APP_MIN_H, SIDEBAR_W,
    ETH_DARKER, ETH_DARK, ETH_CARD, ETH_BORDER, ETH_TEXT, ETH_MUTED, ETH_BLUE,
    FONT_LG, FONT_2XL,
)
from ui.widgets import draw_eth_logo, Divider
from ui.settings_panel import SettingsPanel
from ui.transaction_page import TransactionPage
from ui.balance_page import BalancePage

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_NAV = [
    ("Transactions",          "tx"),
    ("Internal Transactions", "itx"),
    ("Current Balance",       "bal"),
]


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(APP_MIN_W, APP_MIN_H)
        self.configure(fg_color=ETH_DARKER)
        self._set_icon()
        self._pages    = {}
        self._nav_btns = {}
        self._active   = None
        self._build()

    def _set_icon(self):
        try:
            from PIL import Image, ImageDraw
            sz = 64; cx = cy = 32
            img  = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            blue  = (98, 126, 234, 255)
            light = (155, 181, 242, 200)
            draw.polygon([(cx,4),(cx-15,cy-5),(cx+15,cy-5)],    fill=blue)
            draw.polygon([(cx,cy+1),(cx-15,cy-5),(cx,4)],       fill=blue)
            draw.polygon([(cx,cy+1),(cx+15,cy-5),(cx,4)],       fill=light)
            draw.polygon([(cx,sz-4),(cx-15,cy+5),(cx+15,cy+5)], fill=blue)
            ico = os.path.join(tempfile.gettempdir(), "eth_icon.ico")
            img.save(ico, format="ICO", sizes=[(64,64),(32,32),(16,16)])
            self.iconbitmap(ico)
        except Exception:
            pass

    def _build(self):
        # Sidebar
        sidebar = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=0, width=SIDEBAR_W)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_row.pack(fill="x", pady=(20, 6))
        lc = tk.Canvas(logo_row, width=32, height=32, bg=ETH_CARD, highlightthickness=0)
        lc.pack(side="left", padx=(18, 6))
        draw_eth_logo(lc, 16, 16, size=28)
        ctk.CTkLabel(logo_row, text="ETH Explorer",
                     font=ctk.CTkFont(size=FONT_2XL, weight="bold"),
                     text_color=ETH_TEXT).pack(side="left")

        Divider(sidebar).pack(fill="x", padx=14, pady=(8, 16))

        for label, key in _NAV:
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w",
                height=40, corner_radius=8,
                fg_color="transparent", hover_color=ETH_BORDER,
                text_color=ETH_MUTED, font=ctk.CTkFont(size=FONT_LG),
                command=lambda k=key: self._switch(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._nav_btns[key] = btn

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)
        SettingsPanel(sidebar).pack(fill="x", padx=6, pady=(0, 16))

        # Page container
        container = ctk.CTkFrame(self, fg_color=ETH_DARK, corner_radius=0)
        container.pack(side="left", fill="both", expand=True)

        # tx and itx both use TransactionPage — pass tx_type preset
        self._pages["tx"]  = TransactionPage(container, preset_type="normal")
        self._pages["itx"] = TransactionPage(container, preset_type="internal")
        self._pages["bal"] = BalancePage(container)

        self._switch("tx")

    def _switch(self, key):
        if self._active:
            self._active.pack_forget()
        for k, btn in self._nav_btns.items():
            btn.configure(
                fg_color=ETH_BORDER if k == key else "transparent",
                text_color=ETH_TEXT  if k == key else ETH_MUTED,
            )
        self._active = self._pages[key]
        self._active.pack(fill="both", expand=True)

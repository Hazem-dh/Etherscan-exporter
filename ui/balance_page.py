"""
ui/balance_page.py
Page — Query current ETH balance of a wallet (free-tier, instant).
"""

import threading
from tkinter import messagebox

import customtkinter as ctk

from constants import (
    ETH_DARK, ETH_CARD, ETH_MUTED, ETH_TEXT, ETH_ERROR, ETH_ACCENT,
    ETH_DARKER, ETH_BORDER,
    FONT_BASE, FONT_SM, FONT_XL, FONT_HERO,
)
from core.api import get_current_balance
from core.state import AppState
from core.validators import ValidationError, validate_wallet_address
from ui.widgets import PageHeader, LabelledEntry

_SPIN = ["\u280b","\u2819","\u2839","\u2838","\u283c","\u2834","\u2826","\u2827","\u2807","\u280f"]


class BalancePage(ctk.CTkFrame):

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=ETH_DARK, **kw)
        self._build()

    def _build(self):
        PageHeader(self, "Current Balance",
                   "Query the live ETH balance of any wallet",
                   logo_color=ETH_ACCENT).pack(fill="x", padx=20, pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=12)
        form.pack(fill="x", padx=20, pady=6)
        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        self._addr = LabelledEntry(inner, "Wallet Address", placeholder="0x...")
        self._addr.pack(fill="x")

        # Action
        action = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=12)
        action.pack(fill="x", padx=20, pady=6)
        self._btn = ctk.CTkButton(
            action, text="Query Balance",
            height=42, width=180, corner_radius=10,
            fg_color=ETH_ACCENT, hover_color="#7340DC",
            font=ctk.CTkFont(size=FONT_XL, weight="bold"),
            command=self._start,
        )
        self._btn.pack(side="left", padx=16, pady=12)
        self._spinner = ctk.CTkLabel(action, text="",
                                     font=ctk.CTkFont(size=16), text_color=ETH_MUTED)
        self._spinner.pack(side="left")

        # Result card
        result = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=12)
        result.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        self._hint = ctk.CTkLabel(result,
                                  text="Enter a wallet address and click Query",
                                  font=ctk.CTkFont(size=14), text_color=ETH_MUTED)
        self._hint.pack(pady=(60, 4))

        self._bal_lbl = ctk.CTkLabel(result, text="",
                                     font=ctk.CTkFont(size=FONT_HERO, weight="bold"),
                                     text_color=ETH_ACCENT)
        self._bal_lbl.pack()

        self._sub_lbl = ctk.CTkLabel(result, text="",
                                     font=ctk.CTkFont(size=FONT_BASE),
                                     text_color=ETH_MUTED)
        self._sub_lbl.pack(pady=(4, 60))

    def _collect(self):
        try:
            if not AppState.has_api_key():
                raise ValidationError("No API key set. Enter it in the Settings panel.")
            return validate_wallet_address(self._addr.get())
        except ValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
            return None

    def _start(self):
        addr = self._collect()
        if addr is None:
            return
        self._btn.configure(state="disabled")
        self._bal_lbl.configure(text="")
        self._sub_lbl.configure(text="")
        self._hint.configure(text="Querying...", text_color=ETH_MUTED)
        self._animate(0)
        threading.Thread(target=self._worker, args=(addr,), daemon=True).start()

    def _animate(self, i):
        self._spinner.configure(text=_SPIN[i % len(_SPIN)])
        if self._btn.cget("state") == "disabled":
            self.after(80, self._animate, i + 1)
        else:
            self._spinner.configure(text="")

    def _worker(self, addr):
        try:
            bal = get_current_balance(addr, AppState.get_api_key())
            self.after(0, self._show, bal, addr)
        except Exception as exc:
            self.after(0, self._err, str(exc))

    def _show(self, bal, addr):
        self._hint.configure(text="Current balance (latest block)", text_color=ETH_MUTED)
        self._bal_lbl.configure(text=f"E {bal:,.6f}")
        self._sub_lbl.configure(text=addr)
        self._btn.configure(state="normal")

    def _err(self, msg):
        self._hint.configure(text=f"Error: {msg}", text_color=ETH_ERROR)
        self._bal_lbl.configure(text="")
        self._sub_lbl.configure(text="")
        self._btn.configure(state="normal")
        messagebox.showerror("Query Failed", msg)

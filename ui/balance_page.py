"""
ui/balance_page.py
Page 2 — Query ETH balance at a historical date & time.
"""

import threading
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from constants import (
    ETH_DARK, ETH_CARD, ETH_MUTED, ETH_TEXT, ETH_ERROR, ETH_ACCENT,
    FONT_BASE, FONT_SM, FONT_XL, FONT_HERO,
)
from core.api import get_block_number, get_eth_balance_at
from core.state import AppState
from core.validators import ValidationError, validate_wallet_address, validate_datetime
from ui.widgets import PageHeader, LabelledEntry, DateTimePicker

_SPIN = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]


class BalancePage(ctk.CTkFrame):

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=ETH_DARK, **kw)
        self._build()

    def _build(self):
        PageHeader(self, "Balance at Point in Time",
                   "Query ETH balance at any historical UTC date & time",
                   logo_color=ETH_ACCENT).pack(fill="x", padx=20, pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=12)
        form.pack(fill="x", padx=20, pady=6)
        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        self._addr = LabelledEntry(inner, "Wallet Address", placeholder="0x…")
        self._addr.pack(fill="x")

        self._dt = DateTimePicker(inner, "Date & Time",
                                  initial=datetime.utcnow().replace(second=0, microsecond=0))
        self._dt.pack(anchor="w", pady=(12, 0),padx=(5,5))

        # Action
        action = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=12)
        action.pack(fill="x", padx=20, pady=6)
        self._btn = ctk.CTkButton(
            action, text="🔍  Query Balance",
            height=42, width=200, corner_radius=10,
            fg_color=ETH_ACCENT, hover_color="#7340DC",
            font=ctk.CTkFont(size=FONT_XL, weight="bold"),
            command=self._start,
        )
        self._btn.pack(side="left", padx=16, pady=12)
        self._spinner = ctk.CTkLabel(action, text="", font=ctk.CTkFont(size=16),
                                     text_color=ETH_MUTED)
        self._spinner.pack(side="left")

        # Result
        result = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=12)
        result.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        self._hint = ctk.CTkLabel(result,
                                  text="Enter a wallet address and date, then click Query\n(balance is reconstructed from on-chain transactions — may take a moment)",
                                  font=ctk.CTkFont(size=14), text_color=ETH_MUTED)
        self._hint.pack(pady=(50, 4))

        self._bal_lbl = ctk.CTkLabel(result, text="",
                                     font=ctk.CTkFont(size=FONT_HERO, weight="bold"),
                                     text_color=ETH_ACCENT)
        self._bal_lbl.pack()

        self._block_lbl = ctk.CTkLabel(result, text="",
                                       font=ctk.CTkFont(size=FONT_BASE),
                                       text_color=ETH_MUTED)
        self._block_lbl.pack(pady=(4, 0))

        self._addr_lbl = ctk.CTkLabel(result, text="",
                                      font=ctk.CTkFont(family="Courier", size=FONT_SM),
                                      text_color=ETH_MUTED)
        self._addr_lbl.pack(pady=(2, 50))

    def _collect(self):
        try:
            if not AppState.has_api_key():
                raise ValidationError("No API key set. Enter it in the Settings panel.")
            addr = validate_wallet_address(self._addr.get())
            validate_datetime(self._dt.get_date(), self._dt.get_time())
            return dict(api_key=AppState.get_api_key(), addr=addr,
                        date=self._dt.get_date(), time=self._dt.get_time())
        except ValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
            return None

    def _start(self):
        p = self._collect()
        if p is None:
            return
        self._btn.configure(state="disabled")
        self._bal_lbl.configure(text="")
        self._block_lbl.configure(text="")
        self._addr_lbl.configure(text="")
        self._hint.configure(text="Querying Etherscan…", text_color=ETH_MUTED)
        self._animate(0)
        threading.Thread(target=self._worker, args=(p,), daemon=True).start()

    def _animate(self, i):
        self._spinner.configure(text=_SPIN[i % len(_SPIN)])
        if self._btn.cget("state") == "disabled":
            self.after(80, self._animate, i + 1)
        else:
            self._spinner.configure(text="")

    def _worker(self, p):
        try:
            block = get_block_number(p["date"], p["time"], "before", p["api_key"])
            bal   = get_eth_balance_at(p["addr"], block, p["api_key"])
            self.after(0, self._show, bal, block, p)
        except Exception as exc:
            self.after(0, self._err, str(exc))

    def _show(self, bal, block, p):
        self._hint.configure(text=f"Balance on  {p['date']}  {p['time']}  UTC",
                             text_color=ETH_MUTED)
        self._bal_lbl.configure(text=f"Ξ {bal:,.6f}")
        self._block_lbl.configure(text=f"at block #{block:,}")
        self._addr_lbl.configure(text=p["addr"])
        self._btn.configure(state="normal")

    def _err(self, msg):
        self._hint.configure(text=f"Error: {msg}", text_color=ETH_ERROR)
        self._bal_lbl.configure(text="")
        self._block_lbl.configure(text="")
        self._btn.configure(state="normal")
        messagebox.showerror("Query Failed", msg)

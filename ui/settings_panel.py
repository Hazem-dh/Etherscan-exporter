"""
ui/settings_panel.py
Sidebar API-key panel.

How it works:
  1. Paste your Etherscan API key into the field.
  2. Click "Activate Key" — the key is stored in memory for the session.
  3. The status line confirms it is active. All API calls will use it.
  You do NOT need to re-enter it on every launch unless you restart the app.
"""

import tkinter as tk
import customtkinter as ctk

from constants import (
    ETH_CARD, ETH_DARKER, ETH_BORDER, ETH_MUTED,
    ETH_BLUE, ETH_SUCCESS, ETH_WARN, ETH_TEXT,
    FONT_BASE, FONT_SM, FONT_LG,
)
from core.state import AppState
from core.validators import ValidationError


class SettingsPanel(ctk.CTkFrame):

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=ETH_CARD, corner_radius=12, **kw)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="⚙  API Settings",
                     font=ctk.CTkFont(size=FONT_LG, weight="bold"),
                     text_color=ETH_MUTED).pack(anchor="w", padx=14, pady=(14, 2))

        # ── Explanatory hint ──────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Enter your free Etherscan API\nkey to enable all features.",
            font=ctk.CTkFont(size=FONT_SM), text_color=ETH_MUTED,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 6))

        ctk.CTkLabel(self, text="API Key",
                     font=ctk.CTkFont(size=FONT_BASE),
                     text_color=ETH_MUTED).pack(anchor="w", padx=14)

        self._key_var = tk.StringVar()
        self._key_entry = ctk.CTkEntry(
            self, textvariable=self._key_var, show="•",
            placeholder_text="Paste key here…",
            width=180, height=34, corner_radius=8,
            border_color=ETH_BORDER, fg_color=ETH_DARKER,
        )
        self._key_entry.pack(padx=14, pady=(3, 4))

        self._show_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self, text="Show key", variable=self._show_var,
            command=lambda: self._key_entry.configure(
                show="" if self._show_var.get() else "•"),
            font=ctk.CTkFont(size=FONT_SM), text_color=ETH_MUTED,
            checkbox_width=14, checkbox_height=14,
        ).pack(anchor="w", padx=14)

        # Status: shows active key (masked) or warning
        self._status = ctk.CTkLabel(self, text="No key set",
                                    font=ctk.CTkFont(size=FONT_SM),
                                    text_color=ETH_WARN)
        self._status.pack(anchor="w", padx=14, pady=(4, 0))

        ctk.CTkButton(
            self, text="Activate Key",
            height=32, width=120,
            fg_color=ETH_BLUE, hover_color="#4F6DD4",
            corner_radius=8,
            font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
            command=self._activate,
        ).pack(anchor="w", padx=14, pady=(8, 14))

    def _activate(self):
        key = self._key_var.get().strip()
        if not key:
            self._status.configure(text="⚠ Key is empty", text_color=ETH_WARN)
            return
        AppState.set_api_key(key)
        masked = key[:4] + "••••" + key[-4:] if len(key) >= 8 else "••••"
        self._status.configure(text=f"✓ Active: {masked}", text_color=ETH_SUCCESS)

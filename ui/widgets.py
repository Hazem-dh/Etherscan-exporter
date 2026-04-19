"""
ui/widgets.py
Reusable widgets: ETH logo, DateTimePicker, LabelledEntry, Divider, PageHeader.
"""

import tkinter as tk
from datetime import datetime, date
import calendar

import customtkinter as ctk

from constants import (
    ETH_BLUE, ETH_CARD, ETH_DARKER, ETH_BORDER, ETH_MUTED, ETH_TEXT,
    ETH_ACCENT, ETH_DARK, ETH_ERROR,
    FONT_BASE, FONT_SM, FONT_LG, FONT_XL,
)


# ── ETH diamond ───────────────────────────────────────────────────────────────
def draw_eth_logo(canvas: tk.Canvas, cx, cy, size=28, color=ETH_BLUE):
    s = size / 28
    canvas.create_polygon([cx, cy-14*s, cx-7*s, cy-4*s, cx+7*s, cy-4*s], fill=color, outline="")
    canvas.create_polygon([cx, cy-2*s,  cx-7*s, cy-4*s, cx,     cy+2*s], fill=color, outline="")
    canvas.create_polygon([cx, cy-2*s,  cx+7*s, cy-4*s, cx,     cy+2*s], fill="#9BB5F2", outline="")
    canvas.create_polygon([cx, cy+14*s, cx-7*s, cy+4*s, cx+7*s, cy+4*s], fill=color, outline="")


# ── Divider ───────────────────────────────────────────────────────────────────
class Divider(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, height=1, fg_color=ETH_BORDER, **kw)


# ── Page Header ───────────────────────────────────────────────────────────────
class PageHeader(ctk.CTkFrame):
    def __init__(self, master, title, subtitle, logo_color=ETH_BLUE, **kw):
        super().__init__(master, fg_color=ETH_CARD, corner_radius=12, **kw)
        lc = tk.Canvas(self, width=34, height=34, bg=ETH_CARD, highlightthickness=0)
        lc.pack(side="left", padx=(16, 8), pady=10)
        draw_eth_logo(lc, 17, 17, size=30, color=logo_color)
        tf = ctk.CTkFrame(self, fg_color="transparent")
        tf.pack(side="left", pady=10)
        ctk.CTkLabel(tf, text=title, font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=ETH_TEXT).pack(anchor="w")
        ctk.CTkLabel(tf, text=subtitle, font=ctk.CTkFont(size=FONT_BASE),
                     text_color=ETH_MUTED).pack(anchor="w")


# ── Calendar popup ────────────────────────────────────────────────────────────
class _CalendarPopup(tk.Toplevel):
    def __init__(self, master, initial: date, callback):
        super().__init__(master)
        self._callback = callback
        self._year  = initial.year
        self._month = initial.month
        self._sel   = initial
        self.overrideredirect(True)
        self.configure(bg=ETH_CARD)
        self.resizable(False, False)
        self._build()
        self._position(master)
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _position(self, master):
        master.update_idletasks()
        x = master.winfo_rootx()
        y = master.winfo_rooty() + master.winfo_height() + 4
        self.geometry(f"+{x}+{y}")

    def _build(self):
        nav = tk.Frame(self, bg=ETH_CARD)
        nav.pack(fill="x", padx=8, pady=(8, 0))
        tk.Button(nav, text="<", bg=ETH_CARD, fg=ETH_TEXT, relief="flat",
                  font=("Arial", 13, "bold"), activebackground=ETH_BORDER,
                  command=self._prev).pack(side="left")
        self._title_var = tk.StringVar()
        tk.Label(nav, textvariable=self._title_var, bg=ETH_CARD, fg=ETH_TEXT,
                 font=("Arial", 11, "bold"), width=14).pack(side="left", expand=True)
        tk.Button(nav, text=">", bg=ETH_CARD, fg=ETH_TEXT, relief="flat",
                  font=("Arial", 13, "bold"), activebackground=ETH_BORDER,
                  command=self._next).pack(side="right")
        dow_row = tk.Frame(self, bg=ETH_CARD)
        dow_row.pack(padx=8)
        for d in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"):
            tk.Label(dow_row, text=d, bg=ETH_CARD, fg=ETH_MUTED,
                     font=("Arial", 9), width=3).pack(side="left")
        self._grid = tk.Frame(self, bg=ETH_CARD)
        self._grid.pack(padx=8, pady=(0, 8))
        self._render()

    def _render(self):
        for w in self._grid.winfo_children():
            w.destroy()
        self._title_var.set(f"{calendar.month_abbr[self._month]} {self._year}")
        for week in calendar.monthcalendar(self._year, self._month):
            row = tk.Frame(self._grid, bg=ETH_CARD)
            row.pack()
            for day in week:
                if day == 0:
                    tk.Label(row, text="", width=3, bg=ETH_CARD).pack(side="left")
                else:
                    is_sel = (day == self._sel.day and
                              self._month == self._sel.month and
                              self._year  == self._sel.year)
                    tk.Button(
                        row, text=str(day), width=3, relief="flat",
                        bg=ETH_BLUE if is_sel else ETH_CARD,
                        fg=ETH_TEXT, activebackground=ETH_BORDER,
                        font=("Arial", 10),
                        command=lambda d=day: self._pick(d),
                    ).pack(side="left")

    def _prev(self):
        self._month -= 1
        if self._month == 0:
            self._month, self._year = 12, self._year - 1
        self._render()

    def _next(self):
        self._month += 1
        if self._month == 13:
            self._month, self._year = 1, self._year + 1
        self._render()

    def _pick(self, day):
        self._sel = date(self._year, self._month, day)
        self._callback(self._sel)
        self.destroy()


# ── _TimeField: single numeric field (HH, MM or SS) ──────────────────────────
class _TimeField(ctk.CTkEntry):
    """
    A 2-digit numeric-only entry for hours, minutes, or seconds.
    - Rejects non-digit keypresses.
    - Turns red border when value is out of range.
    - Auto-advances focus to `next_widget` after 2 digits are entered.
    """

    def __init__(self, master, max_val: int, next_widget=None, **kw):
        self._max   = max_val
        self._next  = next_widget
        self._var   = tk.StringVar()
        super().__init__(
            master,
            textvariable=self._var,
            width=52, height=36, corner_radius=8,
            border_color=ETH_BORDER, fg_color=ETH_DARKER,
            font=ctk.CTkFont(family="Courier", size=FONT_BASE),
            justify="center",
            **kw,
        )
        # Validate: digits only, max 2 chars
        vcmd = (self.register(self._validate_char), "%P")
        self.configure(validate="key", validatecommand=vcmd)
        self._var.trace_add("write", self._on_change)

    def _validate_char(self, new_val: str) -> bool:
        return new_val == "" or (new_val.isdigit() and len(new_val) <= 2)

    def _on_change(self, *_):
        val = self._var.get()
        # Range check → red border
        if val == "" or (val.isdigit() and 0 <= int(val) <= self._max):
            self.configure(border_color=ETH_BORDER)
        else:
            self.configure(border_color=ETH_ERROR)
        # Auto-advance after 2 digits
        if len(val) == 2 and self._next:
            self._next.focus_set()

    def get_value(self) -> int | None:
        """Return int value if valid, else None."""
        val = self._var.get()
        if val.isdigit() and 0 <= int(val) <= self._max:
            return int(val)
        return None

    def set_value(self, v: int):
        self._var.set(f"{v:02d}")


# ── DateTimePicker ────────────────────────────────────────────────────────────
class DateTimePicker(ctk.CTkFrame):
    """
    Date picker button (calendar popup) + three numeric fields HH | MM | SS.
    get_date() -> "YYYY-MM-DD"
    get_time() -> "HH:MM:SS"   (raises ValueError if any field is invalid)
    get()      -> "YYYY-MM-DD HH:MM:SS"
    """

    def __init__(self, master, label: str, initial: datetime | None = None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        if initial is None:
            initial = datetime.utcnow().replace(second=0, microsecond=0)
        self._date = initial.date()

        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=FONT_BASE),
                     text_color=ETH_MUTED, anchor="w").pack(anchor="w", pady=(0, 2))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")

        # Date button
        self._date_var = tk.StringVar(value=str(self._date))
        self._date_btn = ctk.CTkButton(
            row, textvariable=self._date_var,
            width=130, height=36, corner_radius=8,
            fg_color=ETH_DARKER, hover_color=ETH_BORDER,
            border_width=1, border_color=ETH_BORDER,
            text_color=ETH_TEXT, font=ctk.CTkFont(size=FONT_BASE),
            command=self._open_cal,
        )
        self._date_btn.pack(side="left")


        # Three time fields, auto-advance H -> M -> S
        self._s_field = _TimeField(row, max_val=59)
        self._m_field = _TimeField(row, max_val=59, next_widget=self._s_field)
        self._h_field = _TimeField(row, max_val=23, next_widget=self._m_field)

        self._h_field.set_value(initial.hour)
        self._m_field.set_value(initial.minute)
        self._s_field.set_value(initial.second)

        self._h_field.pack(side="left")
        ctk.CTkLabel(row, text=":", fg_color="transparent",
                     font=ctk.CTkFont(family="Courier", size=14, weight="bold"),
                     text_color=ETH_MUTED).pack(side="left", padx=1)
        self._m_field.pack(side="left")
        ctk.CTkLabel(row, text=":", fg_color="transparent",
                     font=ctk.CTkFont(family="Courier", size=14, weight="bold"),
                     text_color=ETH_MUTED).pack(side="left", padx=1)
        self._s_field.pack(side="left")
        ctk.CTkLabel(row, text="UTC", font=ctk.CTkFont(size=FONT_SM),
                     text_color=ETH_MUTED).pack(side="left", padx=(6, 0))

    def _open_cal(self):
        _CalendarPopup(self._date_btn, self._date, self._on_pick)

    def _on_pick(self, d: date):
        self._date = d
        self._date_var.set(str(d))

    def get_date(self) -> str:
        return str(self._date)

    def get_time(self) -> str:
        h = self._h_field.get_value()
        m = self._m_field.get_value()
        s = self._s_field.get_value()
        if h is None or m is None or s is None:
            raise ValueError("Invalid time — check that hours (0-23), minutes and seconds (0-59) are correct.")
        return f"{h:02d}:{m:02d}:{s:02d}"

    def get(self) -> str:
        return f"{self.get_date()} {self.get_time()}"


# ── LabelledEntry ─────────────────────────────────────────────────────────────
class LabelledEntry(ctk.CTkFrame):
    def __init__(self, master, label: str, placeholder: str = "", width: int = 0, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=FONT_BASE),
                     text_color=ETH_MUTED, anchor="w").pack(anchor="w", pady=(0, 2))
        kw2 = dict(placeholder_text=placeholder, height=36, corner_radius=8,
                   border_color=ETH_BORDER, fg_color=ETH_DARKER)
        if width:
            kw2["width"] = width
        self.entry = ctk.CTkEntry(self, **kw2)
        self.entry.pack(fill="x")

    def get(self) -> str:
        return self.entry.get()

    def insert(self, index, text: str):
        self.entry.insert(index, text)

    def configure(self, **kw):
        self.entry.configure(**kw)

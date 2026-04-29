"""
ui/transaction_page.py
Page — Extract normal or internal transactions and export to CSV.
Instantiated twice (once per type) by app.py.
"""

import threading
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd

from constants import (
    ETH_DARK, ETH_CARD, ETH_DARKER, ETH_BORDER,
    ETH_BLUE, ETH_MUTED, ETH_TEXT, ETH_SUCCESS, ETH_ERROR, ETH_WARN,
    FONT_BASE, FONT_SM, FONT_XL,
)
from core.api import get_block_number, fetch_all_transactions, fetch_all_internal_transactions
from core.state import AppState
from core.validators import (
    ValidationError, validate_wallet_address,
    validate_datetime, validate_date_range, resolve_output_path,
)
from ui.widgets import PageHeader, LabelledEntry, DateTimePicker


class TransactionPage(ctk.CTkFrame):

    def __init__(self, master, preset_type: str = "normal", **kw):
        super().__init__(master, fg_color=ETH_DARK, **kw)
        self._out_folder = ""
        self._tx_type    = preset_type          # "normal" | "internal"
        self._build()

    def _build(self):
        subtitle = ("Export internal transactions to CSV"
                    if self._tx_type == "internal"
                    else "Export normal transactions to CSV")
        PageHeader(self, "Transaction Extractor", subtitle).pack(
            fill="x", padx=20, pady=(20, 10))

        form = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=12)
        form.pack(fill="x", padx=20, pady=6)
        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        self._addr = LabelledEntry(inner, "Wallet Address", placeholder="0x...")
        self._addr.pack(fill="x")

        # Date/time pickers
        dt_row = ctk.CTkFrame(inner, fg_color="transparent")
        dt_row.pack(fill="x", pady=(12, 0))
        self._start_dt = DateTimePicker(dt_row, "Start Date & Time",
                                        initial=datetime(datetime.now().year, 1, 1, 0, 0, 0))
        self._start_dt.pack(side="left", padx=(0, 24))
        self._end_dt = DateTimePicker(dt_row, "End Date & Time",
                                      initial=datetime.now())
        self._end_dt.pack(side="left")

        # Output
        out_sec = ctk.CTkFrame(inner, fg_color="transparent")
        out_sec.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(out_sec, text="Output File Name",
                     font=ctk.CTkFont(size=FONT_BASE),
                     text_color=ETH_MUTED).pack(anchor="w")
        out_row = ctk.CTkFrame(out_sec, fg_color="transparent")
        out_row.pack(fill="x")
        self._fname = ctk.CTkEntry(out_row, placeholder_text="transactions.csv",
                                   height=36, corner_radius=8,
                                   border_color=ETH_BORDER, fg_color=ETH_DARKER)
        self._fname.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(out_row, text="Choose Folder", width=130, height=36,
                      fg_color=ETH_BORDER, hover_color="#3A4560", corner_radius=8,
                      font=ctk.CTkFont(size=FONT_BASE),
                      command=self._pick_folder).pack(side="left", padx=(8, 0))
        self._folder_lbl = ctk.CTkLabel(out_row, text="Default: Desktop",
                                        font=ctk.CTkFont(size=FONT_SM),
                                        text_color=ETH_MUTED)
        self._folder_lbl.pack(side="left", padx=(10, 0))

        # Action bar
        action = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=12)
        action.pack(fill="x", padx=20, pady=6)
        self._run_btn = ctk.CTkButton(
            action, text=">> Extract Transactions",
            height=42, width=220, corner_radius=10,
            fg_color=ETH_BLUE, hover_color="#4F6DD4",
            font=ctk.CTkFont(size=FONT_XL, weight="bold"),
            command=self._start,
        )
        self._run_btn.pack(side="left", padx=16, pady=12)
        self._progress = ctk.CTkProgressBar(action, width=240, height=8,
                                            corner_radius=4, progress_color=ETH_BLUE)
        self._progress.set(0)
        self._progress.pack(side="left", padx=(0, 16), pady=12)
        self._status = ctk.CTkLabel(action, text="Ready",
                                    font=ctk.CTkFont(size=FONT_BASE),
                                    text_color=ETH_MUTED)
        self._status.pack(side="left")

        # Log
        log_card = ctk.CTkFrame(self, fg_color=ETH_CARD, corner_radius=12)
        log_card.pack(fill="both", expand=True, padx=20, pady=(6, 20))
        ctk.CTkLabel(log_card, text="Activity Log",
                     font=ctk.CTkFont(size=FONT_BASE, weight="bold"),
                     text_color=ETH_MUTED).pack(anchor="w", padx=16, pady=(10, 4))
        self._log_box = ctk.CTkTextbox(
            log_card, height=130, corner_radius=8,
            fg_color=ETH_DARKER,
            font=ctk.CTkFont(family="Courier", size=FONT_SM),
            text_color=ETH_TEXT, state="disabled")
        self._log_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self._out_folder = folder
            short = folder if len(folder) < 42 else "..." + folder[-39:]
            self._folder_lbl.configure(text=short)

    def _log(self, msg: str):
        self._log_box.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_box.insert("end", f"[{ts}] {msg}\n")
        self._log_box.configure(state="disabled")
        self._log_box.see("end")

    def _set_status(self, msg, color=ETH_MUTED):
        self._status.configure(text=msg, text_color=color)

    def _collect_params(self):
        try:
            if not AppState.has_api_key():
                raise ValidationError("No API key set. Enter it in the Settings panel.")
            addr = validate_wallet_address(self._addr.get())
            sdt  = validate_datetime(self._start_dt.get_date(),
                                     self._start_dt.get_time(), "Start")
            edt  = validate_datetime(self._end_dt.get_date(),
                                     self._end_dt.get_time(), "End")
            validate_date_range(sdt, edt)
            out  = resolve_output_path(self._out_folder, self._fname.get())
            return dict(api_key=AppState.get_api_key(), addr=addr,
                        sdate=self._start_dt.get_date(), stime=self._start_dt.get_time(),
                        edate=self._end_dt.get_date(),   etime=self._end_dt.get_time(),
                        out_path=out)
        except ValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
            return None

    def _start(self):
        p = self._collect_params()
        if p is None:
            return
        self._run_btn.configure(state="disabled")
        self._progress.set(0)
        threading.Thread(target=self._worker, args=(p,), daemon=True).start()

    def _worker(self, p):
        label    = "internal" if self._tx_type == "internal" else "normal"
        fetch_fn = (fetch_all_internal_transactions
                    if self._tx_type == "internal"
                    else fetch_all_transactions)
        try:
            self._set_status("Resolving start block...")
            self._log("Resolving start block...")
            sb = get_block_number(p["sdate"], p["stime"], "after",  p["api_key"])
            self._log(f"Start block: {sb:,}")

            self._set_status("Resolving end block...")
            self._log("Resolving end block...")
            eb = get_block_number(p["edate"], p["etime"], "before", p["api_key"])
            self._log(f"End block:   {eb:,}")

            self._progress.set(0.15)
            self._set_status(f"Downloading {label} transactions...", ETH_BLUE)
            self._log(f"Fetching {label} transactions...")

            txs = fetch_fn(
                p["addr"], sb, eb, p["api_key"],
                progress_cb=lambda n, pg: self._log(f"  Page {pg+1}: {n:,} txs so far"))
            self._progress.set(0.85)

            if not txs:
                self._log(f"No {label} transactions found in this range.")
                self._set_status("No transactions found", ETH_WARN)
                return

            self._log(f"Total: {len(txs):,} — writing CSV...")
            df = pd.DataFrame(txs)
            if "value" in df.columns:
                df["value_eth"] = df["value"].astype(float) / 1e18
            df.to_csv(p["out_path"], index=False)
            self._progress.set(1.0)
            self._log(f"Saved -> {p['out_path']}")
            self._set_status(f"{len(txs):,} transactions exported", ETH_SUCCESS)
            messagebox.showinfo("Done",
                f"Exported {len(txs):,} {label} transactions to:\n{p['out_path']}")
        except Exception as exc:
            self._log(f"Error: {exc}")
            self._set_status("Error — see log", ETH_ERROR)
            messagebox.showerror("Error", str(exc))
        finally:
            self._run_btn.configure(state="normal")

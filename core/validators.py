"""
core/validators.py
Pure-Python input validation — no UI imports.
"""

import os
from datetime import datetime


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def validate_wallet_address(addr: str) -> str:
    addr = addr.strip()
    if not addr.startswith("0x") or len(addr) != 42:
        raise ValidationError(
            "Wallet address must start with 0x and be exactly 42 characters long."
        )
    return addr


def validate_datetime(date_str: str, time_str: str, label: str = "") -> datetime:
    prefix = f"{label} " if label else ""
    try:
        return datetime.strptime(f"{date_str.strip()} {time_str.strip()}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValidationError(f"{prefix}Date/time must be  YYYY-MM-DD  HH:MM:SS")


def validate_date_range(start_dt: datetime, end_dt: datetime) -> None:
    if end_dt < start_dt:
        raise ValidationError("End date/time must be after start date/time.")


def resolve_output_path(folder: str, filename: str) -> str:
    filename = filename.strip() or "transactions.csv"
    if not filename.endswith(".csv"):
        filename += ".csv"
    if not folder or not os.path.isdir(folder):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        folder  = desktop if os.path.isdir(desktop) else os.path.expanduser("~")
    return os.path.join(folder, filename)

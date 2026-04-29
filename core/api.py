"""
core/api.py
All Etherscan API v2 calls, isolated from UI logic.
"""

import time
from datetime import datetime

import requests

_BASE     = "https://api.etherscan.io/v2/api"
_CHAIN_ID = "1"


def _get(params: dict, timeout: int = 15) -> dict:
    r = requests.get(_BASE, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _p(api_key: str, module: str, action: str) -> dict:
    return {"chainid": _CHAIN_ID, "module": module, "action": action, "apikey": api_key}


# ── Block ──────────────────────────────────────────────────────────────────────
def get_block_number(date_str: str, time_str: str, strategy: str, api_key: str) -> int:
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    p  = _p(api_key, "block", "getblocknobytime")
    p.update({"timestamp": int(dt.timestamp()), "closest": strategy})
    data = _get(p)
    if data["status"] != "1":
        raise ValueError(f"Block lookup failed: {data.get('message', 'unknown')}")
    return int(data["result"])


# ── Current balance (free tier, latest block) ─────────────────────────────────
def get_current_balance(address: str, api_key: str) -> float:
    """Return the current ETH balance using the simple free-tier endpoint."""
    p = _p(api_key, "account", "balance")
    p.update({"address": address, "tag": "latest"})
    data = _get(p)
    if data["status"] != "1":
        raise ValueError(f"Balance fetch failed: {data.get('message', 'unknown')}")
    return int(data["result"]) / 1e18


# ── Paginated transaction fetcher (shared by normal + internal) ───────────────
def _fetch_pages(address, start_block, end_block, api_key, action, progress_cb=None) -> list:
    all_txs, cur_start, page = [], start_block, 0
    while True:
        p = _p(api_key, "account", action)
        p.update({"address": address, "startblock": cur_start,
                  "endblock": end_block, "sort": "asc"})
        data = _get(p)
        if data["status"] == "1":
            txs = data["result"]
        elif data.get("message") == "No transactions found":
            break
        else:
            raise ValueError(f"Fetch failed ({action}): {data.get('result', data.get('message'))}")
        all_txs.extend(txs)
        if progress_cb:
            progress_cb(len(all_txs), page)
        page += 1
        if len(txs) < 10_000:
            break
        cur_start = int(txs[-1]["blockNumber"]) + 1
        time.sleep(0.3)
    return all_txs


def fetch_all_transactions(address, start_block, end_block, api_key, progress_cb=None) -> list:
    """Normal transactions (txlist)."""
    return _fetch_pages(address, start_block, end_block, api_key, "txlist", progress_cb)


def fetch_all_internal_transactions(address, start_block, end_block, api_key, progress_cb=None) -> list:
    """Internal transactions (txlistinternal)."""
    return _fetch_pages(address, start_block, end_block, api_key, "txlistinternal", progress_cb)

"""
core/api.py
All Etherscan API v2 calls, isolated from UI logic.

Free-tier historical balance strategy
--------------------------------------
Etherscan's `balancehistory` endpoint requires a Pro API key.
For free-tier keys we reconstruct the historical balance by:
  1. Fetching all normal outbound/inbound transactions up to `block_number`.
  2. Fetching all internal transactions up to `block_number`.
  3. Summing net ETH received − sent − gas fees paid.
This is accurate for standard EOA (non-contract) wallets.
"""

import time
from datetime import datetime

import requests

_BASE     = "https://api.etherscan.io/v2/api"
_CHAIN_ID = "1"   # Ethereum mainnet


# ── Internals ─────────────────────────────────────────────────────────────────
def _get(params: dict, timeout: int = 15) -> dict:
    r = requests.get(_BASE, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _p(api_key: str, module: str, action: str) -> dict:
    """Base params required by every v2 request."""
    return {"chainid": _CHAIN_ID, "module": module,
            "action": action, "apikey": api_key}


# ── Block helpers ─────────────────────────────────────────────────────────────
def get_block_number(date_str: str, time_str: str, strategy: str, api_key: str) -> int:
    """Return the block number closest to a UTC date/time."""
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    p  = _p(api_key, "block", "getblocknobytime")
    p.update({"timestamp": int(dt.timestamp()), "closest": strategy})
    data = _get(p)
    if data["status"] != "1":
        raise ValueError(f"Block lookup failed: {data.get('message', 'unknown')}")
    return int(data["result"])


# ── Transaction helpers ───────────────────────────────────────────────────────
def _paginate(address: str, end_block: int, api_key: str, action: str) -> list:
    """
    Fetch all pages of `action` (txlist or txlistinternal) from block 0
    up to end_block for the given address.
    """
    all_txs, start = [], 0
    while True:
        p = _p(api_key, "account", action)
        p.update({"address": address, "startblock": start,
                  "endblock": end_block, "sort": "asc"})
        data = _get(p)
        if data["status"] == "1":
            txs = data["result"]
        elif data.get("message") == "No transactions found":
            break
        else:
            # Non-fatal: internal txs endpoint may return NOTOK on some wallets
            break
        all_txs.extend(txs)
        if len(txs) < 10_000:
            break
        start = int(txs[-1]["blockNumber"]) + 1
        time.sleep(0.25)
    return all_txs


def fetch_all_transactions(
    address: str,
    start_block: int,
    end_block: int,
    api_key: str,
    progress_cb=None,
) -> list:
    """Paginate normal transactions between start_block and end_block."""
    all_txs, cur_start, page = [], start_block, 0
    while True:
        p = _p(api_key, "account", "txlist")
        p.update({"address": address, "startblock": cur_start,
                  "endblock": end_block, "sort": "asc"})
        data = _get(p)
        if data["status"] == "1":
            txs = data["result"]
        elif data.get("message") == "No transactions found":
            break
        else:
            raise ValueError(f"TX fetch failed: {data.get('result', data.get('message'))}")
        all_txs.extend(txs)
        if progress_cb:
            progress_cb(len(all_txs), page)
        page += 1
        if len(txs) < 10_000:
            break
        cur_start = int(txs[-1]["blockNumber"]) + 1
        time.sleep(0.3)
    return all_txs


# ── Balance helper (free-tier) ────────────────────────────────────────────────
def get_eth_balance_at(address: str, block_number: int, api_key: str) -> float:
    """
    Reconstruct the ETH balance of *address* at *block_number* using
    only free-tier Etherscan endpoints.

    Method
    ------
    For each normal transaction up to block_number:
      - If sent by address: subtract value + gas_used * gas_price
      - If received by address: add value
    For each internal transaction up to block_number:
      - Add/subtract value accordingly
    """
    addr_lower = address.lower()

    normal_txs   = _paginate(address, block_number, api_key, "txlist")
    internal_txs = _paginate(address, block_number, api_key, "txlistinternal")

    balance_wei = 0

    for tx in normal_txs:
        value     = int(tx.get("value",    0))
        gas_used  = int(tx.get("gasUsed",  tx.get("gas", 0)))
        gas_price = int(tx.get("gasPrice", 0))
        sender    = tx.get("from", "").lower()
        receiver  = tx.get("to",   "").lower()
        is_error  = tx.get("isError", "0") == "1"

        if sender == addr_lower:
            # Gas is always burned even if the tx failed
            balance_wei -= gas_used * gas_price
            if not is_error:
                balance_wei -= value

        if receiver == addr_lower and not is_error:
            balance_wei += value

    for tx in internal_txs:
        value    = int(tx.get("value", 0))
        sender   = tx.get("from", "").lower()
        receiver = tx.get("to",   "").lower()
        is_error = tx.get("isError", "0") == "1"

        if is_error:
            continue
        if receiver == addr_lower:
            balance_wei += value
        if sender == addr_lower:
            balance_wei -= value

    if balance_wei < 0:
        # Can happen for very old wallets pre-dating Etherscan index; clamp to 0
        balance_wei = 0

    return balance_wei / 1e18

# ETH Explorer

A professional desktop application to explore Ethereum wallet activity using the **Etherscan API v2** — extract full transaction history to CSV and reconstruct historical ETH balances, all from a clean CustomTkinter GUI.

***

## Features

- **Transaction Extractor** — export all normal transactions for any wallet address within a custom date range to a `.csv` file
- **Historical Balance Checker** — reconstruct the ETH balance of any wallet at any point in time (free-tier compatible, no Pro API key required)
- **Date & time pickers** — calendar popup for date selection, validated numeric fields for time (HH / MM / SS)
- **Etherscan API v2** — uses the latest v2 endpoint with `chainid` parameter
- **Session API key** — enter your key once per session via the Settings panel; masked display for security

***

## Requirements

- Python 3.11+
- A free [Etherscan API key](https://etherscan.io/myapikey)

***

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/your-username/eth-explorer.git
cd eth-explorer/eth_explorer
```

Create and activate a virtual environment (recommended):

```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

***

## Usage

Run the app directly from inside the `eth_explorer/` folder:

```bash
python main.py
```

### Step 1 — Enter your API key

In the left sidebar, paste your Etherscan API key and click **Activate Key**. The key is stored in memory for the session.

### Step 2 — Extract Transactions

1. Navigate to **Transaction Extractor**
2. Enter a wallet address (`0x…`)
3. Select a start and end date using the calendar pickers, and enter the time (UTC)
4. Choose an output folder and file name
5. Click **>> Extract Transactions**

The CSV will include all normal transactions in the block range, with an extra `value_eth` column (value converted from Wei to ETH).

### Step 3 — Check Historical Balance

1. Navigate to **Balance Check**
2. Enter a wallet address and a UTC date & time
3. Click **Query Balance**

The balance is reconstructed by replaying all on-chain transactions (normal + internal) up to the target block — no Pro API key required.

> **Note:** Reconstruction time depends on transaction volume. Wallets with thousands of transactions may take a moment to query.

***

## Project Structure

```
eth_explorer/
├── main.py                   # Entry point — run this file
├── constants.py              # Colors, font sizes, window geometry
├── requirements.txt
├── core/
│   ├── api.py                # All Etherscan API v2 calls
│   ├── state.py              # Session-level app state (API key)
│   └── validators.py         # Input validation (address, datetime, paths)
└── ui/
    ├── app.py                # Root window + sidebar navigation
    ├── widgets.py            # DateTimePicker, LabelledEntry, PageHeader, ETH logo
    ├── settings_panel.py     # API key entry panel
    ├── transaction_page.py   # Transaction extractor page
    └── balance_page.py       # Historical balance page
```

***

## Dependencies

| Package | Purpose |
|---|---|
| `customtkinter` | Modern themed Tkinter GUI |
| `requests` | HTTP calls to Etherscan API |
| `pandas` | DataFrame construction and CSV export |
| `Pillow` | App icon generation |

***

## Free-tier Compatibility

All features work with a **free Etherscan API key**:

| Feature | Endpoint used | Tier |
|---|---|---|
| Block by timestamp | `block/getblocknobytime` | Free |
| Transaction list | `account/txlist` | Free |
| Internal transactions | `account/txlistinternal` | Free |
| Historical balance | Reconstructed from txlist + txlistinternal | Free |

The `account/balancehistory` Pro endpoint is intentionally not used.

***

## Edge Cases Handled

- Invalid wallet address format (must be `0x` + 42 chars)
- Time fields out of range (hours > 23, minutes/seconds > 59) — red border shown live
- End date before start date
- No transactions found in range
- Missing or inactive API key
- Network errors and Etherscan API error responses
- Output file name without `.csv` extension — auto-appended
- No folder selected — falls back to Desktop, then home directory

***

## Contributing

Contributions are welcome! To get started:

1. **Fork** the repository and create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes** — keep commits focused and descriptive.
3. **Test** your changes locally by running `python main.py`.
4. **Open a Pull Request** against the `main` branch with a clear description of what was changed and why.

### Guidelines

- Follow the existing project structure — UI logic stays in `ui/`, all API calls go in `core/api.py`
- Do not introduce new dependencies without discussion
- Keep the app free-tier compatible — do not add calls to Pro-only Etherscan endpoints without a clear free-tier fallback
- For large changes, open an issue first to discuss the approach before writing code

***

## Reporting Issues

If you encounter a bug or unexpected behaviour, please [open an issue](https://github.com/your-username/eth-explorer/issues) and include:

- **Python version** (`python --version`)
- **OS** (Windows / macOS / Linux)
- **Steps to reproduce** — what you did, what you expected, what happened instead
- **Error message or traceback** if applicable (copy from the Activity Log or terminal)

### Common Issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError` on launch | Dependencies not installed | Run `pip install -r requirements.txt` inside the venv |
| `?` shown on Extract button | Font does not support the icon character | Already fixed in latest version — re-download |
| Balance query returns `0.0` | Wallet has no indexed transactions | Expected for brand-new or contract-only addresses |
| `NOTOK` / Pro endpoint error | Using a free-tier key on a Pro action | Already handled — update to latest version |
| Calendar popup appears off-screen | Multi-monitor setup with different DPI | Move the app window closer to the centre of your primary screen |
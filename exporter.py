import os
import time
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

# loading env variables
load_dotenv()

# Replace with your API key from Etherscan
api_key = os.getenv("ETHERSCAN_API_KEY")

# Wallet address to extract data from
wallet_address = 'WALLET ADDRESS'



def get_block_number(dateblock, timeblock, strategy):
    # Convert date and time to Unix timestamp
    datetime_str = f"{dateblock} {timeblock}"
    datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    timestamp = int(datetime_obj.timestamp())

    # API endpoint URL
    url = f"https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={timestamp}&closest={strategy}&apikey={api_key}"

    # Make the API request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # Check if the response contains block number information
        if data['status'] == '1':
            block_number = int(data['result'])
            return block_number
        else:
            raise Exception("couldn't fetch blockNumer , check for request parameters")
    else:
        raise Exception("Fetching blockNumber failed")


# Function to fetch transactions in batches
def fetch_transactions(address, start_block, end_block):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock={start_block}&endblock={end_block}&sort=asc&apikey={api_key} "
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1':
            return data['result']
    return None


# Function to extract data from wallet
def extract_wallet_data(address, start_block, end_block):
    all_transactions = []
    while True:
        transactions = fetch_transactions(address, start_block, end_block)
        if transactions is None or len(transactions) == 0:
            break
        all_transactions.extend(transactions)
        start_block = int(transactions[-1]['blockNumber']) + 1  # Set start block for next batch
        time.sleep(0.3)  # Add a small delay to avoid hitting rate limits
    return all_transactions


# Main function
def main():
    # random blocks
    start_block = get_block_number("2023-01-01", "00:00:00", 'after')
    end_block = get_block_number("2023-12-31", "00:00:00", 'before')
    if end_block < start_block:
        raise Exception("Ending time is before beginning time")

    # extract data
    wallet_data = extract_wallet_data(wallet_address, start_block, end_block)
    if wallet_data:
        df = pd.DataFrame(wallet_data)
        df.to_csv('Batch Minter Signer.csv', index=False)
        print("Exported data successfully")
    else:
        print("Failed to fetch wallet data")


if __name__ == "__main__":
    main()

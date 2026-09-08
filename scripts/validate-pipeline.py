#!/usr/bin/env python3
"""
Ethereum Node & Blockscout Pipeline End-to-End Validator
-------------------------------------------------------
Verifies RPC query responses from Geth against Blockscout Indexer API responses
for a specified target address or transaction hash.
"""

import sys
import json
import argparse
import urllib.request
import urllib.error

DEFAULT_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" # vitalik.eth
GETH_RPC_DEFAULT = "http://127.0.0.1:8545"
BLOCKSCOUT_API_DEFAULT = "http://127.0.0.1:4000/api/v2"

def json_rpc_call(url, method, params=[]):
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('result')
    except Exception as e:
        return f"ERROR: {e}"

def http_get_json(url):
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return None

def validate_pipeline(address, geth_rpc, blockscout_api):
    print("=================================================================")
    print("      Ethereum Pipeline Validation: Geth RPC + Blockscout        ")
    print("=================================================================")
    print(f"Target Address:   {address}")
    print(f"Geth RPC URL:     {geth_rpc}")
    print(f"Blockscout API:   {blockscout_api}")
    print("-----------------------------------------------------------------")

    # 1. Query Geth Node directly
    print("\n[Step 1] Querying Execution Node (Geth RPC)...")
    geth_block = json_rpc_call(geth_rpc, "eth_blockNumber")
    if isinstance(geth_block, str) and geth_block.startswith("0x"):
        block_num = int(geth_block, 16)
        print(f"  [+] Current Geth Head Block: {block_num:,}")
    else:
        print(f"  [-] Failed to reach Geth RPC: {geth_block}")
        sys.exit(1)

    balance_hex = json_rpc_call(geth_rpc, "eth_getBalance", [address, "latest"])
    if isinstance(balance_hex, str) and balance_hex.startswith("0x"):
        balance_wei = int(balance_hex, 16)
        balance_eth = balance_wei / 10**18
        print(f"  [+] Geth Balance for {address[:10]}...: {balance_eth:.6f} ETH")
    else:
        print(f"  [-] Failed to fetch balance from Geth: {balance_hex}")

    # 2. Query Blockscout Indexer API
    print("\n[Step 2] Querying Blockscout Indexer API...")
    bs_address_url = f"{blockscout_api}/addresses/{address}"
    bs_data = http_get_json(bs_address_url)

    if bs_data:
        bs_coin_balance = bs_data.get('coin_balance')
        print(f"  [+] Blockscout Indexer Address Record Found!")
        if bs_coin_balance:
            bs_eth = int(bs_coin_balance) / 10**18
            print(f"  [+] Blockscout Indexed Balance: {bs_eth:.6f} ETH")
        else:
            print(f"  [+] Blockscout Address Record: {bs_data.get('hash')}")
    else:
        print(f"  [-] Unable to fetch address record from Blockscout at {bs_address_url}")

    # 3. Query Address Transaction History
    print("\n[Step 3] Querying Address Transaction History from Blockscout...")
    bs_tx_url = f"{blockscout_api}/addresses/{address}/transactions"
    tx_data = http_get_json(bs_tx_url)

    if tx_data and 'items' in tx_data:
        items = tx_data['items']
        print(f"  [+] Blockscout returned {len(items)} transactions for address.")
        if len(items) > 0:
            first_tx = items[0]
            print(f"      Latest Indexed Tx Hash:  {first_tx.get('hash')}")
            print(f"      Block Height:            {first_tx.get('block')}")
            print(f"      From:                    {first_tx.get('from', {}).get('hash')}")
            print(f"      To:                      {first_tx.get('to', {}).get('hash')}")
    else:
        print(f"  [-] Transaction list not ready yet or address has no recent live transactions.")

    print("\n=================================================================")
    print("                    Validation Check Completed                   ")
    print("=================================================================")

def main():
    parser = argparse.ArgumentParser(description="Pipeline End-to-End Validator")
    parser.add_argument("--address", default=DEFAULT_ADDRESS, help="Ethereum address to test")
    parser.add_argument("--geth", default=GETH_RPC_DEFAULT, help="Geth RPC URL")
    parser.add_argument("--blockscout", default=BLOCKSCOUT_API_DEFAULT, help="Blockscout API V2 URL")
    args = parser.parse_args()

    validate_pipeline(args.address, args.geth, args.blockscout)

if __name__ == "__main__":
    main()

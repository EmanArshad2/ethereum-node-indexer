#!/usr/bin/env python3
"""
Ethereum Execution (Geth) & Consensus (Lighthouse) Sync Monitor
----------------------------------------------------------------
Polls Geth JSON-RPC (eth_syncing, eth_blockNumber, net_peerCount)
and Lighthouse REST API (/eth/v1/node/syncing) to display realtime progress.
"""

import sys
import json
import time
import argparse
import urllib.request
import urllib.error

GETH_RPC_DEFAULT = "http://127.0.0.1:8545"
LIGHTHOUSE_REST_DEFAULT = "http://127.0.0.1:5052"

def json_rpc_call(url, method, params=[]):
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('result')
    except Exception as e:
        return None

def http_get(url):
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        return None

def print_progress_bar(percentage, length=30):
    filled = int(length * percentage // 100)
    bar = '█' * filled + '░' * (length - filled)
    return f"[{bar}] {percentage:.2f}%"

def check_geth_sync(geth_url):
    print("\n--- Geth Execution Client Status ---")
    sync_res = json_rpc_call(geth_url, "eth_syncing")
    block_num_hex = json_rpc_call(geth_url, "eth_blockNumber")
    peer_count_hex = json_rpc_call(geth_url, "net_peerCount")

    peers = int(peer_count_hex, 16) if peer_count_hex else 0
    current_block = int(block_num_hex, 16) if block_num_hex else 0

    print(f"Connected Peers: {peers}")

    if sync_res is False or sync_res is None:
        if block_num_hex is not None:
            print(f"Sync Status:     SYNCED (Head Block: {current_block:,})")
            print(print_progress_bar(100.0))
            return 100.0, current_block, current_block
        else:
            print(f"Sync Status:     OFFLINE / UNREACHABLE at {geth_url}")
            return 0.0, 0, 0
    elif isinstance(sync_res, dict):
        curr = int(sync_res.get('currentBlock', '0x0'), 16)
        highest = int(sync_res.get('highestBlock', '0x1'), 16)
        pct = (curr / highest * 100.0) if highest > 0 else 0.0
        print(f"Sync Status:     IN PROGRESS")
        print(f"Current Block:   {curr:,}")
        print(f"Highest Block:   {highest:,}")
        print(f"Blocks Remaining:{highest - curr:,}")
        print(print_progress_bar(pct))
        return pct, curr, highest

def check_lighthouse_sync(lh_url):
    print("\n--- Lighthouse Consensus Client Status ---")
    data = http_get(f"{lh_url}/eth/v1/node/syncing")
    if not data or 'data' not in data:
        print(f"Consensus Status: UNREACHABLE at {lh_url}")
        return

    info = data['data']
    is_syncing = info.get('is_syncing', False)
    head_slot = int(info.get('head_slot', 0))
    sync_distance = int(info.get('sync_distance', 0))
    target_slot = head_slot + sync_distance

    pct = ((head_slot / target_slot) * 100.0) if target_slot > 0 else 100.0

    if not is_syncing and sync_distance == 0:
        print(f"Sync Status:     SYNCED (Head Slot: {head_slot:,})")
        print(print_progress_bar(100.0))
    else:
        print(f"Sync Status:     IN PROGRESS")
        print(f"Head Slot:       {head_slot:,}")
        print(f"Target Slot:     {target_slot:,}")
        print(f"Slots Remaining: {sync_distance:,}")
        print(print_progress_bar(pct))

def main():
    parser = argparse.ArgumentParser(description="Ethereum Node Sync Monitor")
    parser.add_argument("--geth", default=GETH_RPC_DEFAULT, help="Geth JSON-RPC endpoint")
    parser.add_argument("--lighthouse", default=LIGHTHOUSE_REST_DEFAULT, help="Lighthouse REST endpoint")
    parser.add_argument("--watch", action="store_true", help="Continuously refresh every 5s")
    args = parser.parse_args()

    while True:
        if args.watch:
            print("\033[H\033[J", end="") # Clear terminal
        print("=================================================================")
        print("           Ethereum Execution & Consensus Sync Tracker           ")
        print("=================================================================")
        check_geth_sync(args.geth)
        check_lighthouse_sync(args.lighthouse)
        print("=================================================================")

        if not args.watch:
            break
        time.sleep(5)

if __name__ == "__main__":
    main()

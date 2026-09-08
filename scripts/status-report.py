#!/usr/bin/env python3
"""
Ethereum Node Status Report Generator
------------------------------------
Generates a structured status report detailing current sync %, disk space used,
block heights, and estimated time to full sync.
"""

import sys
import json
import shutil
import urllib.request
import urllib.error

GETH_RPC_DEFAULT = "http://127.0.0.1:8545"
LIGHTHOUSE_REST_DEFAULT = "http://127.0.0.1:5052"
BLOCKSCOUT_API_DEFAULT = "http://127.0.0.1:4000/api/v2"

def json_rpc_call(url, method, params=[]):
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('result')
    except Exception:
        return None

def http_get_json(url):
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        return None

def generate_report():
    print("=================================================================")
    print("        ETHEREUM NODE & INDEXER SYSTEM STATUS REPORT            ")
    print("=================================================================")

    # 1. Disk Usage
    total, used, free = shutil.disk_usage("/")
    pct_used = (used / total) * 100.0
    print(f"STORAGE STATS:")
    print(f"  Total Storage:    {total / (1024**3):.2f} GB")
    print(f"  Used Storage:     {used / (1024**3):.2f} GB ({pct_used:.2f}%)")
    print(f"  Free Storage:     {free / (1024**3):.2f} GB")
    print("-----------------------------------------------------------------")

    # 2. Geth Execution Client Status
    sync_res = json_rpc_call(GETH_RPC_DEFAULT, "eth_syncing")
    block_num_hex = json_rpc_call(GETH_RPC_DEFAULT, "eth_blockNumber")

    print("EXECUTION CLIENT (GETH):")
    if sync_res is False and block_num_hex:
        curr_block = int(block_num_hex, 16)
        print(f"  Status:           FULLY SYNCED")
        print(f"  Current Block:    #{curr_block:,}")
        print(f"  Sync Progress:    100.00%")
        print(f"  Estimated Time:   Synced (0 minutes remaining)")
    elif isinstance(sync_res, dict):
        curr = int(sync_res.get('currentBlock', '0x0'), 16)
        highest = int(sync_res.get('highestBlock', '0x1'), 16)
        pct = (curr / highest * 100.0) if highest > 0 else 0.0
        remaining_blocks = highest - curr
        # Estimate based on avg ~50 blocks/sec during snap sync
        est_seconds = remaining_blocks / 50.0
        est_hours = est_seconds / 3600.0

        print(f"  Status:           SNAP SYNCING IN PROGRESS")
        print(f"  Current Block:    #{curr:,}")
        print(f"  Target Block:     #{highest:,}")
        print(f"  Blocks Remaining: {remaining_blocks:,}")
        print(f"  Sync Progress:    {pct:.2f}%")
        print(f"  Estimated Time:   ~{est_hours:.1f} hours remaining (@ ~50 blocks/sec)")
    else:
        print("  Status:           OFFLINE / WAITING FOR START")
        print("  Sync Progress:    N/A")
        print("  Estimated Time:   N/A")
    print("-----------------------------------------------------------------")

    # 3. Lighthouse Consensus Client Status
    lh_data = http_get_json(f"{LIGHTHOUSE_REST_DEFAULT}/eth/v1/node/syncing")
    print("CONSENSUS CLIENT (LIGHTHOUSE):")
    if lh_data and 'data' in lh_data:
        info = lh_data['data']
        head_slot = int(info.get('head_slot', 0))
        sync_distance = int(info.get('sync_distance', 0))
        is_syncing = info.get('is_syncing', False)
        print(f"  Status:           {'SYNCING' if is_syncing else 'FULLY SYNCED'}")
        print(f"  Head Slot:        #{head_slot:,}")
        print(f"  Slots Behind:     {sync_distance:,}")
    else:
        print("  Status:           OFFLINE / WAITING FOR START")
    print("-----------------------------------------------------------------")

    # 4. Blockscout Indexer Status
    bs_blocks = http_get_json(f"{BLOCKSCOUT_API_DEFAULT}/blocks")
    print("TRANSACTION INDEXER (BLOCKSCOUT):")
    if bs_blocks and 'items' in bs_blocks and len(bs_blocks['items']) > 0:
        bs_head = int(bs_blocks['items'][0].get('height', 0))
        print(f"  Status:           ACTIVE")
        print(f"  Indexed Head:     #{bs_head:,}")
        print(f"  Mode:             Live-Only (Forward Indexing)")
    else:
        print("  Status:           CONTAINERS RUNNING / WAITING FOR DB MIGRATION")
    print("=================================================================")

if __name__ == "__main__":
    generate_report()

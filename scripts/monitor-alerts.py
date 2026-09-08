#!/usr/bin/env python3
"""
Ethereum Node & Indexer Monitoring & Alerting Daemon
---------------------------------------------------
Monitors:
  1. Disk Usage threshold (>85%)
  2. Geth node sync status & peer count
  3. Blockscout indexer block height lag vs Geth head
Sends Webhook alerts (Slack / Discord / Webhook) when limits are breached.
"""

import os
import sys
import time
import json
import shutil
import logging
import argparse
import urllib.request
import urllib.error

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

GETH_RPC_DEFAULT = "http://127.0.0.1:8545"
BLOCKSCOUT_API_DEFAULT = "http://127.0.0.1:4000/api/v2"
DISK_ALERT_THRESHOLD_PCT = 85.0
MAX_ALLOWED_INDEXER_LAG_BLOCKS = 20

def json_rpc_call(url, method, params=[]):
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('result')
    except Exception as e:
        return None

def http_get_json(url):
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        return None

def send_alert(webhook_url, title, message, severity="WARNING"):
    logging.warning(f"ALERT [{severity}]: {title} - {message}")
    if not webhook_url:
        return

    payload = json.dumps({
        "username": "Eth-Node-Monitor",
        "content": f"🚨 **[{severity}] {title}**\n{message}"
    }).encode('utf-8')
    req = urllib.request.Request(webhook_url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception as e:
        logging.error(f"Failed to deliver webhook alert: {e}")

def check_system_metrics(mount_point="/"):
    total, used, free = shutil.disk_usage(mount_point)
    pct_used = (used / total) * 100.0
    return pct_used, free / (1024**3), total / (1024**3)

def run_monitoring_cycle(geth_url, blockscout_api, webhook_url, disk_threshold):
    # 1. Disk Space Monitoring
    pct_used, free_gb, total_gb = check_system_metrics("/")
    logging.info(f"Disk Usage: {pct_used:.1f}% ({free_gb:.1f} GB free of {total_gb:.1f} GB)")
    if pct_used > disk_threshold:
        send_alert(
            webhook_url,
            "Disk Usage Threshold Exceeded",
            f"Disk usage is at {pct_used:.2f}% (Threshold: {disk_threshold}%). Free space left: {free_gb:.1f} GB.",
            severity="CRITICAL"
        )

    # 2. Geth Node Health & Sync Check
    geth_block_hex = json_rpc_call(geth_url, "eth_blockNumber")
    sync_status = json_rpc_call(geth_url, "eth_syncing")

    if geth_block_hex is None:
        send_alert(
            webhook_url,
            "Geth Execution Node Unreachable",
            f"Unable to query Geth RPC endpoint at {geth_url}. Check if geth service is active.",
            severity="CRITICAL"
        )
        return

    geth_head = int(geth_block_hex, 16)
    if sync_status and isinstance(sync_status, dict):
        curr = int(sync_status.get('currentBlock', '0x0'), 16)
        highest = int(sync_status.get('highestBlock', '0x1'), 16)
        logging.info(f"Geth Syncing: {curr:,} / {highest:,} ({curr/highest*100:.1f}%)")
        if highest - curr > 100:
            send_alert(
                webhook_url,
                "Geth Syncing Lag",
                f"Geth node is currently syncing. Current block: {curr:,}, Target: {highest:,} ({highest - curr:,} behind).",
                severity="WARNING"
            )
    else:
        logging.info(f"Geth State: SYNCED at Head Block #{geth_head:,}")

    # 3. Blockscout Indexer Lag Check
    bs_blocks = http_get_json(f"{blockscout_api}/blocks")
    if bs_blocks and 'items' in bs_blocks and len(bs_blocks['items']) > 0:
        bs_head = int(bs_blocks['items'][0].get('height', 0))
        lag = geth_head - bs_head
        logging.info(f"Blockscout Indexer Head: #{bs_head:,} (Lag: {lag} blocks)")
        if lag > MAX_ALLOWED_INDEXER_LAG_BLOCKS:
            send_alert(
                webhook_url,
                "Blockscout Indexer Falling Behind",
                f"Blockscout indexer head (#{bs_head:,}) is lagging {lag} blocks behind Geth head (#{geth_head:,}).",
                severity="WARNING"
            )
    else:
        logging.info("Blockscout Indexer block endpoint not reachable or empty.")

def main():
    parser = argparse.ArgumentParser(description="Ethereum Node Alerting Daemon")
    parser.add_argument("--geth", default=GETH_RPC_DEFAULT, help="Geth RPC URL")
    parser.add_argument("--blockscout", default=BLOCKSCOUT_API_DEFAULT, help="Blockscout API URL")
    parser.add_argument("--webhook", default=os.getenv("ALERT_WEBHOOK_URL", ""), help="Webhook notification URL")
    parser.add_argument("--disk-threshold", type=float, default=DISK_ALERT_THRESHOLD_PCT, help="Disk usage alert threshold percentage")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring polling interval in seconds")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in background daemon mode")
    args = parser.parse_args()

    logging.info("Starting Ethereum Node Monitoring Service...")
    while True:
        try:
            run_monitoring_cycle(args.geth, args.blockscout, args.webhook, args.disk_threshold)
        except Exception as e:
            logging.error(f"Error during monitoring loop: {e}")

        if not args.daemon:
            break
        time.sleep(args.interval)

if __name__ == "__main__":
    main()

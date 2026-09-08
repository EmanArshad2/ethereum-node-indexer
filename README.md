# Ethereum Mainnet / Sepolia Full Node & Transaction Indexer ("Mini-Etherscan")

An end-to-end, production-grade deployment suite for running an Ethereum Full Node (**Execution: Geth**, **Consensus: Lighthouse**) paired with **Blockscout** (PostgreSQL + Elixir Backend + Next.js Explorer UI) to track and search network-wide transactions.

> [!NOTE]
> **100% Free & Open-Source (FOSS)**: This entire stack uses completely free, open-source software (Geth, Lighthouse, Blockscout, PostgreSQL, Docker). There are **zero software subscription fees**, **zero paid API keys** (no reliance on paid Infura/Alchemy services), and **zero licensing costs**. Running this on your own PC / local hardware is completely **$0**.

---

## 📋 System Requirements & Self-Hosting Guide

### Hardware Minimums (For running on your own PC / Hardware)
- **CPU**: 8+ Physical Cores (AMD EPYC, Ryzen 7/9, or Intel Core i7/i9/Xeon)
- **RAM**: 32GB+ RAM (64GB recommended)
- **Storage**: 4TB - 8TB NVMe SSD (PCIe 4.0 recommended; regular SATA SSDs bottleneck on state healing IOPS)
- **Bandwidth**: 300 - 500 Mbps stable, unmetered internet connection (>10TB/month data transfer)

### Free Self-Hosting vs. Optional Cloud VPS
- **Self-Hosted (Local PC / Server)**: **$0 / month** (Runs entirely locally on your machine with 100% free software).
- **Cloud VPS (Optional)**: If you choose to rent a remote server instead of using your own PC, providers like Hetzner Dedicated (AX102) cost ~$160/mo, but this is entirely optional.

---

## 📁 Repository Structure

```
.
├── README.md                          # Complete operational guide
├── hardware-check.sh                  # Pre-flight environment & hardware validator
├── setup-jwt.sh                       # Secret key generator for Engine API
├── config/
│   ├── geth/
│   │   ├── flags.env                  # Shared Geth CLI flags
│   │   ├── geth-sepolia.service       # Sepolia execution service
│   │   └── geth-mainnet.service       # Mainnet execution service
│   └── lighthouse/
│       ├── flags.env                  # Shared Lighthouse CLI flags
│       ├── lighthouse-sepolia.service # Sepolia consensus service
│       └── lighthouse-mainnet.service # Mainnet consensus service
├── blockscout/
│   ├── docker-compose.yml             # Postgres, Backend, Frontend, Stats
│   ├── .env.sepolia                   # Sepolia indexing configuration
│   └── .env.mainnet                   # Mainnet indexing configuration
├── scripts/
│   ├── sync-status.py                 # Realtime node sync tracker CLI
│   ├── validate-pipeline.py           # Pipeline end-to-end validator
│   ├── monitor-alerts.py              # Automated daemon for disk & sync alerts
│   ├── status-report.py               # Dynamic status report generator
│   └── toggle-backfill.sh             # Live-Only <-> Full Historical switcher
└── systemd/
    └── eth-monitor.service            # Systemd unit for alerting daemon
```

---

## 🚀 Quick Start Guide

### Step 1: Pre-Flight Hardware Check
Run the pre-flight check script on your Linux machine (Ubuntu 22.04 / 24.04 LTS recommended):

```bash
chmod +x hardware-check.sh setup-jwt.sh scripts/*.sh
./hardware-check.sh
```

### Step 2: Install Geth & Lighthouse
Install the official Ethereum Execution (Geth) and Consensus (Lighthouse) binaries:

```bash
# Install Geth
sudo add-apt-repository -y ppa:ethereum/ethereum
sudo apt-get update
sudo apt-get install -y ethereum

# Install Lighthouse
curl -L https://github.com/sigp/lighthouse/releases/latest/download/lighthouse-v5.0.0-x86_64-unknown-linux-gnu.tar.gz | tar -xz
sudo mv lighthouse /usr/local/bin/
```

### Step 3: Generate Engine API Shared JWT Secret
Geth and Lighthouse authenticate communication via a shared JWT token:

```bash
./setup-jwt.sh /var/lib/ethereum/jwt.hex
```

---

## 🧪 Phase A: Sepolia Testnet Trial Setup

Before committing to Mainnet, verify the end-to-end stack on Sepolia:

1. **Install systemd service files**:
   ```bash
   sudo cp config/geth/geth-sepolia.service /etc/systemd/system/
   sudo cp config/lighthouse/lighthouse-sepolia.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

2. **Start Execution & Consensus clients**:
   ```bash
   sudo systemctl start geth-sepolia
   sudo systemctl start lighthouse-sepolia
   ```

3. **Check sync progress**:
   ```bash
   python3 scripts/sync-status.py --watch
   ```

4. **Launch Blockscout Indexer (Sepolia)**:
   ```bash
   cd blockscout
   cp .env.sepolia .env
   docker compose up -d
   ```

5. **Validate Pipeline**:
   ```bash
   python3 scripts/validate-pipeline.py --address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
   ```

---

## 🌐 Phase B: Mainnet Production Deployment

Once Sepolia trial validation succeeds, launch the Mainnet pipeline:

1. **Install Mainnet systemd unit files**:
   ```bash
   sudo cp config/geth/geth-mainnet.service /etc/systemd/system/
   sudo cp config/lighthouse/lighthouse-mainnet.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

2. **Start Mainnet clients**:
   ```bash
   sudo systemctl enable --now geth-mainnet
   sudo systemctl enable --now lighthouse-mainnet
   ```

3. **Monitor Mainnet Sync Progress**:
   ```bash
   python3 scripts/sync-status.py --watch
   ```
   *Note: Geth snap sync takes ~8-16 hours on NVMe SSD with 32GB+ RAM.*

4. **Deploy Blockscout Indexer for Mainnet**:
   ```bash
   cd blockscout
   cp .env.mainnet .env
   docker compose up -d
   ```

---

## ⚙️ Operational Management Commands

### Start / Stop Node Services
```bash
# Mainnet Execution
sudo systemctl start geth-mainnet
sudo systemctl stop geth-mainnet

# Mainnet Consensus
sudo systemctl start lighthouse-mainnet
sudo systemctl stop lighthouse-mainnet

# Blockscout Indexer
cd blockscout
docker compose down   # Stop indexer
docker compose up -d  # Start indexer
```

### Inspect Logs
```bash
# Geth Logs
journalctl -u geth-mainnet -f -n 100

# Lighthouse Logs
journalctl -u lighthouse-mainnet -f -n 100

# Blockscout Logs
cd blockscout && docker compose logs -f backend
```

---

## 🔄 Switching Between Live-Only Mode & Full Historical Backfill

By default, Blockscout starts in **Live-Only Mode** (`FIRST_BLOCK=latest`), indexing incoming new blocks immediately so you get search capabilities right away.

To switch to **Full Historical Backfill** (indexing all blocks back to Genesis 0):

```bash
# Switch to Full Backfill
./scripts/toggle-backfill.sh full-backfill

# Switch back to Live-Only
./scripts/toggle-backfill.sh live-only
```

---

## 🔔 Monitoring & Automated Alerting Daemon

The monitoring daemon tracks disk space (>85% alert), Geth peer counts, and indexer lag:

1. **Run single health check**:
   ```bash
   python3 scripts/monitor-alerts.py
   ```

2. **Generate system status report**:
   ```bash
   python3 scripts/status-report.py
   ```

3. **Enable webhook notifications (Discord / Slack / Telegram)**:
   ```bash
   export ALERT_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"
   python3 scripts/monitor-alerts.py --daemon --interval 60
   ```

4. **Install Alerting Daemon as a Systemd Service**:
   ```bash
   sudo cp systemd/eth-monitor.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now eth-monitor
   ```

---

## 📡 API Querying Examples

- **Geth JSON-RPC API**: `http://localhost:8545`
  ```bash
  curl -X POST -H "Content-Type: application/json" \
    --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
    http://localhost:8545
  ```

- **Blockscout Indexer API**: `http://localhost:4000/api/v2`
  ```bash
  # Query Address Transactions
  curl -s http://localhost:4000/api/v2/addresses/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045/transactions
  ```

- **Blockscout Explorer Web UI**: `http://localhost:3000`

#!/usr/bin/env bash
# ==============================================================================
# Ethereum Mainnet / Sepolia Node Pre-Flight Hardware & Environment Checker
# ==============================================================================
# This script evaluates whether the host machine meets the minimum hardware 
# requirements to comfortably sync and run an Ethereum Execution (Geth) + 
# Consensus (Lighthouse) client alongside Blockscout indexer.
# ==============================================================================

set -euo pipefail

BOLD="\031[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}================================================================${RESET}"
echo -e "${BOLD}${BLUE}  Ethereum Mainnet & Sepolia Node Setup - Hardware & OS Check  ${RESET}"
echo -e "${BOLD}${BLUE}================================================================${RESET}"
echo

ERRORS=0
WARNINGS=0

# 1. OS Verification
echo -e "${BOLD}[1/6] Operating System Verification${RESET}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "  OS Name:     ${GREEN}$NAME ($VERSION)${RESET}"
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        echo -e "  ${YELLOW}[WARNING] Recommended OS is Ubuntu 22.04 LTS or 24.04 LTS.${RESET}"
        ((WARNINGS++))
    fi
else
    echo -e "  ${RED}[FAIL] Unable to determine OS release details.${RESET}"
    ((ERRORS++))
fi
echo

# 2. CPU Cores Check
echo -e "${BOLD}[2/6] CPU Core Count Check${RESET}"
CPU_CORES=$(nproc 2>/dev/null || grep -c ^processor /proc/cpuinfo)
echo -e "  Detected Cores: ${BOLD}${CPU_CORES}${RESET} logical processors"

if [ "$CPU_CORES" -ge 8 ]; then
    echo -e "  Status:         ${GREEN}[PASS] Meets or exceeds minimum of 8 CPU cores.${RESET}"
elif [ "$CPU_CORES" -ge 4 ]; then
    echo -e "  Status:         ${YELLOW}[WARNING] 4 cores detected. Minimum for Mainnet is 8 cores (Sepolia ok).${RESET}"
    ((WARNINGS++))
else
    echo -e "  Status:         ${RED}[FAIL] Less than 4 cores detected. Mainnet node will fail state healing.${RESET}"
    ((ERRORS++))
fi
echo

# 3. Memory (RAM) Check
echo -e "${BOLD}[3/6] System Memory (RAM) Check${RESET}"
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$(echo "scale=1; $TOTAL_RAM_KB / 1024 / 1024" | bc 2>/dev/null || awk "BEGIN {print $TOTAL_RAM_KB / 1048576}")
echo -e "  Total RAM:      ${BOLD}${TOTAL_RAM_GB} GB${RESET}"

if (( $(echo "$TOTAL_RAM_GB >= 31.0" | bc -l 2>/dev/null || echo 0) )); then
    echo -e "  Status:         ${GREEN}[PASS] Meets 32GB+ RAM requirement.${RESET}"
elif (( $(echo "$TOTAL_RAM_GB >= 15.0" | bc -l 2>/dev/null || echo 0) )); then
    echo -e "  Status:         ${YELLOW}[WARNING] 16GB RAM detected. Recommended minimum for Geth+Lighthouse is 32GB.${RESET}"
    ((WARNINGS++))
else
    echo -e "  Status:         ${RED}[FAIL] Insufficient RAM (${TOTAL_RAM_GB} GB). Geth OOM crashes likely.${RESET}"
    ((ERRORS++))
fi
echo

# 4. Storage & NVMe Check
echo -e "${BOLD}[4/6] Storage Capacity & Disk Type Check${RESET}"
ROOT_DISK=$(df -k / | awk 'NR==2 {print $1}')
AVAILABLE_STORAGE_KB=$(df -k / | awk 'NR==2 {print $4}')
AVAILABLE_STORAGE_GB=$(echo "scale=1; $AVAILABLE_STORAGE_KB / 1024 / 1024" | bc 2>/dev/null || awk "BEGIN {print $AVAILABLE_STORAGE_KB / 1048576}")

echo -e "  Root Partition: ${ROOT_DISK}"
echo -e "  Available Space: ${BOLD}${AVAILABLE_STORAGE_GB} GB${RESET}"

# Check NVMe
IS_NVME=$(lsblk -d -o NAME,ROTA 2>/dev/null | grep -E "nvme" || echo "")
if [ -n "$IS_NVME" ]; then
    echo -e "  Drive Type:     ${GREEN}[PASS] NVMe SSD detected.${RESET}"
else
    echo -e "  Drive Type:     ${YELLOW}[WARNING] NVMe drive not explicitly detected. Ensure SSD (not HDD or slow SATA).${RESET}"
    ((WARNINGS++))
fi

if (( $(echo "$AVAILABLE_STORAGE_GB >= 2000.0" | bc -l 2>/dev/null || echo 0) )); then
    echo -e "  Capacity:       ${GREEN}[PASS] Storage meets Geth Mainnet snap sync requirements (>2TB).${RESET}"
elif (( $(echo "$AVAILABLE_STORAGE_GB >= 350.0" | bc -l 2>/dev/null || echo 0) )); then
    echo -e "  Capacity:       ${YELLOW}[WARNING] Space is sufficient for Sepolia testnet (~350GB), but Mainnet requires 2-4TB.${RESET}"
    ((WARNINGS++))
else
    echo -e "  Capacity:       ${RED}[FAIL] Disk space dangerously low (<350 GB free).${RESET}"
    ((ERRORS++))
fi
echo

# 5. Required Ports Check
echo -e "${BOLD}[5/6] Port Availability Check${RESET}"
PORTS=(30303 9000 8545 8546 8551 5052 80 443 5432)
PORT_ERRORS=0

for PORT in "${PORTS[@]}"; do
    if ss -tuln 2>/dev/null | grep -q ":${PORT} "; then
        echo -e "  Port ${PORT}: ${YELLOW}IN USE (Check if Ethereum process or docker already running)${RESET}"
        ((PORT_ERRORS++))
    else
        echo -e "  Port ${PORT}: ${GREEN}AVAILABLE${RESET}"
    fi
done
echo

# 6. Recommendation & Free Software Summary
echo -e "${BOLD}[6/6] 100% Free & Open-Source (FOSS) Software Stack${RESET}"
echo -e "  - ${GREEN}Software Cost: \$0.00${RESET} (Geth, Lighthouse, Blockscout, Postgres are all 100% free open-source)"
echo -e "  - ${GREEN}API / Service Fees: \$0.00${RESET} (Zero third-party RPC subscriptions required)"
echo -e "  - ${BOLD}Running on local PC / dedicated server:${RESET} Total software & hosting cost is ${GREEN}\$0.00 / month${RESET}."
echo -e "  - ${BOLD}(Optional Cloud VPS rentals for remote hosting only):${RESET} Hetzner Dedicated / OVH, but optional."
echo

echo -e "${BOLD}${BLUE}================================================================${RESET}"
if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}  Pre-flight check passed with ${WARNINGS} warning(s) and 0 critical errors.${RESET}"
    echo -e "${GREEN}  You are ready to proceed with JWT setup and client initialization!${RESET}"
else
    echo -e "${RED}${BOLD}  Pre-flight check failed with ${ERRORS} critical error(s) and ${WARNINGS} warning(s).${RESET}"
    echo -e "${RED}  Please resolve the hardware/disk bottlenecks before running Mainnet sync.${RESET}"
fi
echo -e "${BOLD}${BLUE}================================================================${RESET}"

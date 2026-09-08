#!/usr/bin/env bash
# ==============================================================================
# Blockscout Indexing Mode Switcher (Live-Only vs Full Historical Backfill)
# ==============================================================================
# Usage:
#   ./scripts/toggle-backfill.sh live-only
#   ./scripts/toggle-backfill.sh full-backfill
# ==============================================================================

set -euo pipefail

MODE="${1:-}"
BLOCKSCOUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../blockscout" && pwd)"
ENV_FILE="${BLOCKSCOUT_DIR}/.env"

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}================================================================${RESET}"
echo -e "${BOLD}${BLUE}          Blockscout Indexing Mode Configuration Switcher        ${RESET}"
echo -e "${BOLD}${BLUE}================================================================${RESET}"
echo

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}[ERROR] Target .env file not found at ${ENV_FILE}.${RESET}"
    echo -e "Please copy .env.sepolia or .env.mainnet to .env in the blockscout directory first."
    exit 1
fi

if [ "$MODE" == "live-only" ]; then
    echo -e "${YELLOW}Configuring Blockscout for LIVE-ONLY Indexing Mode...${RESET}"
    sed -i 's/^INDEXER_DISABLE_HISTORICAL_INDEXING=.*/INDEXER_DISABLE_HISTORICAL_INDEXING=true/' "$ENV_FILE" || true
    if grep -q "^FIRST_BLOCK=" "$ENV_FILE"; then
        sed -i 's/^FIRST_BLOCK=.*/FIRST_BLOCK=latest/' "$ENV_FILE"
    else
        echo "FIRST_BLOCK=latest" >> "$ENV_FILE"
    fi
    echo -e "${GREEN}[SUCCESS] Updated .env to Live-Only mode (indexing new blocks from current head).${RESET}"

elif [ "$MODE" == "full-backfill" ]; then
    echo -e "${YELLOW}Configuring Blockscout for FULL HISTORICAL BACKFILL Mode...${RESET}"
    sed -i 's/^INDEXER_DISABLE_HISTORICAL_INDEXING=.*/INDEXER_DISABLE_HISTORICAL_INDEXING=false/' "$ENV_FILE" || true
    if grep -q "^FIRST_BLOCK=" "$ENV_FILE"; then
        sed -i 's/^FIRST_BLOCK=.*/FIRST_BLOCK=0/' "$ENV_FILE"
    else
        echo "FIRST_BLOCK=0" >> "$ENV_FILE"
    fi
    echo -e "${GREEN}[SUCCESS] Updated .env to Full Backfill mode (indexing all blocks back to Genesis 0).${RESET}"

else
    echo -e "${RED}Invalid mode specified.${RESET}"
    echo -e "Usage:"
    echo -e "  $0 live-only       (Index only new forward-going blocks)"
    echo -e "  $0 full-backfill   (Backfill all historical blocks starting from genesis)"
    exit 1
fi

echo
echo -e "Restarting Blockscout backend container to apply changes..."
cd "$BLOCKSCOUT_DIR"
docker compose restart backend || echo -e "${YELLOW}[NOTE] Ensure Docker Compose is active to restart container.${RESET}"

echo
echo -e "${BOLD}${GREEN}Mode switch applied successfully!${RESET}"
echo -e "${BOLD}${BLUE}================================================================${RESET}"

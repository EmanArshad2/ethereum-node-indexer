#!/usr/bin/env bash
# ==============================================================================
# Ethereum Node JWT Secret Setup Utility
# ==============================================================================
# Execution (Geth) and Consensus (Lighthouse) clients authenticate Engine API 
# calls via a shared 256-bit (32-byte) hex JWT secret key.
# ==============================================================================

set -euo pipefail

JWT_PATH="${1:-/var/lib/ethereum/jwt.hex}"
JWT_DIR=$(dirname "$JWT_PATH")

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}================================================================${RESET}"
echo -e "${BOLD}${BLUE}          Ethereum Node JWT Authentication Generator           ${RESET}"
echo -e "${BOLD}${BLUE}================================================================${RESET}"
echo

# 1. Target Directory Setup
echo -e "Target JWT File Path: ${BOLD}${JWT_PATH}${RESET}"
if [ ! -d "$JWT_DIR" ]; then
    echo -e "Creating directory structure: ${JWT_DIR}"
    mkdir -p "$JWT_DIR" || sudo mkdir -p "$JWT_DIR"
fi

# 2. Key Generation
if [ -f "$JWT_PATH" ]; then
    echo -e "${GREEN}[INFO] JWT secret already exists at ${JWT_PATH}.${RESET}"
else
    echo -e "Generating cryptographically secure 32-byte hex secret..."
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex 32 | tr -d '\n' | sudo tee "$JWT_PATH" > /dev/null
    else
        xxd -l 32 -c 32 -p /dev/urandom | tr -d '\n' | sudo tee "$JWT_PATH" > /dev/null
    fi
    echo -e "${GREEN}[SUCCESS] Generated new JWT secret.${RESET}"
fi

# 3. Permissions Security Hardening
echo -e "Applying strict read-only permissions (chmod 600)..."
sudo chmod 600 "$JWT_PATH" 2>/dev/null || chmod 600 "$JWT_PATH" 2>/dev/null || true

# 4. Key Verification Output
JWT_CONTENT=$(sudo cat "$JWT_PATH" 2>/dev/null || cat "$JWT_PATH")
JWT_LEN=${#JWT_CONTENT}

echo
echo -e "${GREEN}JWT Verification Summary:${RESET}"
echo -e "  Secret Length: ${BOLD}${JWT_LEN} characters${RESET} (Expected: 64 hex characters)"
echo -e "  Secret SHA256: ${BOLD}$(echo -n "$JWT_CONTENT" | sha256sum | awk '{print $1}')${RESET}"
echo
echo -e "${BOLD}${GREEN}JWT Setup Complete. Geth and Lighthouse can now authenticate via Engine API.${RESET}"
echo -e "${BOLD}${BLUE}================================================================${RESET}"

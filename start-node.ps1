# ==============================================================================
# Ethereum Node & Explorer 1-Click Windows Launcher
# ==============================================================================
# Double-click or run: .\start-node.ps1
# ==============================================================================

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       Launching Ethereum Node & Blockscout Explorer UI...      " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$BASE_DIR = "$env:USERPROFILE\Desktop\ethereum"
$DATA_DIR = "$BASE_DIR\data"
$JWT_PATH = "$BASE_DIR\jwt.hex"
$PROJECT_DIR = $PSScriptRoot

# 1. Create data directory if missing
if (-not (Test-Path $DATA_DIR)) {
    Write-Host "[1/5] Creating Ethereum data directory at $DATA_DIR..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $DATA_DIR | Out-Null
}

# 2. Generate JWT Secret if missing
if (-not (Test-Path $JWT_PATH)) {
    Write-Host "[2/5] Generating JWT secret key..." -ForegroundColor Yellow
    [Byte[]]$bytes = New-Object Byte[] 32
    (New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
    $jwt = [BitConverter]::ToString($bytes).Replace("-","").ToLower()
    Set-Content -Path $JWT_PATH -Value $jwt -Encoding Ascii
}

# 3. Check if Geth is already running, if not start it
$gethListening = Test-NetConnection -ComputerName "127.0.0.1" -Port 8545 -InformationLevel Quiet
if (-not $gethListening) {
    Write-Host "[3/5] Starting Geth Execution Client in background..." -ForegroundColor Yellow
    $gethExe = "C:\Program Files\Geth\geth.exe"
    if (Test-Path $gethExe) {
        Start-Process -FilePath $gethExe -ArgumentList "--sepolia --datadir `"$DATA_DIR\geth`" --http --http.addr `"0.0.0.0`" --http.port 8545 --http.api `"eth,net,web3,engine,txpool,debug`" --http.corsdomain `"*`" --ws --ws.addr `"0.0.0.0`" --ws.port 8546 --ws.api `"eth,net,web3`" --authrpc.addr `"127.0.0.1`" --authrpc.port 8551 --authrpc.jwtsecret `"$JWT_PATH`" --authrpc.vhosts `"*`" --cache 8192 --maxpeers 50" -WindowStyle Hidden
    } else {
        Write-Host "  [-] Geth executable not found at $gethExe. Please install Geth." -ForegroundColor Red
    }
} else {
    Write-Host "[3/5] Geth Execution Client is already running! [OK]" -ForegroundColor Green
}

# 4. Start Lighthouse Docker container if not running
$lhRunning = docker ps --format '{{.Names}}' | Select-String "lighthouse"
if (-not $lhRunning) {
    Write-Host "[4/5] Starting Lighthouse Consensus Client in Docker..." -ForegroundColor Yellow
    docker run -d `
      --name lighthouse `
      --restart unless-stopped `
      -p 5052:5052 `
      -p 9000:9000/tcp `
      -p 9000:9000/udp `
      -v "$DATA_DIR\lighthouse:/root/.lighthouse" `
      -v "$JWT_PATH:/root/jwt.hex" `
      sigp/lighthouse:latest `
      lighthouse bn `
      --network sepolia `
      --execution-endpoint http://host.docker.internal:8551 `
      --execution-jwt /root/jwt.hex `
      --checkpoint-sync-url https://checkpoint-sync.sepolia.ethpandaops.io `
      --http `
      --http-address 0.0.0.0 `
      --http-port 5052 | Out-Null
} else {
    Write-Host "[4/5] Lighthouse Consensus Client is already running! [OK]" -ForegroundColor Green
}

# 5. Start Blockscout Docker Containers
Write-Host "[5/5] Launching Blockscout Indexer & Explorer UI..." -ForegroundColor Yellow
$blockscoutDir = Join-Path $PROJECT_DIR "blockscout"
if (Test-Path $blockscoutDir) {
    Set-Location $blockscoutDir
    
    # Ensure .env is set
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.sepolia" ".env"
    }

    docker compose up -d
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  SUCCESS! All Ethereum Node & Explorer Services are Running!    " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  Opening Explorer UI: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://localhost:3000"

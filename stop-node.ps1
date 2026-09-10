# ==============================================================================
# Ethereum Node & Explorer 1-Click Windows Stop Script
# ==============================================================================
# Double-click or run: .\stop-node.ps1
# ==============================================================================

Write-Host "Stopping Blockscout Explorer..." -ForegroundColor Yellow
$PROJECT_DIR = $PSScriptRoot
$blockscoutDir = Join-Path $PROJECT_DIR "blockscout"
if (Test-Path $blockscoutDir) {
    Set-Location $blockscoutDir
    docker compose down
}

Write-Host "Stopping Lighthouse Container..." -ForegroundColor Yellow
docker stop lighthouse 2>$null
docker rm lighthouse 2>$null

Write-Host "Stopping Geth Execution Client..." -ForegroundColor Yellow
Stop-Process -Name "geth" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "All Ethereum services stopped successfully!" -ForegroundColor Green

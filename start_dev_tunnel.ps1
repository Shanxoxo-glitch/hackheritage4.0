# Start Development Tunnel & Stack Bridge Script for Shaan
# Connects Frontend PWA (5173) -> Backend (8400) -> Azure VM Orchestrator (8500 over SSH Tunnel)

$VM_IP = "20.198.64.9"
$SSH_KEY = "$env:USERPROFILE\.ssh\id_ed25519"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  PS26094 UNIFIED DEV STACK & AZURE VM TUNNEL LAUNCHER   " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Start SSH Tunnel to Azure VM in Background
Write-Host "`n[1/3] Starting SSH Tunnel to Azure VM ($VM_IP)..." -ForegroundColor Yellow
if (Test-Path $SSH_KEY) {
    Start-Process -FilePath "ssh" -ArgumentList "-N", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "-L", "8500:localhost:8500", "-L", "11434:localhost:11434", "azureuser@$VM_IP" -WindowStyle Hidden
    Write-Host "  -> SSH Tunnel active: localhost:8500 (Orchestrator) & localhost:11434 (Avik's Ollama Models)" -ForegroundColor Green
} else {
    Write-Host "  -> Warning: SSH Key $SSH_KEY not found. Please ensure SSH key is generated." -ForegroundColor Red
}

# 2. Check Backend & Services
Write-Host "`n[2/3] Backend API Engine configured on http://localhost:8400" -ForegroundColor Yellow
Write-Host "  -> Stream Proxy path: POST /v1/interactions/stream forwards to localhost:8500 (VM Orchestrator)" -ForegroundColor Green

# 3. Instructions for running full local stack
Write-Host "`n[3/3] Launching Local Frontend PWA & Backend Stack..." -ForegroundColor Yellow
Write-Host "  To run Backend:  cd services/backend; uvicorn app.main:app --port 8400 --reload" -ForegroundColor Cyan
Write-Host "  To run Frontend: cd services/web; npm run dev" -ForegroundColor Cyan
Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "  Your PWA frontend will now send user chat queries" -ForegroundColor Green
Write-Host "  to Backend (8400), which proxies to VM Orchestrator (8500)" -ForegroundColor Green
Write-Host "  and streams the AI response back into your PWA interface!" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Cyan

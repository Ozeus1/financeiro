# 4_atualizar_remoto.ps1
# Atalho Windows: faz push local e aciona o deploy na VPS via SSH.
# Edite as variaveis VPS_USER e VPS_IP antes de usar.

param(
    [string]$Mensagem = "deploy: atualizacao"
)

# ── CONFIGURE AQUI ────────────────────────────────────────────────────────
$VPS_USER = "root"          # usuario SSH da VPS
$VPS_IP   = "SEU_IP_AQUI"  # IP ou hostname da VPS
# ─────────────────────────────────────────────────────────────────────────

if ($VPS_IP -eq "SEU_IP_AQUI") {
    Write-Host "ERRO: Edite o arquivo 4_atualizar_remoto.ps1 e defina VPS_IP." -ForegroundColor Red
    exit 1
}

Write-Host "=== ATUALIZACAO COMPLETA: Local → GitHub → VPS ===" -ForegroundColor Cyan

# Passo 1: push para o GitHub
Write-Host "`n[1/2] Enviando codigo para GitHub..." -ForegroundColor Yellow
& "$PSScriptRoot\1_push_github.ps1" -Mensagem $Mensagem
if ($LASTEXITCODE -ne 0) { exit 1 }

# Passo 2: acionar deploy na VPS
Write-Host "`n[2/2] Acionando deploy na VPS ($VPS_USER@$VPS_IP)..." -ForegroundColor Yellow
ssh "${VPS_USER}@${VPS_IP}" "bash /home/deploy/finan_pub/deploy/3_deploy.sh"
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDeploy concluido! Acesse: https://www.finan.automathos.cloud" -ForegroundColor Green
} else {
    Write-Host "`nErro no deploy remoto. Verifique os logs na VPS." -ForegroundColor Red
    exit 1
}

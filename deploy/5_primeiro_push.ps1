# 5_primeiro_push.ps1
# Execute APENAS na primeira vez para adicionar flask/ e deploy/ ao GitHub.
# Depois use 4_atualizar_remoto.ps1 para atualizações normais.

Set-Location "$PSScriptRoot\.."

Write-Host "=== PRIMEIRO PUSH: adicionando flask/ e deploy/ ao GitHub ===" -ForegroundColor Cyan

# Garante branch finan_pub
git checkout finan_pub

# Adiciona flask/ (excluindo .env.production que está no .gitignore)
git add flask/
git add deploy/
git add .gitignore

# Verifica o que será commitado
Write-Host "`nArquivos que serao commitados:" -ForegroundColor Yellow
git status --short

$confirm = Read-Host "`nConfirmar commit e push? (s/n)"
if ($confirm -ne "s") {
    Write-Host "Cancelado." -ForegroundColor Yellow
    exit 0
}

git commit -m "feat: adicionar aplicacao flask/ e scripts de deploy"
git push origin finan_pub

Write-Host "`nPronto! Agora execute o setup na VPS:" -ForegroundColor Green
Write-Host "  ssh usuario@IP_DA_VPS 'bash -s' < deploy/2_setup_vps.sh" -ForegroundColor Cyan

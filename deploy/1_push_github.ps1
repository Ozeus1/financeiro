# 1_push_github.ps1
# Executa no Windows: faz commit de tudo e envia para o branch finan_pub no GitHub

param(
    [string]$Mensagem = "deploy: atualizacao automatica"
)

Set-Location "$PSScriptRoot\.."

Write-Host "=== PUSH PARA GITHUB (branch: finan_pub) ===" -ForegroundColor Cyan

# Garante que está no branch correto
git checkout finan_pub
if ($LASTEXITCODE -ne 0) {
    git checkout -b finan_pub
}

# Adiciona tudo (exceto o que está no .gitignore)
git add -A

# Verifica se há algo para commitar
$status = git status --porcelain
if (-not $status) {
    Write-Host "Nada para commitar. Repositorio ja esta atualizado." -ForegroundColor Yellow
} else {
    git commit -m $Mensagem
    Write-Host "Commit criado: $Mensagem" -ForegroundColor Green
}

# Push para o GitHub
git push origin finan_pub
if ($LASTEXITCODE -eq 0) {
    Write-Host "Push concluido com sucesso!" -ForegroundColor Green
    Write-Host "Proximo passo: execute 4_atualizar_remoto.ps1 para acionar o deploy na VPS." -ForegroundColor Cyan
} else {
    Write-Host "Erro no push. Verifique suas credenciais do GitHub." -ForegroundColor Red
    exit 1
}

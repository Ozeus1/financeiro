#!/bin/bash

# Script para atualizar o servidor VPS com as novas funcionalidades
# Sincronização Bidirecional Desktop ↔ Servidor

echo "======================================"
echo "🚀 Atualizando Servidor VPS"
echo "======================================"
echo ""

# 1. Ir para o diretório do projeto
echo "📁 Acessando diretório do projeto..."
cd /var/www/financeiro || exit 1

# 2. Fazer backup do código atual
echo "💾 Fazendo backup do código atual..."
BACKUP_DIR="/var/www/financeiro_backup_$(date +%Y%m%d_%H%M%S)"
sudo cp -r /var/www/financeiro "$BACKUP_DIR"
echo "   Backup salvo em: $BACKUP_DIR"
echo ""

# 3. Parar o serviço
echo "⏸️  Parando serviço financeiro..."
sudo systemctl stop financeiro
echo ""

# 4. Baixar atualizações do GitHub
echo "📥 Baixando atualizações do GitHub..."
sudo -u www-data git fetch origin
sudo -u www-data git pull origin main
echo ""

# 5. Verificar se há novos pacotes Python
echo "📦 Verificando dependências Python..."
if [ -f requirements.txt ]; then
    echo "   Instalando/atualizando pacotes..."
    sudo -u www-data /var/www/financeiro/venv/bin/pip install -r requirements.txt --quiet
    echo "   ✓ Dependências atualizadas"
else
    echo "   ⚠️  Arquivo requirements.txt não encontrado"
fi
echo ""

# 6. Verificar permissões
echo "🔐 Ajustando permissões..."
sudo chown -R www-data:www-data /var/www/financeiro
sudo chmod 640 /var/www/financeiro/.env 2>/dev/null || echo "   (arquivo .env não encontrado, ok)"
echo ""

# 7. Reiniciar o serviço
echo "▶️  Reiniciando serviço financeiro..."
sudo systemctl start financeiro
sleep 3
echo ""

# 8. Verificar status
echo "✅ Verificando status do serviço..."
sudo systemctl status financeiro --no-pager -l | head -n 20
echo ""

# 9. Verificar logs recentes
echo "📋 Últimas linhas do log:"
sudo journalctl -u financeiro -n 10 --no-pager
echo ""

# 10. Resumo
echo "======================================"
echo "✨ Atualização Concluída!"
echo "======================================"
echo ""
echo "🌐 Acesse o sistema em:"
echo "   https://finan.receberbemevinhos.com.br"
echo ""
echo "📤 Teste a sincronização em:"
echo "   https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos"
echo ""
echo "📖 Documentação:"
echo "   - GUIA_SYNC_BIDIRECIONAL.md"
echo "   - QUICK_REFERENCE_SYNC.md"
echo ""
echo "💾 Backup anterior salvo em:"
echo "   $BACKUP_DIR"
echo ""
echo "======================================"

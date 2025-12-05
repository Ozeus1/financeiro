#!/bin/bash
# Script para configurar SSL/HTTPS com Let's Encrypt

set -e

echo "======================================================"
echo "  CONFIGURAÇÃO SSL - SISTEMA FINANCEIRO"
echo "======================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    print_error "Execute este script com sudo"
    echo "Uso: sudo bash setup_ssl.sh"
    exit 1
fi

# Domínio
DOMAIN="finan.receberbemevinhos.com.br"
WWW_DOMAIN="www.finan.receberbemevinhos.com.br"

echo "Configurando SSL para:"
echo "  - $DOMAIN"
echo "  - $WWW_DOMAIN"
echo ""

# 1. Instalar Certbot
echo "1️⃣  Instalando Certbot..."
if ! command -v certbot &> /dev/null; then
    apt update
    apt install certbot python3-certbot-nginx -y
    print_success "Certbot instalado"
else
    print_warning "Certbot já está instalado"
fi

# 2. Verificar se o Nginx está configurado
echo ""
echo "2️⃣  Verificando configuração do Nginx..."
if [ -f "/etc/nginx/sites-available/financeiro" ]; then
    print_success "Configuração do Nginx encontrada"
else
    print_error "Configuração do Nginx não encontrada"
    echo "Execute primeiro: sudo bash install_servidor.sh"
    exit 1
fi

# 3. Testar configuração do Nginx
echo ""
echo "3️⃣  Testando configuração do Nginx..."
nginx -t
if [ $? -eq 0 ]; then
    print_success "Configuração do Nginx válida"
    systemctl reload nginx
else
    print_error "Erro na configuração do Nginx"
    exit 1
fi

# 4. Obter certificado SSL
echo ""
echo "4️⃣  Obtendo certificado SSL..."
echo ""
print_warning "IMPORTANTE: Certifique-se que o DNS está apontando para este servidor!"
echo ""
read -p "Continuar? (s/n): " CONTINUE

if [ "$CONTINUE" != "s" ]; then
    echo "Cancelado pelo usuário"
    exit 0
fi

# Obter certificado
certbot --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN --redirect

if [ $? -eq 0 ]; then
    print_success "Certificado SSL obtido com sucesso!"
else
    print_error "Erro ao obter certificado SSL"
    echo ""
    print_warning "Possíveis causas:"
    echo "  1. DNS não está apontando para este servidor"
    echo "  2. Portas 80 e 443 não estão abertas no firewall"
    echo "  3. Domínio não está acessível pela internet"
    exit 1
fi

# 5. Configurar renovação automática
echo ""
echo "5️⃣  Configurando renovação automática..."
systemctl enable certbot.timer
systemctl start certbot.timer
print_success "Renovação automática configurada"

# 6. Testar renovação
echo ""
echo "6️⃣  Testando renovação..."
certbot renew --dry-run
if [ $? -eq 0 ]; then
    print_success "Teste de renovação bem-sucedido"
else
    print_warning "Teste de renovação falhou, mas o certificado está instalado"
fi

# Resultado final
echo ""
echo "======================================================"
print_success "SSL CONFIGURADO COM SUCESSO!"
echo "======================================================"
echo ""
echo "🌐 Seu site agora está acessível em:"
echo "   https://$DOMAIN"
echo "   https://$WWW_DOMAIN"
echo ""
echo "🔒 Certificado SSL:"
echo "   Emissor: Let's Encrypt"
echo "   Validade: 90 dias (renovação automática)"
echo ""
echo "📋 Próximos passos:"
echo "   1. Acesse: https://$DOMAIN"
echo "   2. Faça login com: admin / admin123"
echo "   3. Altere a senha do admin imediatamente!"
echo ""
echo "🔄 Renovação automática:"
echo "   O certificado será renovado automaticamente antes de expirar"
echo "   Verifique o status: sudo systemctl status certbot.timer"
echo ""
print_success "Deploy completo!"
echo "======================================================"

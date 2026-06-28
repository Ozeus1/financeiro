#!/bin/bash
# deploy_promo1.sh
# Publica a landing page promo em promo1.finanai.pro
# Execute na VPS como root: bash deploy_promo1.sh

set -e

REPO_URL="https://github.com/Ozeus1/financeiro.git"
REPO_DIR="/home/deploy/finan_pub"
BRANCH="finan_pub"
PROMO_SRC="$REPO_DIR/FinanIA_landing/FinanIA/promo"
WEB_DIR="/var/www/promo1"
NGINX_CONF="/etc/nginx/sites-available/promo1"
DOMAIN="promo1.finanai.pro"

echo "======================================"
echo " DEPLOY — $DOMAIN"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================"

# 1. Atualizar repositório
echo "[1/5] Atualizando repositorio..."
if [ -d "$REPO_DIR/.git" ]; then
    cd "$REPO_DIR"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi

# 2. Copiar arquivos da landing page
echo "[2/5] Copiando arquivos para $WEB_DIR..."
mkdir -p "$WEB_DIR"
rsync -av --delete "$PROMO_SRC/" "$WEB_DIR/"
chown -R www-data:www-data "$WEB_DIR"
chmod -R 755 "$WEB_DIR"

# 3. Configurar Nginx
echo "[3/5] Configurando Nginx..."
cp "$PROMO_SRC/nginx_promo1.conf" "$NGINX_CONF"
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/promo1
nginx -t
systemctl reload nginx

# 4. SSL com certbot
echo "[4/5] Emitindo certificado SSL..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
    -m orlei.barbosa1@gmail.com --redirect || \
    echo "AVISO: certbot falhou — verifique se o DNS ja propagou e tente manualmente:"
    echo "  sudo certbot --nginx -d $DOMAIN"

# 5. Verificar
echo "[5/5] Verificando..."
nginx -t && systemctl reload nginx

echo ""
echo "======================================"
echo " DEPLOY CONCLUIDO!"
echo " Acesse: https://$DOMAIN"
echo "======================================"

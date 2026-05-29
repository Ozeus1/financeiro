#!/bin/bash
# 2_setup_vps.sh
# Execute UMA VEZ na VPS para preparar o ambiente completo.
# Uso: ssh usuario@IP_DA_VPS "bash -s" < deploy/2_setup_vps.sh

set -e

REPO_URL="https://github.com/Ozeus1/financeiro.git"
APP_DIR="/home/deploy/finan_pub"
APP_BRANCH="finan_pub"
APP_USER="deploy"

echo "======================================"
echo " SETUP INICIAL DA VPS - finan_pub"
echo " Dominio: www.finan.automathos.cloud"
echo "======================================"

# ── 1. Dependências do sistema ─────────────────────────────────────────────
echo "[1/8] Instalando dependencias do sistema..."
apt-get update -qq
apt-get install -y -qq \
    git curl wget \
    nginx certbot python3-certbot-nginx \
    docker.io docker-compose \
    ufw

# ── 2. Habilitar e iniciar Docker ─────────────────────────────────────────
echo "[2/8] Configurando Docker..."
systemctl enable docker
systemctl start docker

# ── 3. Criar usuário de deploy (se não existir) ──────────────────────────
echo "[3/8] Criando usuario de deploy..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
    usermod -aG docker "$APP_USER"
    echo "Usuario '$APP_USER' criado e adicionado ao grupo docker."
else
    usermod -aG docker "$APP_USER" 2>/dev/null || true
    echo "Usuario '$APP_USER' ja existe."
fi

# ── 4. Clonar o repositório ───────────────────────────────────────────────
echo "[4/8] Clonando repositorio GitHub..."
mkdir -p "$(dirname "$APP_DIR")"
if [ -d "$APP_DIR/.git" ]; then
    echo "Repositorio ja clonado. Atualizando..."
    cd "$APP_DIR"
    git fetch origin
    git checkout "$APP_BRANCH"
    git pull origin "$APP_BRANCH"
else
    git clone --branch "$APP_BRANCH" "$REPO_URL" "$APP_DIR"
fi
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# ── 5. Criar arquivo .env de produção ────────────────────────────────────
echo "[5/8] Verificando .env de producao..."
ENV_FILE="$APP_DIR/flask/.env.production"
if [ ! -f "$ENV_FILE" ] || grep -q "change_this" "$ENV_FILE"; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    DB_PASS=$(python3 -c "import secrets; print(secrets.token_hex(16))")
    cat > "$ENV_FILE" <<EOF
FLASK_ENV=production
SECRET_KEY=${SECRET}
DEBUG=False

# Banco de dados (PostgreSQL via Docker)
DATABASE_URL=postgresql://finan_user:${DB_PASS}@finan_db:5432/finan_db
DB_USER=finan_user
DB_PASSWORD=${DB_PASS}
DB_NAME=finan_db
EOF
    echo "ATENCAO: .env.production criado com senha gerada automaticamente."
    echo "  DB_PASSWORD: ${DB_PASS}"
    echo "  Guarde essa senha em local seguro!"
fi

# ── 6. Configurar Nginx ───────────────────────────────────────────────────
echo "[6/8] Configurando Nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/finan_pub
ln -sf /etc/nginx/sites-available/finan_pub /etc/nginx/sites-enabled/finan_pub
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl reload nginx

# ── 7. Firewall ───────────────────────────────────────────────────────────
echo "[7/8] Configurando firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# ── 8. Construir e subir containers ──────────────────────────────────────
echo "[8/8] Subindo containers Docker..."
cd "$APP_DIR/flask"
docker-compose -f ../deploy/docker-compose.prod.yml up -d --build

echo ""
echo "======================================"
echo " SETUP CONCLUIDO!"
echo "======================================"
echo ""
echo "Proximos passos:"
echo "  1. Configure o SSL:"
echo "     sudo certbot --nginx -d finan.automathos.cloud -d www.finan.automathos.cloud"
echo ""
echo "  2. Para atualizar a aplicacao no futuro, execute:"
echo "     bash $APP_DIR/deploy/3_deploy.sh"
echo ""
echo "  3. Verifique os logs:"
echo "     docker-compose -f $APP_DIR/deploy/docker-compose.prod.yml logs -f finan_web"
echo ""

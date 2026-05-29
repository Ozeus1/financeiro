#!/bin/bash
# 3_deploy.sh
# Atualiza a aplicação na VPS a partir do GitHub.
# Execute na VPS: bash /home/deploy/finan_pub/deploy/3_deploy.sh

set -e

APP_DIR="/home/deploy/finan_pub"
COMPOSE_FILE="$APP_DIR/deploy/docker-compose.prod.yml"
BRANCH="finan_pub"

echo "======================================"
echo " DEPLOY - finan_pub"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================"

# ── 1. Backup rápido do banco ─────────────────────────────────────────────
echo "[1/5] Criando backup do banco de dados..."
BACKUP_DIR="$APP_DIR/backups"
mkdir -p "$BACKUP_DIR"
if docker ps --format '{{.Names}}' | grep -q "finan_db"; then
    docker exec finan_db pg_dump -U finan_user finan_db \
        > "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql" 2>/dev/null \
        && echo "Backup criado em $BACKUP_DIR" \
        || echo "Aviso: backup do banco falhou (pode estar vazio na primeira vez)."
fi

# ── 2. Atualizar código ───────────────────────────────────────────────────
echo "[2/5] Atualizando codigo do GitHub..."
cd "$APP_DIR"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

# ── 3. Reconstruir imagem e subir ─────────────────────────────────────────
echo "[3/5] Reconstruindo containers..."
docker-compose -f "$COMPOSE_FILE" build --no-cache finan_web

# ── 4. Reiniciar sem downtime ─────────────────────────────────────────────
echo "[4/5] Reiniciando servicos..."
docker-compose -f "$COMPOSE_FILE" up -d

# ── 5. Verificar saúde ───────────────────────────────────────────────────
echo "[5/5] Verificando saude da aplicacao..."
sleep 5
if docker ps --format '{{.Names}}\t{{.Status}}' | grep "finan_web" | grep -q "Up"; then
    echo ""
    echo "======================================"
    echo " DEPLOY CONCLUIDO COM SUCESSO!"
    echo " Acesse: https://www.finan.automathos.cloud"
    echo "======================================"
else
    echo ""
    echo "ATENCAO: container pode nao ter subido corretamente."
    echo "Verifique: docker-compose -f $COMPOSE_FILE logs finan_web"
    exit 1
fi

# Limpar imagens antigas para liberar espaço
docker image prune -f --filter "until=24h" 2>/dev/null || true

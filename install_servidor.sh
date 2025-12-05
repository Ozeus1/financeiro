#!/bin/bash
# Script de instalação rápida no servidor VPS
# Execute com: bash install_servidor.sh

set -e  # Parar em caso de erro

echo "======================================================"
echo "  INSTALAÇÃO AUTOMÁTICA - SISTEMA FINANCEIRO"
echo "======================================================"
echo ""

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para printar com cor
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
    echo "Uso: sudo bash install_servidor.sh"
    exit 1
fi

# 1. Atualizar sistema
echo "1️⃣  Atualizando sistema..."
apt update -y
apt upgrade -y
print_success "Sistema atualizado"

# 2. Instalar PostgreSQL
echo ""
echo "2️⃣  Instalando PostgreSQL..."
if ! command -v psql &> /dev/null; then
    apt install postgresql postgresql-contrib -y
    systemctl start postgresql
    systemctl enable postgresql
    print_success "PostgreSQL instalado"
else
    print_warning "PostgreSQL já está instalado"
fi

# 3. Instalar Python e dependências
echo ""
echo "3️⃣  Instalando Python e ferramentas..."
apt install python3 python3-pip python3-venv git -y
print_success "Python instalado"

# 4. Instalar Nginx
echo ""
echo "4️⃣  Instalando Nginx..."
if ! command -v nginx &> /dev/null; then
    apt install nginx -y
    systemctl start nginx
    systemctl enable nginx
    print_success "Nginx instalado"
else
    print_warning "Nginx já está instalado"
fi

# 5. Criar estrutura de diretórios
echo ""
echo "5️⃣  Criando estrutura de diretórios..."
mkdir -p /var/www/financeiro
mkdir -p /var/www/financeiro/uploads
mkdir -p /var/log/financeiro
print_success "Diretórios criados"

# 6. Clonar repositório (se ainda não existe)
echo ""
echo "6️⃣  Verificando repositório..."
if [ ! -d "/var/www/financeiro/.git" ]; then
    echo "Digite a URL do repositório Git:"
    echo "(Exemplo: https://github.com/Ozeus1/financeiro.git)"
    read -p "URL: " REPO_URL

    if [ ! -z "$REPO_URL" ]; then
        cd /var/www
        rm -rf financeiro
        git clone $REPO_URL financeiro
        print_success "Repositório clonado"
    else
        print_warning "URL não fornecida. Pule esta etapa se já tem os arquivos no servidor"
    fi
else
    print_warning "Repositório já existe em /var/www/financeiro"
    cd /var/www/financeiro
    git pull
    print_success "Repositório atualizado"
fi

# 7. Criar ambiente virtual e instalar dependências
echo ""
echo "7️⃣  Configurando ambiente Python..."
cd /var/www/financeiro

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Ambiente virtual criado"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependências instaladas"

# 8. Executar setup do banco de dados
echo ""
echo "8️⃣  Configurando banco de dados..."
print_warning "Execute o script de setup do banco:"
echo "   sudo python3 setup_production.py"
echo ""
read -p "Deseja executar agora? (s/n): " RUN_SETUP

if [ "$RUN_SETUP" = "s" ]; then
    python3 setup_production.py
    print_success "Banco configurado"

    # 9. Inicializar banco
    echo ""
    echo "9️⃣  Inicializando tabelas do banco..."
    python3 init_production_db.py
    print_success "Banco inicializado"
fi

# 10. Configurar permissões
echo ""
echo "🔒 Configurando permissões..."
chown -R www-data:www-data /var/www/financeiro
chmod -R 755 /var/www/financeiro
chmod 600 /var/www/financeiro/.env 2>/dev/null || true
chown -R www-data:www-data /var/log/financeiro
print_success "Permissões configuradas"

# 11. Criar serviço systemd
echo ""
echo "⚙️  Criando serviço systemd..."
cat > /etc/systemd/system/financeiro.service << 'EOF'
[Unit]
Description=Sistema Financeiro Flask App
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/financeiro
Environment="PATH=/var/www/financeiro/venv/bin"
ExecStart=/var/www/financeiro/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable financeiro.service
print_success "Serviço criado"

# 12. Configurar Nginx
echo ""
echo "🌐 Configurando Nginx..."
read -p "Digite o domínio do servidor (ou deixe em branco para usar IP): " DOMAIN

if [ -z "$DOMAIN" ]; then
    DOMAIN="_"
    print_warning "Usando configuração sem domínio específico"
fi

cat > /etc/nginx/sites-available/financeiro << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/financeiro/static;
        expires 30d;
    }

    location /uploads {
        alias /var/www/financeiro/uploads;
        internal;
    }
}
EOF

# Ativar site
ln -sf /etc/nginx/sites-available/financeiro /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
print_success "Nginx configurado"

# Resumo final
echo ""
echo "======================================================"
print_success "INSTALAÇÃO CONCLUÍDA!"
echo "======================================================"
echo ""
echo "📝 Próximos passos:"
echo ""
echo "1. Se ainda não executou, configure o banco:"
echo "   cd /var/www/financeiro"
echo "   sudo python3 setup_production.py"
echo "   python3 init_production_db.py"
echo ""
echo "2. Inicie o serviço:"
echo "   sudo systemctl start financeiro"
echo "   sudo systemctl status financeiro"
echo ""
echo "3. Acesse a aplicação:"
if [ "$DOMAIN" = "_" ]; then
    echo "   http://SEU_IP_DO_SERVIDOR"
else
    echo "   http://$DOMAIN"
fi
echo ""
echo "4. Credenciais padrão:"
echo "   Usuário: admin"
echo "   Senha: admin123"
echo "   ⚠️  ALTERE A SENHA APÓS O PRIMEIRO LOGIN!"
echo ""
echo "5. Ver logs:"
echo "   sudo journalctl -u financeiro -f"
echo "   tail -f /var/log/financeiro/app.log"
echo ""
echo "6. Comandos úteis:"
echo "   Reiniciar: sudo systemctl restart financeiro"
echo "   Parar: sudo systemctl stop financeiro"
echo "   Ver status: sudo systemctl status financeiro"
echo ""
print_success "Instalação completa!"
echo "======================================================"

# 🚀 Deploy Final - Sistema Financeiro

Guia rápido para colocar o sistema em produção no domínio **finan.receberbemevinhos.com.br**

## ✅ Status Atual

- ✅ Banco de dados PostgreSQL configurado
- ✅ Tabelas criadas e populadas
- ✅ Usuário admin criado (admin/admin123)
- ⏳ Nginx precisa ser configurado
- ⏳ Serviço precisa ser iniciado
- ⏳ SSL precisa ser configurado

## 📋 Próximos Passos

### 1. Configurar o Nginx para o seu domínio

```bash
# No servidor
cd /var/www/financeiro

# Copiar configuração do Nginx
sudo cp nginx_finan.conf /etc/nginx/sites-available/financeiro

# Ativar o site
sudo ln -sf /etc/nginx/sites-available/financeiro /etc/nginx/sites-enabled/

# Remover configuração padrão
sudo rm -f /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t

# Recarregar Nginx
sudo systemctl reload nginx
```

### 2. Iniciar o serviço da aplicação

```bash
# Verificar se o serviço existe
sudo systemctl status financeiro

# Se não existir, criar:
sudo cat > /etc/systemd/system/financeiro.service << 'EOF'
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

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar e iniciar o serviço
sudo systemctl enable financeiro
sudo systemctl start financeiro

# Verificar status
sudo systemctl status financeiro
```

### 3. Configurar SSL/HTTPS (Let's Encrypt)

**IMPORTANTE:** Antes de executar, certifique-se que:
- O DNS do domínio está apontando para o IP do servidor
- As portas 80 e 443 estão abertas no firewall

```bash
cd /var/www/financeiro
sudo bash setup_ssl.sh
```

### 4. Verificar se está funcionando

```bash
# Testar localmente
curl http://localhost:8000

# Testar pelo domínio (HTTP)
curl http://finan.receberbemevinhos.com.br

# Testar HTTPS (após configurar SSL)
curl https://finan.receberbemevinhos.com.br
```

### 5. Acessar o sistema

🌐 **URL:** https://finan.receberbemevinhos.com.br

👤 **Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin123`

⚠️ **IMPORTANTE:** Altere a senha imediatamente após o primeiro login!

## 🔧 Comandos Úteis

### Gerenciar o serviço

```bash
# Ver logs em tempo real
sudo journalctl -u financeiro -f

# Ver status
sudo systemctl status financeiro

# Reiniciar
sudo systemctl restart financeiro

# Parar
sudo systemctl stop financeiro

# Iniciar
sudo systemctl start financeiro
```

### Logs da aplicação

```bash
# Logs do Nginx
sudo tail -f /var/log/nginx/financeiro_access.log
sudo tail -f /var/log/nginx/financeiro_error.log

# Logs da aplicação (se configurado)
tail -f /var/log/financeiro/app.log
```

### Atualizar a aplicação

```bash
cd /var/www/financeiro

# Baixar atualizações
git pull

# Ativar ambiente virtual
source venv/bin/activate

# Atualizar dependências
pip install -r requirements.txt

# Reiniciar serviço
sudo systemctl restart financeiro
```

### Backup do banco de dados

```bash
# Fazer backup
sudo -u postgres pg_dump financeiro > backup_$(date +%Y%m%d).sql

# Restaurar backup
sudo -u postgres psql financeiro < backup_20231205.sql
```

## 🔒 Segurança

### Firewall (UFW)

```bash
# Habilitar firewall
sudo ufw enable

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP e HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Ver status
sudo ufw status
```

### Alterar senha do PostgreSQL

```bash
sudo -u postgres psql
```

```sql
ALTER USER financeiro_user WITH PASSWORD 'nova_senha_super_segura';
\q
```

Depois atualizar o `.env`:

```bash
sudo nano /var/www/financeiro/.env
# Alterar a linha DATABASE_URL com a nova senha
```

### Permissões corretas

```bash
# Garantir permissões corretas
sudo chown -R www-data:www-data /var/www/financeiro
sudo chmod 600 /var/www/financeiro/.env
sudo chmod -R 755 /var/www/financeiro
```

## 🆘 Troubleshooting

### Erro 502 Bad Gateway

```bash
# Verificar se o serviço está rodando
sudo systemctl status financeiro

# Ver logs
sudo journalctl -u financeiro -n 50

# Testar manualmente
cd /var/www/financeiro
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 wsgi:app
```

### Erro de conexão ao banco

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
sudo -u postgres psql -c "\l"

# Verificar credenciais no .env
cat /var/www/financeiro/.env | grep DATABASE
```

### Erro de importação de módulos

```bash
cd /var/www/financeiro
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

## 📊 Monitoramento

### Verificar uso de recursos

```bash
# CPU e memória
htop

# Espaço em disco
df -h

# Conexões ao banco
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'financeiro';"
```

### Verificar certificado SSL

```bash
# Ver data de expiração
sudo certbot certificates

# Renovar manualmente (se necessário)
sudo certbot renew

# Testar renovação
sudo certbot renew --dry-run
```

## 🎯 Checklist Final

- [ ] Nginx configurado para o domínio
- [ ] Serviço financeiro rodando
- [ ] SSL/HTTPS configurado
- [ ] Domínio acessível via HTTPS
- [ ] Login funcionando
- [ ] Senha do admin alterada
- [ ] Firewall configurado
- [ ] Logs funcionando
- [ ] Backup configurado
- [ ] Renovação automática de SSL ativa

---

**🎉 Parabéns! Seu sistema está em produção!**

Acesse: https://finan.receberbemevinhos.com.br

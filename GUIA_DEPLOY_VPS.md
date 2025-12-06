# 🚀 Guia Completo de Deploy - Sistema Financeiro Flask

Este guia detalha TODOS os passos para fazer o deploy da aplicação Flask em uma VPS (Ubuntu/Debian).

---

## 📋 Pré-requisitos

- VPS com Ubuntu 20.04+ ou Debian 11+
- Acesso SSH (root ou sudo)
- Domínio (opcional, mas recomendado)
- Repositório GitHub configurado

---

## 🎯 PASSO 1: Preparar o Repositório GitHub

### 1.1 - Commitar as alterações

No seu computador local (Windows), execute:

```bash
# Adicionar todos os novos arquivos
git add .

# Criar commit
git commit -m "Preparar aplicação para deploy em produção

- Adicionar wsgi.py para Gunicorn
- Adicionar gunicorn ao requirements.txt
- Criar configurações Nginx e Systemd
- Adicionar script de inicialização do banco
- Atualizar .gitignore e .env.example"

# Enviar para GitHub
git push origin main
```

### 1.2 - Verificar no GitHub

Acesse seu repositório GitHub e confirme que todos os arquivos foram enviados corretamente:
- `wsgi.py`
- `requirements.txt` (atualizado)
- `financeiro.service`
- `nginx_financeiro.conf`
- `init_production_db.py`
- `.env.example`
- `.gitignore`

---

## 🔧 PASSO 2: Configurar o Servidor VPS

### 2.1 - Conectar via SSH

```bash
ssh seu_usuario@IP_DA_SUA_VPS
```

### 2.2 - Atualizar o sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 - Instalar dependências do sistema

```bash
# Python e ferramentas essenciais
sudo apt install -y python3 python3-pip python3-venv git nginx

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Bibliotecas necessárias para compilar pacotes Python
sudo apt install -y build-essential libpq-dev python3-dev
```

---

## 🗄️ PASSO 3: Configurar PostgreSQL

### 3.1 - Acessar PostgreSQL

```bash

```

### 3.2 - Criar banco e usuário

Execute dentro do PostgreSQL:

```sql
-- Criar banco de dados
CREATE DATABASE financeiro;

-- Criar usuário (MUDE A SENHA!)
CREATE USER financeiro_user WITH PASSWORD 'sua_senha_segura_aqui';

-- Dar permissões
GRANT ALL PRIVILEGES ON DATABASE financeiro TO financeiro_user;

-- Sair
\q
```

### 3.3 - Testar conexão

```bash
psql -h localhost -U financeiro_user -d financeiro
# Digite a senha quando solicitado
# Se conectar com sucesso, digite \q para sair
```

---

## 📦 PASSO 4: Clonar e Configurar a Aplicação

### 4.1 - Criar diretório da aplicação

```bash
sudo mkdir -p /var/www/financeiro
sudo chown $USER:www-data /var/www/financeiro
```

### 4.2 - Clonar repositório

```bash
cd /var/www
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git financeiro
cd financeiro
```

### 4.3 - Criar ambiente virtual

```bash
python3 -m venv venv
```

### 4.4 - Ativar ambiente virtual

```bash
source venv/bin/activate
```

### 4.5 - Instalar dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ PASSO 5: Configurar Variáveis de Ambiente

### 5.1 - Criar arquivo .env

```bash
cp .env.example .env
nano .env
```

### 5.2 - Editar o arquivo .env

Configure com suas credenciais reais:

```env
# Gerar chave secreta segura
SECRET_KEY=cole_aqui_a_chave_gerada_abaixo

# Configuração do banco PostgreSQL
DATABASE_URL=postgresql://financeiro_user:sua_senha_segura_aqui@localhost:5432/financeiro

# Ambiente de produção
FLASK_ENV=production
FLASK_DEBUG=False
```

### 5.3 - Gerar SECRET_KEY

Execute este comando para gerar uma chave segura:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copie o resultado e cole no campo `SECRET_KEY` do arquivo `.env`.

Salve e feche (Ctrl+O, Enter, Ctrl+X).

---

## 🔨 PASSO 6: Inicializar Banco de Dados

### 6.1 - Executar script de inicialização

```bash
python3 init_production_db.py
```

Você deve ver uma mensagem de sucesso com as credenciais padrão:
- **Usuário:** admin
- **Senha:** admin123

⚠️ **IMPORTANTE:** Altere essa senha após o primeiro login!

### 6.2 - Verificar tabelas criadas

```bash
psql -h localhost -U financeiro_user -d financeiro -c "\dt"
```

Você deve ver todas as tabelas listadas.

---

## 🚦 PASSO 7: Configurar Gunicorn (Servidor WSGI)

### 7.1 - Testar Gunicorn manualmente

```bash
# Ainda com venv ativo
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

Abra o navegador e acesse: `http://IP_DA_SUA_VPS:8000`

Se funcionar, pressione Ctrl+C para parar.

### 7.2 - Configurar como serviço systemd

```bash
# Editar arquivo de serviço
sudo nano financeiro.service
```

Atualize a linha `User=seu_usuario` com seu nome de usuário real:

```ini
User=seu_nome_de_usuario_aqui
```

Salve e feche (Ctrl+O, Enter, Ctrl+X).

### 7.3 - Copiar para systemd

```bash
sudo cp financeiro.service /etc/systemd/system/
```

### 7.4 - Ajustar permissões

```bash
sudo chown www-data:www-data /var/www/financeiro
sudo chmod 755 /var/www/financeiro
```

### 7.5 - Ativar e iniciar o serviço

```bash
# Recarregar daemon
sudo systemctl daemon-reload

# Ativar para iniciar no boot
sudo systemctl enable financeiro

# Iniciar o serviço
sudo systemctl start financeiro

# Verificar status
sudo systemctl status financeiro
```

Se estiver **active (running)** em verde, está funcionando! ✅

### 7.6 - Comandos úteis do serviço

```bash
# Ver logs em tempo real
sudo journalctl -u financeiro -f

# Reiniciar serviço
sudo systemctl restart financeiro

# Parar serviço
sudo systemctl stop financeiro

# Ver status
sudo systemctl status financeiro
```

---

## 🌐 PASSO 8: Configurar Nginx (Proxy Reverso)

### 8.1 - Editar configuração Nginx

```bash
# Editar o arquivo de configuração
nano nginx_financeiro.conf
```

Substitua `seu_dominio.com` pelo seu domínio ou IP:

```nginx
server_name seu_dominio.com www.seu_dominio.com;
```

Se usar apenas IP:

```nginx
server_name IP_DA_SUA_VPS;
```

Salve e feche.

### 8.2 - Copiar configuração para Nginx

```bash
sudo cp nginx_financeiro.conf /etc/nginx/sites-available/financeiro
```

### 8.3 - Criar link simbólico

```bash
sudo ln -s /etc/nginx/sites-available/financeiro /etc/nginx/sites-enabled/
```

### 8.4 - Remover configuração padrão (opcional)

```bash
sudo rm /etc/nginx/sites-enabled/default
```

### 8.5 - Testar configuração Nginx

```bash
sudo nginx -t
```

Se mostrar "syntax is ok" e "test is successful", está correto! ✅

### 8.6 - Reiniciar Nginx

```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 8.7 - Ajustar Firewall (se ativo)

```bash
# Permitir HTTP e HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

---

## 🎉 PASSO 9: Testar a Aplicação

### 9.1 - Acessar no navegador

Abra seu navegador e acesse:

```
http://SEU_DOMINIO_OU_IP
```

Você deve ver a página de login da aplicação! 🎊

### 9.2 - Fazer login inicial

- **Usuário:** admin
- **Senha:** admin123

### 9.3 - ALTERAR SENHA DO ADMIN

⚠️ **MUITO IMPORTANTE:** Vá para Configurações e altere a senha padrão imediatamente!

---

## 🔒 PASSO 10: Configurar HTTPS com SSL (OPCIONAL mas RECOMENDADO)

### 10.1 - Instalar Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 10.2 - Obter certificado SSL

```bash
sudo certbot --nginx -d seu_dominio.com -d www.seu_dominio.com
```

Siga as instruções interativas:
- Digite seu email
- Aceite os termos de serviço
- Escolha redirecionar HTTP para HTTPS (opção 2)

### 10.3 - Renovação automática

O Certbot já configura renovação automática. Para testar:

```bash
sudo certbot renew --dry-run
```

### 10.4 - Acessar com HTTPS

Agora acesse:

```
https://seu_dominio.com
```

Deve mostrar o cadeado verde! 🔒

---

## 🔄 PASSO 11: Atualizar a Aplicação (Deploys Futuros)

Quando fizer alterações no código e quiser atualizar o servidor:

### 11.1 - Conectar via SSH

```bash
ssh seu_usuario@IP_DA_SUA_VPS
```

### 11.2 - Ir para o diretório da aplicação

```bash
cd /var/www/financeiro
```

### 11.3 - Ativar ambiente virtual

```bash
source venv/bin/activate
```

### 11.4 - Baixar alterações do GitHub

```bash
git pull origin main
```

### 11.5 - Instalar novas dependências (se houver)

```bash
pip install -r requirements.txt
```

### 11.6 - Aplicar migrações de banco (se necessário)

```bash
python3 init_production_db.py
```

### 11.7 - Reiniciar o serviço

```bash
sudo systemctl restart financeiro
```

### 11.8 - Verificar se está funcionando

```bash
sudo systemctl status financeiro
```

---

## 🛠️ TROUBLESHOOTING - Problemas Comuns

### Problema 1: Erro 502 Bad Gateway

**Solução:**

```bash
# Verificar se Gunicorn está rodando
sudo systemctl status financeiro

# Ver logs
sudo journalctl -u financeiro -n 50

# Reiniciar
sudo systemctl restart financeiro
```

### Problema 2: Erro de conexão com banco de dados

**Solução:**

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão manual
psql -h localhost -U financeiro_user -d financeiro

# Verificar .env
cat /var/www/financeiro/.env
```

### Problema 3: Erro de permissões

**Solução:**

```bash
# Ajustar permissões
sudo chown -R www-data:www-data /var/www/financeiro
sudo chmod -R 755 /var/www/financeiro

# Reiniciar serviços
sudo systemctl restart financeiro
sudo systemctl restart nginx
```

### Problema 4: Arquivos estáticos não carregam (CSS/JS)

**Solução:**

```bash
# Verificar pasta static
ls -la /var/www/financeiro/static

# Ajustar permissões
sudo chmod -R 755 /var/www/financeiro/static

# Reiniciar Nginx
sudo systemctl restart nginx
```

### Problema 5: Ver logs detalhados

**Logs da aplicação:**

```bash
sudo journalctl -u financeiro -f
```

**Logs do Nginx:**

```bash
# Logs de erro
sudo tail -f /var/log/nginx/financeiro_error.log

# Logs de acesso
sudo tail -f /var/log/nginx/financeiro_access.log
```

**Logs do PostgreSQL:**

```bash
sudo tail -f /var/log/postgresql/postgresql-*.log
```

---

## 📊 PASSO 12: Monitoramento e Manutenção

### 12.1 - Ver uso de recursos

```bash
# CPU e memória
htop

# Espaço em disco
df -h

# Conexões PostgreSQL ativas
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

### 12.2 - Fazer backup do banco

```bash
# Criar backup
pg_dump -h localhost -U financeiro_user financeiro > backup_$(date +%Y%m%d).sql

# Restaurar backup (se necessário)
psql -h localhost -U financeiro_user financeiro < backup_20250101.sql
```

### 12.3 - Atualizações de segurança do sistema

Execute periodicamente:

```bash
sudo apt update && sudo apt upgrade -y
sudo systemctl restart financeiro
```

---

## ✅ CHECKLIST FINAL

Marque cada item após completar:

- [ ] **Passo 1:** Código enviado para GitHub
- [ ] **Passo 2:** VPS atualizada e dependências instaladas
- [ ] **Passo 3:** PostgreSQL configurado e banco criado
- [ ] **Passo 4:** Aplicação clonada e dependências instaladas
- [ ] **Passo 5:** Arquivo .env configurado com SECRET_KEY única
- [ ] **Passo 6:** Banco de dados inicializado
- [ ] **Passo 7:** Gunicorn rodando como serviço
- [ ] **Passo 8:** Nginx configurado e rodando
- [ ] **Passo 9:** Aplicação acessível no navegador
- [ ] **Passo 10:** SSL/HTTPS configurado (opcional)
- [ ] **Senha admin alterada**
- [ ] **Backup configurado**

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs (journalctl, nginx logs)
2. Revise cada passo cuidadosamente
3. Consulte a documentação oficial de cada ferramenta

---

## 🎓 Comandos Úteis Resumidos

```bash
# Ver status de tudo
sudo systemctl status financeiro nginx postgresql

# Reiniciar aplicação
sudo systemctl restart financeiro

# Ver logs em tempo real
sudo journalctl -u financeiro -f

# Atualizar código
cd /var/www/financeiro && git pull && sudo systemctl restart financeiro

# Backup banco
pg_dump -h localhost -U financeiro_user financeiro > backup.sql

# Gerar nova SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

**🎉 Parabéns! Sua aplicação está em produção!** 🚀

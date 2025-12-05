# Guia de Setup Automático do Servidor

Este guia explica como usar o script `setup_production.py` para configurar automaticamente o PostgreSQL no seu servidor VPS.

## 📋 Pré-requisitos

1. Servidor VPS com Ubuntu/Debian
2. Acesso root ou sudo
3. PostgreSQL instalado

## 🚀 Passo a Passo

### 1. Enviar arquivos para o servidor

No seu computador local, envie os arquivos necessários:

```bash
# Clonar o repositório no servidor
ssh root@seu-servidor
cd /var/www
git clone https://github.com/Ozeus1/financeiro.git
cd financeiro
```

### 2. Executar o script de setup

```bash
# Tornar o script executável
chmod +x setup_production.py

# Executar com sudo
sudo python3 setup_production.py
```

### 3. O que o script faz automaticamente

✅ Verifica se PostgreSQL está instalado
✅ Gera senha segura automaticamente
✅ Cria banco de dados `financeiro`
✅ Cria usuário `financeiro_user`
✅ Configura permissões corretas
✅ Cria arquivo `.env` com todas as configurações
✅ Testa a conexão com o banco
✅ Cria diretórios necessários

### 4. Após o script executar

O script mostrará as credenciais geradas:

```
📝 Credenciais do banco (GUARDE COM SEGURANÇA):
   Database: financeiro
   User: financeiro_user
   Password: [senha_gerada_automaticamente]
   Connection String: postgresql://financeiro_user:senha@localhost:5432/financeiro
```

**⚠️ IMPORTANTE: Copie e guarde essas credenciais em local seguro!**

### 5. Instalar dependências Python

```bash
# Instalar pip se não tiver
sudo apt install python3-pip python3-venv -y

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 6. Inicializar o banco de dados

```bash
# Criar as tabelas e dados iniciais
python3 init_production_db.py
```

Isso criará:
- Todas as tabelas do sistema
- Usuário administrador padrão
- Categorias padrão
- Meios de pagamento padrão

**Credenciais do admin:**
- Usuário: `admin`
- Senha: `admin123`

⚠️ **Altere a senha após o primeiro login!**

### 7. Testar a aplicação

```bash
# Rodar em modo de desenvolvimento (teste)
python3 app.py
```

Acesse: `http://seu-servidor:5000`

### 8. Configurar para produção

Para rodar em produção, use Gunicorn + Nginx:

```bash
# Instalar Gunicorn
pip install gunicorn

# Rodar com Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

## 🔧 Configuração Manual (alternativa)

Se preferir configurar manualmente ao invés de usar o script:

### 1. Criar banco manualmente

```bash
sudo -u postgres psql
```

```sql
CREATE USER financeiro_user WITH PASSWORD 'sua_senha_forte';
CREATE DATABASE financeiro OWNER financeiro_user;
GRANT ALL PRIVILEGES ON DATABASE financeiro TO financeiro_user;
\c financeiro
GRANT ALL ON SCHEMA public TO financeiro_user;
\q
```

### 2. Criar arquivo .env manualmente

Copie o arquivo `.env.example` e edite:

```bash
cp .env.example .env
nano .env
```

Configure as variáveis:

```env
DATABASE_URL=postgresql://financeiro_user:sua_senha@localhost:5432/financeiro
SECRET_KEY=sua_chave_secreta_muito_segura
FLASK_ENV=production
DEBUG=False
```

## 📝 Estrutura de Diretórios Criados

```
/var/www/financeiro/          # Aplicação
/var/www/financeiro/uploads/  # Arquivos enviados
/var/log/financeiro/          # Logs da aplicação
```

## ⚙️ Configuração do Nginx (Opcional)

Arquivo: `/etc/nginx/sites-available/financeiro`

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /var/www/financeiro/static;
    }
}
```

Ativar:

```bash
sudo ln -s /etc/nginx/sites-available/financeiro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Segurança

- ✅ Arquivo `.env` tem permissões 600 (apenas owner pode ler)
- ✅ Senhas são geradas com 20 caracteres aleatórios
- ✅ SECRET_KEY do Flask é gerada automaticamente
- ✅ Banco de dados só aceita conexões localhost por padrão

## 🆘 Troubleshooting

### Erro: "PostgreSQL não está instalado"

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
```

### Erro: "Permissão negada"

Execute o script com `sudo`:

```bash
sudo python3 setup_production.py
```

### Erro: "Não consegue conectar ao banco"

Verifique se o PostgreSQL está rodando:

```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Ver logs do PostgreSQL

```bash
sudo tail -f /var/log/postgresql/postgresql-*.log
```

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs: `/var/log/financeiro/app.log`
2. Teste a conexão manualmente: `psql -U financeiro_user -d financeiro`
3. Verifique as permissões do arquivo `.env`: `ls -l .env`

## ✅ Checklist Final

- [ ] PostgreSQL instalado e rodando
- [ ] Script `setup_production.py` executado com sucesso
- [ ] Arquivo `.env` criado e com permissões corretas
- [ ] Credenciais do banco anotadas em local seguro
- [ ] Dependências Python instaladas
- [ ] Banco de dados inicializado (`init_production_db.py`)
- [ ] Aplicação testada e funcionando
- [ ] Senha do admin alterada
- [ ] Nginx configurado (opcional)
- [ ] SSL/HTTPS configurado (recomendado)

---

**Gerado para o Sistema Financeiro v15**
**Repositório:** https://github.com/Ozeus1/financeiro

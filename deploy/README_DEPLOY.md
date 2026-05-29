# Deploy: finan_pub → VPS via GitHub

## Domínio: www.finan.automathos.cloud
## Pasta na VPS: /home/deploy/finan_pub

---

## Fluxo geral

```
Local (Windows) ──git push──► GitHub (branch: finan_pub)
                                        │
                                        ▼ (ssh)
                              VPS: git pull
                              docker-compose up --build
                              Nginx → proxy → Gunicorn:5000
```

---

## PASSO A PASSO COMPLETO

### ETAPA 1 — Primeiro push (executar apenas uma vez)

No PowerShell do Windows:
```powershell
.\deploy\5_primeiro_push.ps1
```
Isso adiciona `flask/` e `deploy/` ao GitHub no branch `finan_pub`.

---

### ETAPA 2 — Setup inicial da VPS (executar apenas uma vez)

Você precisa ter o SSH configurado. Execute no PowerShell:
```powershell
ssh root@IP_DA_VPS "bash -s" < deploy/2_setup_vps.sh
```

O script faz automaticamente:
- Instala Docker, Nginx, Certbot
- Cria usuário `deploy`
- Clona o repositório em `/home/deploy/finan_pub`
- Gera `.env.production` com senhas seguras
- Configura Nginx
- Sobe os containers Docker

> **Guarde a senha do banco** que aparece na saída do script!

---

### ETAPA 3 — Configurar SSL (executar apenas uma vez)

> Pré-requisito: DNS do domínio já apontando para o IP da VPS.
> Configure o registro A: `finan.automathos.cloud` → `IP_DA_VPS`
> Configure o registro CNAME: `www` → `finan.automathos.cloud`

```bash
ssh root@IP_DA_VPS
sudo certbot --nginx -d finan.automathos.cloud -d www.finan.automathos.cloud
```

O certbot configura HTTPS e renovação automática.

---

### ETAPA 4 — Deploy e atualizações futuras

Edite o IP no script `4_atualizar_remoto.ps1`:
```
$VPS_IP = "IP_DA_VPS"
```

Depois, sempre que quiser atualizar:
```powershell
.\deploy\4_atualizar_remoto.ps1 -Mensagem "feat: minha nova funcionalidade"
```

Isso faz:
1. Commit + push local → GitHub
2. SSH na VPS → git pull → docker-compose up --build

---

## Estrutura dos arquivos de deploy

```
deploy/
├── README_DEPLOY.md          ← este arquivo
├── 1_push_github.ps1         ← push local → GitHub
├── 2_setup_vps.sh            ← setup inicial da VPS
├── 3_deploy.sh               ← atualiza app na VPS
├── 4_atualizar_remoto.ps1    ← atalho: push + deploy (uso diário)
├── 5_primeiro_push.ps1       ← adiciona flask/ ao git (1x)
├── docker-compose.prod.yml   ← Docker Compose de produção
├── nginx.conf                ← config Nginx + SSL
└── .env.production.example   ← modelo de variáveis de ambiente
```

---

## Verificação e diagnóstico

### Ver logs da aplicação
```bash
ssh root@IP_DA_VPS
docker logs finan_web -f
```

### Ver logs do Nginx
```bash
sudo tail -f /var/log/nginx/error.log
```

### Status dos containers
```bash
docker ps
docker-compose -f /home/deploy/finan_pub/deploy/docker-compose.prod.yml ps
```

### Reiniciar manualmente
```bash
cd /home/deploy/finan_pub
docker-compose -f deploy/docker-compose.prod.yml restart finan_web
```

### Testar localmente antes de enviar
```bash
# No Windows, testando com Docker local:
cd flask
docker-compose up --build
# Acesse: http://localhost:5000
```

---

## Variáveis de ambiente (.env.production)

O arquivo `flask/.env.production` **nunca vai ao GitHub** (está no .gitignore).
Na primeira vez, o `2_setup_vps.sh` gera automaticamente.

Para editar na VPS:
```bash
nano /home/deploy/finan_pub/flask/.env.production
docker-compose -f /home/deploy/finan_pub/deploy/docker-compose.prod.yml restart finan_web
```

---

## Arquitetura de produção

```
Internet → DNS (finan.automathos.cloud)
              │
              ▼
         VPS (porta 443)
              │
         Nginx (SSL/TLS)
              │
         proxy_pass 127.0.0.1:5000
              │
         Docker: finan_web (Gunicorn)
              │
         Docker: finan_db (PostgreSQL 15)
```

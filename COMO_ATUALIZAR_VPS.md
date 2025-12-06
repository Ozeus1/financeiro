# 🚀 Como Atualizar o Servidor VPS

## Método 1: Script Automático (RECOMENDADO)

### 1. Copiar o script para o servidor

No seu computador Windows, abra o PowerShell e execute:

```powershell
scp atualizar_servidor.sh root@SEU_IP_VPS:/root/
```

**Ou** se você já está conectado via SSH no servidor:

```bash
# Criar o arquivo no servidor
nano /root/atualizar_servidor.sh

# Cole o conteúdo do script (Ctrl+Shift+V)
# Salve com Ctrl+O, Enter, Ctrl+X
```

### 2. Dar permissão de execução

```bash
chmod +x /root/atualizar_servidor.sh
```

### 3. Executar o script

```bash
sudo /root/atualizar_servidor.sh
```

**Pronto!** O script fará tudo automaticamente:
- ✅ Backup do código atual
- ✅ Parar o serviço
- ✅ Baixar atualizações do GitHub
- ✅ Instalar dependências
- ✅ Ajustar permissões
- ✅ Reiniciar o serviço
- ✅ Verificar status

---

## Método 2: Passo a Passo Manual

Se preferir fazer manualmente, siga estes passos:

### 1. Conectar ao servidor

```bash
ssh root@SEU_IP_VPS
```

### 2. Ir para o diretório do projeto

```bash
cd /var/www/financeiro
```

### 3. Fazer backup (IMPORTANTE!)

```bash
sudo cp -r /var/www/financeiro /var/www/financeiro_backup_$(date +%Y%m%d)
```

### 4. Parar o serviço

```bash
sudo systemctl stop financeiro
```

### 5. Baixar atualizações do GitHub

```bash
sudo -u www-data git pull origin main
```

**Saída esperada:**
```
remote: Enumerating objects: 10, done.
remote: Counting objects: 100% (10/10), done.
Updating 76b9956..dbf2602
Fast-forward
 CHANGELOG_SYNC_BIDIRECIONAL.md      | 456 +++++++++
 GUIA_SYNC_BIDIRECIONAL.md           | 342 +++++++
 QUICK_REFERENCE_SYNC.md             |  89 ++
 routes/configuracao.py              | 201 ++++++
 templates/config/importar_dados.html| 311 +++----
 6 files changed, 1399 insertions(+), 51 deletions(-)
```

### 6. Verificar arquivos atualizados

```bash
git log -1 --stat
```

### 7. Ajustar permissões

```bash
sudo chown -R www-data:www-data /var/www/financeiro
```

### 8. Reiniciar o serviço

```bash
sudo systemctl start financeiro
```

### 9. Verificar se está rodando

```bash
sudo systemctl status financeiro
```

**Status esperado:**
```
● financeiro.service - Sistema Financeiro Flask
     Loaded: loaded (/etc/systemd/system/financeiro.service; enabled)
     Active: active (running) since ...
```

### 10. Verificar logs

```bash
sudo journalctl -u financeiro -f
```

Pressione `Ctrl+C` para sair.

---

## ✅ Verificação Pós-Atualização

### 1. Testar acesso ao site

Abra no navegador:
```
https://finan.receberbemevinhos.com.br
```

### 2. Testar nova funcionalidade

Acesse:
```
https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos
```

Você deve ver:
- ✅ Seção "📤 Fazer Upload do Banco de Despesas" (vermelho)
- ✅ Seção "📤 Fazer Upload do Banco de Receitas" (verde)
- ✅ Seção "📥 Baixar Bancos para Desktop" (azul)

### 3. Testar upload

1. Faça login como admin
2. Tente fazer upload de um arquivo .db pequeno
3. Verifique se aparece mensagem de sucesso

### 4. Testar download

1. Clique em "Baixar financas.db"
2. Deve fazer download de um arquivo SQLite
3. Verifique que o arquivo não está vazio

---

## 🆘 Troubleshooting

### Erro: "Permission denied" ao fazer git pull

**Solução:**
```bash
sudo chown -R www-data:www-data /var/www/financeiro
sudo -u www-data git pull origin main
```

### Erro: Serviço não inicia

**Ver logs completos:**
```bash
sudo journalctl -u financeiro -n 50 --no-pager
```

**Causas comuns:**
- Erro de sintaxe Python: Veja o log
- Porta ocupada: Reinicie o servidor
- Permissões: Execute `sudo chown -R www-data:www-data /var/www/financeiro`

### Erro: "ModuleNotFoundError"

**Instalar dependências:**
```bash
sudo -u www-data /var/www/financeiro/venv/bin/pip install -r requirements.txt
sudo systemctl restart financeiro
```

### Página não carrega mudanças

**Limpar cache do navegador:**
- Chrome: Ctrl+Shift+R
- Firefox: Ctrl+F5

**Verificar se realmente atualizou:**
```bash
cd /var/www/financeiro
git log -1 --oneline
```

Deve mostrar: `dbf2602 Implementa sincronização bidirecional completa`

### Reverter atualização (se necessário)

**Se algo der errado:**
```bash
# Parar serviço
sudo systemctl stop financeiro

# Restaurar backup
sudo rm -rf /var/www/financeiro
sudo cp -r /var/www/financeiro_backup_XXXXXXXX /var/www/financeiro

# Reiniciar
sudo systemctl start financeiro
```

---

## 📊 Comandos Úteis

### Ver versão atual
```bash
cd /var/www/financeiro
git log -1 --oneline
```

### Ver diferenças antes de atualizar
```bash
git fetch origin
git diff HEAD origin/main
```

### Ver arquivos que serão atualizados
```bash
git fetch origin
git diff --stat HEAD origin/main
```

### Forçar atualização (CUIDADO!)
```bash
sudo -u www-data git fetch --all
sudo -u www-data git reset --hard origin/main
```

### Ver todos os backups
```bash
ls -la /var/www/ | grep financeiro_backup
```

---

## 📞 Suporte

Se tiver problemas:

1. ✅ Verifique os logs: `sudo journalctl -u financeiro -n 50`
2. ✅ Verifique permissões: `ls -la /var/www/financeiro`
3. ✅ Verifique se atualizou: `git log -1`
4. ✅ Restaure backup se necessário

---

**Última atualização:** Dezembro 2025
**Commit:** dbf2602
**Funcionalidade:** Sincronização Bidirecional Completa

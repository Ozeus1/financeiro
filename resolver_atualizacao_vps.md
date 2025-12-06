# 🔧 Resolver Atualização do VPS

## Situação Atual
Você fez alterações no servidor que não estão no GitHub, e agora precisa atualizar com as novas funcionalidades.

## Solução Passo a Passo

### 1️⃣ Primeiro, resolver o erro de permissão

```bash
cd /var/www/financeiro
sudo git config --global --add safe.directory /var/www/financeiro
```

### 2️⃣ Ver quais arquivos você modificou no servidor

```bash
sudo git status
```

Isso mostrará quais arquivos foram alterados.

### 3️⃣ Salvar suas alterações locais (IMPORTANTE!)

```bash
# Fazer backup das suas alterações
sudo git stash save "Alterações locais antes de atualizar - $(date +%Y%m%d_%H%M%S)"
```

Isso guarda suas alterações temporariamente de forma segura.

### 4️⃣ Baixar as atualizações do GitHub

```bash
sudo git pull origin main
```

### 5️⃣ OPÇÃO A - Aplicar suas alterações por cima (RECOMENDADO)

```bash
# Aplicar suas alterações que foram guardadas
sudo git stash pop
```

Se houver **conflitos**, o Git mostrará quais arquivos têm conflito.

### 6️⃣ OPÇÃO B - Ver suas alterações antes de aplicar

```bash
# Ver o que você tinha alterado
sudo git stash show -p

# Se quiser manter, aplicar
sudo git stash pop

# Se não quiser, descartar
sudo git stash drop
```

### 7️⃣ Resolver conflitos (se houver)

Se aparecer mensagem de conflito, edite os arquivos:

```bash
# Ver quais arquivos têm conflito
sudo git status

# Editar o arquivo
sudo nano routes/configuracao.py  # ou outro arquivo

# Procure por marcas de conflito:
# <<<<<<< HEAD
# código do GitHub
# =======
# suas alterações
# >>>>>>>

# Mantenha o que você quer e delete as marcas
```

Depois:
```bash
sudo git add .
sudo git commit -m "Mescla alterações locais com atualizações do GitHub"
```

### 8️⃣ Ajustar permissões

```bash
sudo chown -R www-data:www-data /var/www/financeiro
```

### 9️⃣ Reiniciar o serviço

```bash
sudo systemctl restart financeiro
sudo systemctl status financeiro
```

---

## 🎯 Comando Completo (Copiar e Colar)

```bash
# Execute tudo de uma vez
cd /var/www/financeiro && \
sudo git config --global --add safe.directory /var/www/financeiro && \
echo "=== Verificando alterações locais ===" && \
sudo git status && \
echo "" && \
echo "=== Salvando alterações locais ===" && \
sudo git stash save "Backup antes de atualizar - $(date +%Y%m%d_%H%M%S)" && \
echo "" && \
echo "=== Baixando atualizações do GitHub ===" && \
sudo git pull origin main && \
echo "" && \
echo "=== Aplicando suas alterações ===" && \
sudo git stash pop && \
echo "" && \
echo "=== Ajustando permissões ===" && \
sudo chown -R www-data:www-data /var/www/financeiro && \
echo "" && \
echo "=== Reiniciando serviço ===" && \
sudo systemctl restart financeiro && \
sleep 2 && \
sudo systemctl status financeiro --no-pager -l
```

---

## 🆘 Se Algo Der Errado

### Voltar ao estado anterior

```bash
# Se deu conflito e você quer desistir
sudo git merge --abort
sudo git stash pop  # recupera suas alterações

# Ou se quiser voltar tudo
sudo git reset --hard HEAD
sudo git stash pop  # recupera suas alterações
```

### Ver suas alterações salvas

```bash
# Listar stashes salvos
sudo git stash list

# Ver conteúdo do stash mais recente
sudo git stash show -p stash@{0}
```

### Recuperar alterações depois

```bash
# Se você quiser aplicar suas alterações depois
sudo git stash list
sudo git stash apply stash@{0}  # ou outro número
```

---

## 📝 Alternativa: Mesclar Manualmente

Se preferir controle total:

### 1. Backup completo do servidor atual

```bash
sudo cp -r /var/www/financeiro /var/www/financeiro_backup_manual_$(date +%Y%m%d)
```

### 2. Ver suas alterações

```bash
cd /var/www/financeiro
sudo git diff routes/configuracao.py  # ou outro arquivo
```

### 3. Copiar suas alterações para outro lugar

```bash
# Copiar arquivos alterados
sudo cp routes/configuracao.py /root/configuracao_minhas_alteracoes.py
sudo cp templates/config/usuarios.html /root/usuarios_minhas_alteracoes.html
# etc...
```

### 4. Atualizar forçado (perde alterações locais)

```bash
sudo git fetch --all
sudo git reset --hard origin/main
```

### 5. Aplicar suas alterações manualmente

Edite os arquivos e adicione suas alterações de volta:
```bash
sudo nano routes/configuracao.py
# Cole suas alterações do backup
```

---

## ✅ Verificação Final

Depois de atualizar:

```bash
# 1. Ver commit atual
git log -1 --oneline
# Deve mostrar: dbf2602 Implementa sincronização bidirecional completa

# 2. Verificar serviço
sudo systemctl status financeiro

# 3. Ver logs
sudo journalctl -u financeiro -n 20 --no-pager

# 4. Testar no navegador
# https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos
```

---

## 💡 Dica para o Futuro

Para evitar isso novamente:

1. **Sempre faça alterações no código LOCAL (Windows)**
2. **Commit e push para GitHub**
3. **Depois atualize o servidor**

Assim você mantém tudo sincronizado! 📌

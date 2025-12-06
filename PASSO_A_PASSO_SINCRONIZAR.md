# 🔄 Passo a Passo: Sincronizar Alterações do Antigravity

## Situação
Você fez alterações no servidor VPS usando o Antigravity (editor web) e quer trazer essas alterações para o código local no Windows.

## ✅ Solução Completa

### PASSO 1: Enviar Alterações do Servidor para o GitHub

**No servidor VPS (SSH):**

```bash
cd /var/www/financeiro

# Configurar repositório
sudo git config --global --add safe.directory /var/www/financeiro

# Ver o que foi alterado
sudo git status

# Adicionar arquivos modificados
sudo git add routes/configuracao.py
sudo git add templates/config/usuarios.html
sudo git add routes/auth.py
sudo git add templates/auth/profile.html

# Fazer commit
sudo git commit -m "Adiciona formulários de cadastro e alteração de senha (via Antigravity)"

# Enviar para GitHub
sudo git push origin main
```

### PASSO 2: Baixar Alterações no Windows

**No seu Windows (Git Bash ou PowerShell):**

```bash
cd C:\Users\orlei\OneDrive\ProjPython\FINAN

# Baixar atualizações do GitHub
git pull origin main
```

### PASSO 3: Agora Fazer as Novas Alterações (Sync Bidirecional)

**No Windows:**

```bash
# Seus arquivos agora têm:
# - Formulários de usuário (do servidor)
# - Sync bidirecional (do commit anterior)

# Ver status
git status

# Fazer commit com tudo junto
git add .
git commit -m "Mescla formulários de usuário + sync bidirecional"
git push origin main
```

### PASSO 4: Atualizar o Servidor com TUDO

**No servidor VPS:**

```bash
cd /var/www/financeiro

# Baixar atualizações
sudo git pull origin main

# Ajustar permissões
sudo chown -R www-data:www-data /var/www/financeiro

# Reiniciar serviço
sudo systemctl restart financeiro
sudo systemctl status financeiro
```

---

## 🎯 Resumo Visual

```
┌─────────────────────────────────────────────────────────┐
│ SITUAÇÃO ATUAL                                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Servidor VPS                     Windows Local         │
│  ✅ Formulários usuário          ✅ Sync bidirecional   │
│  ❌ Sync bidirecional            ❌ Formulários usuário │
│                                                         │
└─────────────────────────────────────────────────────────┘

            ↓ PASSO 1: Servidor → GitHub

┌─────────────────────────────────────────────────────────┐
│  GitHub                                                 │
│  ✅ Formulários usuário                                 │
│  ❌ Sync bidirecional (ainda no commit anterior)        │
└─────────────────────────────────────────────────────────┘

            ↓ PASSO 2: GitHub → Windows

┌─────────────────────────────────────────────────────────┐
│  Windows Local                                          │
│  ✅ Formulários usuário (baixou)                        │
│  ✅ Sync bidirecional (já tinha)                        │
└─────────────────────────────────────────────────────────┘

            ↓ PASSO 3: Windows → GitHub

┌─────────────────────────────────────────────────────────┐
│  GitHub                                                 │
│  ✅ Formulários usuário                                 │
│  ✅ Sync bidirecional                                   │
└─────────────────────────────────────────────────────────┘

            ↓ PASSO 4: GitHub → Servidor

┌─────────────────────────────────────────────────────────┐
│  Servidor VPS                                           │
│  ✅ Formulários usuário                                 │
│  ✅ Sync bidirecional                                   │
│  ✅ TUDO SINCRONIZADO! 🎉                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🚨 Método Alternativo: SCP Direto

Se preferir copiar arquivos diretamente sem Git:

### Do Servidor para o Windows

**No Windows PowerShell:**

```powershell
# Baixar arquivo específico
scp root@SEU_IP_VPS:/var/www/financeiro/routes/configuracao.py C:\Users\orlei\OneDrive\ProjPython\FINAN\routes\configuracao.py

scp root@SEU_IP_VPS:/var/www/financeiro/templates/config/usuarios.html C:\Users\orlei\OneDrive\ProjPython\FINAN\templates\config\usuarios.html
```

Depois:
```bash
git add .
git commit -m "Adiciona formulários de usuário do servidor"
git push
```

---

## 📋 Checklist

Marque conforme for fazendo:

### No Servidor VPS:
- [ ] `cd /var/www/financeiro`
- [ ] `sudo git config --global --add safe.directory /var/www/financeiro`
- [ ] `sudo git status` (ver arquivos modificados)
- [ ] `sudo git add routes/configuracao.py templates/config/usuarios.html routes/auth.py`
- [ ] `sudo git commit -m "Adiciona formulários de usuário"`
- [ ] `sudo git push origin main`

### No Windows:
- [ ] `cd C:\Users\orlei\OneDrive\ProjPython\FINAN`
- [ ] `git pull origin main`
- [ ] `git status` (verificar se baixou)
- [ ] `git add .` (se tiver outras alterações)
- [ ] `git commit -m "Mescla todas as funcionalidades"`
- [ ] `git push origin main`

### No Servidor VPS (atualizar):
- [ ] `cd /var/www/financeiro`
- [ ] `sudo git pull origin main`
- [ ] `sudo chown -R www-data:www-data /var/www/financeiro`
- [ ] `sudo systemctl restart financeiro`
- [ ] `sudo systemctl status financeiro`

---

## 🎓 Para Evitar Isso no Futuro

### Regra de Ouro:

```
1. SEMPRE edite código no WINDOWS (local)
2. Commit e push para GitHub
3. Atualize o servidor com git pull

NUNCA edite direto no servidor (exceto emergências)
```

### Se precisar editar no servidor:

```
1. Edite via Antigravity
2. IMEDIATAMENTE faça commit e push
3. Pull no Windows
4. Continue trabalhando no Windows
```

---

## 🆘 Troubleshooting

### Erro: "Permission denied" no git push

**Solução:**
```bash
# Configurar Git no servidor
sudo git config --global user.email "seu@email.com"
sudo git config --global user.name "Seu Nome"

# Ou usar HTTPS com token
sudo git remote set-url origin https://SEU_TOKEN@github.com/Ozeus1/financeiro.git
```

### Erro: Conflitos ao fazer pull

**Solução:**
```bash
# Ver conflitos
git status

# Resolver manualmente ou aceitar versão do servidor
git checkout --theirs routes/configuracao.py
git add routes/configuracao.py
git commit -m "Resolve conflitos"
```

### Não lembra quais arquivos alterou no servidor

**Solução:**
```bash
cd /var/www/financeiro
sudo git status
sudo git diff --name-only
```

---

## ✅ Verificação Final

Depois de sincronizar tudo:

```bash
# No Servidor
cd /var/www/financeiro
git log -1 --oneline

# No Windows
cd C:\Users\orlei\OneDrive\ProjPython\FINAN
git log -1 --oneline
```

**Ambos devem mostrar o mesmo commit!** ✅

---

## 📞 Resumo dos Comandos

**Servidor → GitHub:**
```bash
sudo git add . && sudo git commit -m "Mensagem" && sudo git push
```

**GitHub → Windows:**
```bash
git pull origin main
```

**Windows → GitHub:**
```bash
git add . && git commit -m "Mensagem" && git push
```

**GitHub → Servidor:**
```bash
sudo git pull && sudo systemctl restart financeiro
```

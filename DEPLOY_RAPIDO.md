# 🚀 Deploy Rápido - VPS Produção

## ✅ Commit Criado e Push Concluído
- Commit: `ba87338`
- Mensagem: "Implementar isolamento completo de dados por usuário"

---

## 📋 COMANDOS PARA EXECUTAR NA VPS

### 1️⃣ Conectar e Fazer Backup (5 min)

```bash
# Conectar via SSH
ssh usuario@finan.receberbemevinhos.com.br

# Backup do banco (OBRIGATÓRIO!)
sudo -u postgres pg_dump financeiro > ~/backup_financeiro_$(date +%Y%m%d_%H%M%S).sql

# Verificar backup criado
ls -lh ~/backup_financeiro_*.sql

# Backup da aplicação
cd /var/www
sudo tar -czf ~/backup_financeiro_app_$(date +%Y%m%d_%H%M%S).tar.gz financeiro/
```

---

### 2️⃣ Atualizar Código (2 min)

```bash
# Pull das mudanças
cd /var/www/financeiro
sudo -u www-data git pull origin main

# Verificar mudanças aplicadas
git log -1
```

---

### 3️⃣ Migrar Banco de Dados (5 min)

```bash
# Executar script de migração
cd /var/www/financeiro
sudo -u www-data python3 migrate_add_user_id.py
```

**⚠️ Quando solicitado:**
- Digite: `SIM` (em maiúsculas)
- Aguarde conclusão (~30 segundos)

**✅ Saída esperada:**
```
✅ Colunas user_id adicionadas
✅ Dados migrados
✅ Colunas user_id agora são obrigatórias
✅ Constraints antigos removidos
✅ Novos constraints adicionados
✅ Índices criados
✅ Migração concluída com sucesso!
```

---

### 4️⃣ Reiniciar Aplicação (1 min)

```bash
# Reiniciar serviço
sudo systemctl restart financeiro

# Aguardar 5 segundos
sleep 5

# Verificar status (deve estar "active (running)")
sudo systemctl status financeiro

# Verificar logs (não deve ter erros)
sudo journalctl -u financeiro -n 30 --no-pager
```

---

### 5️⃣ Testar Sistema (5 min)

#### No Navegador:
1. Acessar: `https://finan.receberbemevinhos.com.br`
2. Login como admin
3. ✅ Dashboard deve carregar normalmente

#### Criar Usuário de Teste:
1. Menu: Configuração → Gerenciar Usuários
2. Criar usuário: `teste`
3. Email: `teste@example.com`
4. Nível: `usuario`
5. Senha: `Teste@123`

#### Verificar Dados Padrão:
1. Logout do admin
2. Login como `teste`
3. Menu: Despesas → Nova Despesa
4. ✅ Categorias devem estar preenchidas
5. ✅ Meios de pagamento devem estar preenchidos

#### Verificar Isolamento:
1. Como `teste`, criar uma despesa qualquer
2. Logout
3. Login como admin
4. Listar despesas
5. ✅ Despesa do usuário `teste` NÃO deve aparecer

---

## 🔴 SE ALGO DER ERRADO - ROLLBACK

### Reverter Código:
```bash
cd /var/www/financeiro
sudo -u www-data git reset --hard d6e4322
sudo systemctl restart financeiro
```

### Restaurar Banco:
```bash
sudo systemctl stop financeiro
sudo -u postgres psql financeiro < ~/backup_financeiro_TIMESTAMP.sql
sudo systemctl start financeiro
```

---

## ✅ CHECKLIST RÁPIDO

- [ ] Backup do banco criado ✅
- [ ] Pull executado ✅
- [ ] Migração executada com sucesso ✅
- [ ] Aplicação reiniciada sem erros ✅
- [ ] Login admin funciona ✅
- [ ] Novo usuário criado ✅
- [ ] Dados padrão verificados ✅
- [ ] Isolamento verificado ✅

---

## 📞 TROUBLESHOOTING RÁPIDO

### Erro: "column user_id already exists"
**Solução:** Migração já foi executada. Pular para passo 4.

### Aplicação não inicia
**Verificar:** `sudo journalctl -u financeiro -n 50`
**Solução:** Se erro de sintaxe, reverter código.

### Usuário não vê categorias
**Executar:**
```bash
sudo -u www-data python3 << 'EOF'
from app import create_app
from models import db, User, criar_dados_padrao_usuario
app = create_app('production')
with app.app_context():
    user = User.query.filter_by(username='teste').first()
    if user:
        criar_dados_padrao_usuario(user)
EOF
```

---

## 📚 Documentação Completa

Para detalhes: `DEPLOY_VPS_ISOLAMENTO.md`

---

**Tempo Total Estimado:** 15-20 minutos
**Downtime:** ~2-5 minutos (durante reinicialização)

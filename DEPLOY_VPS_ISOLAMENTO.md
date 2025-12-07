# 🚀 Procedimento de Deploy: Isolamento de Usuários na VPS

## ⚠️ ATENÇÃO: Sistema em Produção

Este guia detalha o procedimento seguro para atualizar o sistema financeiro na VPS com as mudanças de isolamento de dados por usuário.

---

## 📋 PRÉ-REQUISITOS

- [x] Acesso SSH à VPS
- [x] Credenciais do PostgreSQL
- [x] Backup recente do banco de dados
- [x] Janela de manutenção agendada (recomendado)

---

## 🔴 FASE 1: BACKUP COMPLETO (OBRIGATÓRIO)

### 1.1 Conectar à VPS
```bash
ssh usuario@finan.receberbemevinhos.com.br
```

### 1.2 Backup do Banco de Dados PostgreSQL
```bash
# Backup completo com timestamp
sudo -u postgres pg_dump financeiro > ~/backup_financeiro_$(date +%Y%m%d_%H%M%S).sql

# Verificar tamanho do backup
ls -lh ~/backup_financeiro_*.sql

# Copiar backup para local seguro (opcional, mas recomendado)
scp usuario@finan.receberbemevinhos.com.br:~/backup_financeiro_*.sql ~/backups/
```

### 1.3 Backup dos Arquivos da Aplicação
```bash
# Criar backup da pasta atual
cd /var/www
sudo tar -czf ~/backup_financeiro_app_$(date +%Y%m%d_%H%M%S).tar.gz financeiro/

# Verificar backup criado
ls -lh ~/backup_financeiro_app_*.tar.gz
```

### 1.4 Verificar Status Atual
```bash
cd /var/www/financeiro
git status
git log -3 --oneline
sudo systemctl status financeiro
```

---

## 🟡 FASE 2: ATUALIZAÇÃO DO CÓDIGO

### 2.1 Commit Local das Mudanças (em sua máquina Windows)

```bash
cd C:\Users\orlei\OneDrive\ProjPython\FINAN

# Adicionar arquivos modificados
git add models.py
git add routes/auth.py
git add routes/despesas.py
git add routes/receitas.py
git add routes/relatorios.py
git add gerenciador_sync_bancos.py

# Adicionar novos arquivos
git add MIGRATION_GUIDE.md
git add ISOLAMENTO_USUARIOS_README.md
git add migrate_add_user_id.py

# NÃO adicionar arquivos temporários
# git add ATUALIZAR_FLUXO_CAIXA.md
# git add ATUALIZAR_VPS_AGORA.md
# git add .claude/settings.local.json

# Criar commit
git commit -m "$(cat <<'EOF'
Implementar isolamento completo de dados por usuário

BREAKING CHANGE: Adiciona user_id em categorias e meios de pagamento

Mudanças:
- models.py: user_id em CategoriaDespesa, CategoriaReceita,
  MeioPagamento, MeioRecebimento
- Função criar_dados_padrao_usuario() para novos usuários
- Corrige vulnerabilidades de vazamento de dados em exportações
- Corrige queries de relatórios sem filtro de usuário
- Adiciona user_id em backup/restore do gerenciador_sync_bancos

Vulnerabilidades corrigidas:
- routes/despesas.py:185 - Gerentes viam despesas de todos
- routes/receitas.py:184 - Gerentes viam receitas de todos
- routes/relatorios.py:713 - Relatório sem filtro user_id
- routes/relatorios.py:758 - Relatório mensal sem filtro user_id

Arquivos criados:
- migrate_add_user_id.py: Script de migração do banco
- MIGRATION_GUIDE.md: Guia técnico completo
- ISOLAMENTO_USUARIOS_README.md: Instruções de uso

PENDENTE: Atualizar routes/configuracao.py com filtros user_id

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# Push para GitHub
git push origin main
```

### 2.2 Pull na VPS

```bash
# Na VPS
cd /var/www/financeiro

# Verificar branch atual
git branch

# Pull das mudanças
sudo -u www-data git pull origin main

# Verificar mudanças aplicadas
git log -1
```

---

## 🔵 FASE 3: MIGRAÇÃO DO BANCO DE DADOS

### 3.1 Verificar Conexão com o Banco

```bash
cd /var/www/financeiro

# Verificar .env
sudo cat .env | grep DATABASE_URL

# Testar conexão
sudo -u www-data python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()
print("DATABASE_URL:", os.environ.get('DATABASE_URL')[:50] + "...")
EOF
```

### 3.2 Executar Script de Migração

```bash
cd /var/www/financeiro

# Executar script de migração
sudo -u www-data python3 migrate_add_user_id.py
```

**⚠️ O script irá:**
1. Solicitar confirmação (digite 'SIM')
2. Adicionar user_id nas 4 tabelas
3. Migrar dados existentes para admin (user_id=1)
4. Atualizar constraints
5. Criar índices

**Saída esperada:**
```
✅ Colunas user_id adicionadas
✅ Dados migrados
✅ Colunas user_id agora são obrigatórias
✅ Constraints antigos removidos
✅ Novos constraints adicionados
✅ Índices criados
✅ Migração concluída com sucesso!
```

### 3.3 Verificar Migração

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql financeiro

-- Verificar estrutura das tabelas
\d categorias_despesa
\d categorias_receita
\d meios_pagamento
\d meios_recebimento

-- Verificar dados migrados (todos devem ter user_id=1)
SELECT COUNT(*), user_id FROM categorias_despesa GROUP BY user_id;
SELECT COUNT(*), user_id FROM categorias_receita GROUP BY user_id;
SELECT COUNT(*), user_id FROM meios_pagamento GROUP BY user_id;
SELECT COUNT(*), user_id FROM meios_recebimento GROUP BY user_id;

-- Sair
\q
```

---

## 🟢 FASE 4: REINICIAR APLICAÇÃO

### 4.1 Reiniciar Serviço Flask

```bash
# Reiniciar aplicação
sudo systemctl restart financeiro

# Aguardar 5 segundos
sleep 5

# Verificar status
sudo systemctl status financeiro

# Verificar logs
sudo journalctl -u financeiro -n 50 --no-pager

# Verificar se está respondendo
curl -I http://localhost:5000
```

### 4.2 Verificar Nginx

```bash
# Status do Nginx
sudo systemctl status nginx

# Se necessário, recarregar configuração
sudo nginx -t
sudo systemctl reload nginx
```

---

## ✅ FASE 5: TESTES DE VALIDAÇÃO

### 5.1 Teste de Login
```bash
# Acessar via navegador
https://finan.receberbemevinhos.com.br

# Fazer login como admin
# Verificar se dashboard carrega normalmente
```

### 5.2 Criar Novo Usuário de Teste
1. Como admin, acessar: Configuração → Gerenciar Usuários
2. Criar usuário: `teste_isolamento`
3. Email: `teste@example.com`
4. Nível: `usuario`
5. Senha: `Teste@123`

### 5.3 Verificar Dados Padrão Criados
1. Fazer logout do admin
2. Login como `teste_isolamento`
3. Acessar: Despesas → Nova Despesa
4. **Verificar**: Dropdown de categorias está preenchido
5. **Verificar**: Dropdown de meios de pagamento está preenchido
6. **Verificar**: Não há despesas antigas do admin

### 5.4 Teste de Isolamento
1. Como `teste_isolamento`, criar uma despesa de teste
2. Fazer logout
3. Login como admin
4. **Verificar**: Despesa do teste_isolamento NÃO aparece
5. **Verificar**: Exportação do admin não contém dados do teste

### 5.5 Teste de Relatórios
1. Como admin, acessar Relatórios
2. Executar "Despesas entre Datas"
3. **Verificar**: Apenas despesas do admin aparecem
4. Repetir como `teste_isolamento`
5. **Verificar**: Nenhuma despesa aparece (usuário novo)

---

## 🔧 TROUBLESHOOTING

### Problema 1: Erro ao executar migrate_add_user_id.py

**Erro:** `sqlalchemy.exc.ProgrammingError: column "user_id" already exists`

**Solução:**
```bash
# Verificar se migração já foi executada
sudo -u postgres psql financeiro -c "\d categorias_despesa" | grep user_id

# Se user_id já existe, pular migração
# Continuar para Fase 4
```

### Problema 2: Aplicação não inicia após reiniciar

**Verificar logs:**
```bash
sudo journalctl -u financeiro -n 100 --no-pager
```

**Possíveis causas:**
- Erro de sintaxe Python
- Erro de importação em models.py
- Problema de permissões

**Solução:**
```bash
# Verificar sintaxe
sudo -u www-data python3 -m py_compile models.py

# Testar importação
sudo -u www-data python3 -c "from models import criar_dados_padrao_usuario; print('OK')"

# Se erro, reverter (ver FASE 6)
```

### Problema 3: Usuário não vê categorias

**Causa:** Dados padrão não foram criados

**Solução:**
```bash
# Executar manualmente no Python
sudo -u www-data python3 << 'EOF'
from app import create_app
from models import db, User, criar_dados_padrao_usuario

app = create_app('production')
with app.app_context():
    user = User.query.filter_by(username='teste_isolamento').first()
    if user:
        criar_dados_padrao_usuario(user)
        print(f"Dados padrão criados para {user.username}")
    else:
        print("Usuário não encontrado")
EOF
```

### Problema 4: Erro de constraint UNIQUE

**Erro:** `duplicate key value violates constraint`

**Causa:** Constraint antigo não foi removido

**Solução:**
```sql
-- Conectar ao PostgreSQL
sudo -u postgres psql financeiro

-- Verificar constraints
SELECT conname FROM pg_constraint WHERE conrelid = 'categorias_despesa'::regclass;

-- Remover constraint antigo se existir
ALTER TABLE categorias_despesa DROP CONSTRAINT IF EXISTS categorias_despesa_nome_key;
ALTER TABLE categorias_receita DROP CONSTRAINT IF EXISTS categorias_receita_nome_key;
ALTER TABLE meios_pagamento DROP CONSTRAINT IF EXISTS meios_pagamento_nome_key;
ALTER TABLE meios_recebimento DROP CONSTRAINT IF EXISTS meios_recebimento_nome_key;

-- Sair
\q

-- Reiniciar aplicação
sudo systemctl restart financeiro
```

---

## 🔙 FASE 6: ROLLBACK (Se necessário)

### 6.1 Reverter Código

```bash
cd /var/www/financeiro

# Verificar hash do commit anterior
git log --oneline -5

# Reverter para commit anterior (substituir HASH)
sudo -u www-data git reset --hard HASH_DO_COMMIT_ANTERIOR

# Reiniciar aplicação
sudo systemctl restart financeiro
```

### 6.2 Reverter Banco de Dados

```bash
# Parar aplicação
sudo systemctl stop financeiro

# Restaurar backup
sudo -u postgres psql financeiro < ~/backup_financeiro_TIMESTAMP.sql

# Reiniciar aplicação
sudo systemctl start financeiro

# Verificar status
sudo systemctl status financeiro
```

---

## 📊 CHECKLIST FINAL

### Antes do Deploy:
- [ ] Backup do banco criado e verificado
- [ ] Backup da aplicação criado
- [ ] Commit local criado
- [ ] Push para GitHub concluído
- [ ] Janela de manutenção comunicada (se aplicável)

### Durante o Deploy:
- [ ] Pull executado na VPS
- [ ] Script de migração executado com sucesso
- [ ] Migração verificada no PostgreSQL
- [ ] Aplicação reiniciada sem erros
- [ ] Logs verificados (sem erros)

### Após o Deploy:
- [ ] Login como admin funciona
- [ ] Novo usuário criado e testado
- [ ] Dados padrão criados automaticamente
- [ ] Isolamento verificado (usuários não veem dados uns dos outros)
- [ ] Relatórios filtrados corretamente
- [ ] Exportações isoladas por usuário
- [ ] Usuário de teste removido (opcional)

---

## 📝 NOTAS IMPORTANTES

### Dados Migrados
- ✅ Todas as categorias/meios existentes foram atribuídos ao admin (user_id=1)
- ✅ Admin continua vendo todos os seus dados normalmente
- ✅ Novos usuários recebem cópias próprias das categorias/meios padrão

### Comportamento Após Deploy
- ❌ Gerentes NÃO veem mais dados de outros usuários
- ✅ Cada usuário vê APENAS seus próprios dados
- ✅ Novos usuários começam com categorias/meios padrão

### Pendências
- ⚠️ `routes/configuracao.py` ainda precisa ser atualizado
- ⚠️ Queries de formulários em despesas/receitas podem precisar ajustes
- ⚠️ Algumas queries em relatorios.py podem precisar filtros adicionais

---

## 🆘 SUPORTE

Em caso de problemas críticos:

1. **Reverter imediatamente** (FASE 6)
2. **Verificar logs**: `sudo journalctl -u financeiro -n 200`
3. **Verificar erro específico** no PostgreSQL: `sudo -u postgres tail -100 /var/log/postgresql/postgresql-*-main.log`
4. **Contatar suporte** com logs coletados

---

## ✅ DEPLOY CONCLUÍDO

Após validação completa:
- [ ] Remover usuário de teste
- [ ] Documentar quaisquer issues encontrados
- [ ] Atualizar documentação interna
- [ ] Comunicar usuários sobre nova funcionalidade

---

**Versão:** 1.0
**Data:** Dezembro 2025
**Tempo Estimado:** 15-30 minutos
**Downtime:** ~2-5 minutos (durante reinicialização)

# Guia de Migração: Isolamento de Dados por Usuário

## 📋 Resumo das Mudanças

Este guia documenta as alterações para isolar completamente os dados entre usuários no sistema financeiro Flask.

### Mudanças Principais:
1. ✅ **Models.py**: Adicionado `user_id` em todas as tabelas compartilhadas
2. ✅ **Dados Padrão**: Criada função para popular categorias/meios para novos usuários
3. ✅ **Auth.py**: Atualizado registro para criar dados padrão
4. ✅ **Queries Críticas**: Corrigidas vulnerabilidades de vazamento de dados
5. ⚠️ **Migração de Banco**: Script necessário para migrar dados existentes

---

## 1. Alterações no models.py

### Tabelas Modificadas:

#### CategoriaDespesa
**ANTES:**
```python
nome = db.Column(db.String(100), unique=True, nullable=False)
# Sem user_id
```

**DEPOIS:**
```python
nome = db.Column(db.String(100), nullable=False)
user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
__table_args__ = (db.UniqueConstraint('nome', 'user_id', name='_categoria_despesa_usuario_uc'),)
```

#### CategoriaReceita
**ANTES:**
```python
nome = db.Column(db.String(100), unique=True, nullable=False)
# Sem user_id
```

**DEPOIS:**
```python
nome = db.Column(db.String(100), nullable=False)
user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
__table_args__ = (db.UniqueConstraint('nome', 'user_id', name='_categoria_receita_usuario_uc'),)
```

#### MeioPagamento
**ANTES:**
```python
nome = db.Column(db.String(100), unique=True, nullable=False)
# Sem user_id
```

**DEPOIS:**
```python
nome = db.Column(db.String(100), nullable=False)
user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
__table_args__ = (db.UniqueConstraint('nome', 'user_id', name='_meio_pagamento_usuario_uc'),)
```

#### MeioRecebimento
**ANTES:**
```python
nome = db.Column(db.String(100), unique=True, nullable=False)
# Sem user_id
```

**DEPOIS:**
```python
nome = db.Column(db.String(100), nullable=False)
user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
__table_args__ = (db.UniqueConstraint('nome', 'user_id', name='_meio_recebimento_usuario_uc'),)
```

---

## 2. Função de Dados Padrão

Nova função criada em `models.py`:

```python
def criar_dados_padrao_usuario(user):
    """Cria categorias e meios de pagamento padrão para um novo usuário"""
    # Cria 12 categorias de despesa
    # Cria 5 categorias de receita
    # Cria 6 meios de pagamento
    # Cria 4 meios de recebimento
```

Esta função é chamada automaticamente ao criar novo usuário em `routes/auth.py`.

---

## 3. Queries Corrigidas

### ❌ VULNERABILIDADES CRÍTICAS CORRIGIDAS:

#### routes/despesas.py - linha 185
**ANTES:**
```python
if current_user.is_gerente():
    despesas = Despesa.query.all()  # VAZAMENTO: Gerentes viam tudo
else:
    despesas = Despesa.query.filter_by(user_id=current_user.id).all()
```

**DEPOIS:**
```python
# Todos os usuários veem apenas seus dados
despesas = Despesa.query.filter_by(user_id=current_user.id).all()
```

#### routes/receitas.py - linha 184
**ANTES:**
```python
if current_user.is_gerente():
    receitas = Receita.query.all()  # VAZAMENTO: Gerentes viam tudo
else:
    receitas = Receita.query.filter_by(user_id=current_user.id).all()
```

**DEPOIS:**
```python
# Todos os usuários veem apenas seus dados
receitas = Receita.query.filter_by(user_id=current_user.id).all()
```

#### routes/relatorios.py - linha 713
**ANTES:**
```python
).filter(
    Despesa.data_pagamento.between(data_inicio, data_fim)
)  # FALTAVA: Despesa.user_id == current_user.id
```

**DEPOIS:**
```python
).filter(
    Despesa.data_pagamento.between(data_inicio, data_fim),
    Despesa.user_id == current_user.id  # ADICIONADO
)
```

#### routes/relatorios.py - linha 758
**ANTES:**
```python
).filter(
    Despesa.data_pagamento.between(data_inicio, data_fim)
)  # FALTAVA: Despesa.user_id == current_user.id
```

**DEPOIS:**
```python
).filter(
    Despesa.data_pagamento.between(data_inicio, data_fim),
    Despesa.user_id == current_user.id  # ADICIONADO
)
```

---

## 4. Queries que PRECISAM ser Atualizadas

### routes/configuracao.py

Todas as queries de categorias e meios de pagamento precisam filtrar por user_id:

**Padrão para todas as queries:**
```python
# ANTES:
CategoriaDespesa.query.all()

# DEPOIS:
CategoriaDespesa.query.filter_by(user_id=current_user.id).all()
```

**Locais específicos:**
- Linha ~173: `categorias_despesa()`
- Linha ~214: `categorias_receita()`
- Linha ~258: `meios_pagamento()`
- Linha ~299: `meios_recebimento()`

**Criar nova categoria:**
```python
# ANTES:
nova_categoria = CategoriaDespesa(nome=nome, ativo=True)

# DEPOIS:
nova_categoria = CategoriaDespesa(nome=nome, ativo=True, user_id=current_user.id)
```

### routes/despesas.py

**Listar categorias em formulários:**
```python
# ANTES:
categorias = CategoriaDespesa.query.filter_by(ativo=True).all()

# DEPOIS:
categorias = CategoriaDespesa.query.filter_by(ativo=True, user_id=current_user.id).all()
```

**Listar meios de pagamento:**
```python
# ANTES:
meios = MeioPagamento.query.filter_by(ativo=True).all()

# DEPOIS:
meios = MeioPagamento.query.filter_by(ativo=True, user_id=current_user.id).all()
```

### routes/receitas.py

Mesmo padrão de despesas.py - filtrar categorias e meios por user_id.

### routes/relatorios.py

**Linha ~579:** `despesas_por_categoria_evolucao()`
```python
# ANTES:
categorias = CategoriaDespesa.query.order_by(CategoriaDespesa.nome).all()

# DEPOIS:
categorias = CategoriaDespesa.query.filter_by(user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
```

**Linha ~645:** `despesas_por_pagamento()`
```python
# ANTES:
meios_pagamento = [m.nome for m in MeioPagamento.query.order_by(MeioPagamento.nome).all()]

# DEPOIS:
meios_pagamento = [m.nome for m in MeioPagamento.query.filter_by(user_id=current_user.id).order_by(MeioPagamento.nome).all()]
```

---

## 5. Migração do Banco de Dados

### ⚠️ IMPORTANTE: Backup Obrigatório

Antes de executar a migração, faça backup do banco:
```bash
pg_dump -U postgres -d nome_do_banco > backup_pre_migration.sql
```

### Script de Migração SQL

Execute o script `migrate_add_user_id.py` (criado separadamente) que:

1. Adiciona coluna `user_id` nas tabelas
2. Migra dados existentes para o usuário admin (id=1)
3. Remove constraint UNIQUE antigo
4. Adiciona novo constraint UNIQUE composto (nome + user_id)
5. Adiciona índices para performance

### Comandos SQL Manuais (se necessário):

```sql
-- 1. Adicionar colunas user_id
ALTER TABLE categorias_despesa ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE categorias_receita ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE meios_pagamento ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE meios_recebimento ADD COLUMN user_id INTEGER REFERENCES users(id);

-- 2. Migrar dados existentes para admin (user_id=1)
UPDATE categorias_despesa SET user_id = 1 WHERE user_id IS NULL;
UPDATE categorias_receita SET user_id = 1 WHERE user_id IS NULL;
UPDATE meios_pagamento SET user_id = 1 WHERE user_id IS NULL;
UPDATE meios_recebimento SET user_id = 1 WHERE user_id IS NULL;

-- 3. Tornar user_id NOT NULL
ALTER TABLE categorias_despesa ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE categorias_receita ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE meios_pagamento ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE meios_recebimento ALTER COLUMN user_id SET NOT NULL;

-- 4. Remover constraints UNIQUE antigos
ALTER TABLE categorias_despesa DROP CONSTRAINT IF EXISTS categorias_despesa_nome_key;
ALTER TABLE categorias_receita DROP CONSTRAINT IF EXISTS categorias_receita_nome_key;
ALTER TABLE meios_pagamento DROP CONSTRAINT IF EXISTS meios_pagamento_nome_key;
ALTER TABLE meios_recebimento DROP CONSTRAINT IF EXISTS meios_recebimento_nome_key;

-- 5. Adicionar novos constraints UNIQUE compostos
ALTER TABLE categorias_despesa ADD CONSTRAINT _categoria_despesa_usuario_uc UNIQUE (nome, user_id);
ALTER TABLE categorias_receita ADD CONSTRAINT _categoria_receita_usuario_uc UNIQUE (nome, user_id);
ALTER TABLE meios_pagamento ADD CONSTRAINT _meio_pagamento_usuario_uc UNIQUE (nome, user_id);
ALTER TABLE meios_recebimento ADD CONSTRAINT _meio_recebimento_usuario_uc UNIQUE (nome, user_id);

-- 6. Criar índices para performance
CREATE INDEX idx_categoria_despesa_user ON categorias_despesa(user_id);
CREATE INDEX idx_categoria_receita_user ON categorias_receita(user_id);
CREATE INDEX idx_meio_pagamento_user ON meios_pagamento(user_id);
CREATE INDEX idx_meio_recebimento_user ON meios_recebimento(user_id);
```

---

## 6. Checklist de Implementação

### Fase 1: Preparação
- [ ] Fazer backup completo do banco de dados
- [ ] Testar em ambiente de desenvolvimento primeiro
- [ ] Revisar todas as mudanças no código

### Fase 2: Migração de Código
- [x] Atualizar models.py
- [x] Criar função criar_dados_padrao_usuario()
- [x] Atualizar routes/auth.py
- [x] Corrigir routes/despesas.py (exportar)
- [x] Corrigir routes/receitas.py (exportar)
- [x] Corrigir routes/relatorios.py (2 queries críticas)
- [ ] Atualizar routes/configuracao.py (todas as queries)
- [ ] Atualizar routes/despesas.py (queries de formulário)
- [ ] Atualizar routes/receitas.py (queries de formulário)
- [ ] Atualizar routes/relatorios.py (queries restantes)

### Fase 3: Migração de Banco
- [ ] Executar script de migração SQL
- [ ] Verificar integridade dos dados
- [ ] Testar queries com múltiplos usuários

### Fase 4: Testes
- [ ] Criar usuário novo e verificar dados padrão
- [ ] Testar isolamento: Usuário A não vê dados de Usuário B
- [ ] Testar relatórios filtrados por usuário
- [ ] Testar exportação de dados
- [ ] Testar gerentes (não devem mais ver dados de outros)

---

## 7. Riscos e Mitigações

### Risco 1: Perda de Dados
**Mitigação**: Backup obrigatório antes da migração

### Risco 2: Queries Quebradas
**Mitigação**: Testar em desenvolvimento, logs detalhados

### Risco 3: Performance
**Mitigação**: Índices criados em user_id para otimização

### Risco 4: Dados Existentes
**Mitigação**: Script migra tudo para admin primeiro, depois duplicar manualmente se necessário

---

## 8. Reversão

Se necessário reverter:

```sql
-- Remover constraints novos
ALTER TABLE categorias_despesa DROP CONSTRAINT _categoria_despesa_usuario_uc;
ALTER TABLE categorias_receita DROP CONSTRAINT _categoria_receita_usuario_uc;
ALTER TABLE meios_pagamento DROP CONSTRAINT _meio_pagamento_usuario_uc;
ALTER TABLE meios_recebimento DROP CONSTRAINT _meio_recebimento_usuario_uc;

-- Remover colunas user_id
ALTER TABLE categorias_despesa DROP COLUMN user_id;
ALTER TABLE categorias_receita DROP COLUMN user_id;
ALTER TABLE meios_pagamento DROP COLUMN user_id;
ALTER TABLE meios_recebimento DROP COLUMN user_id;

-- Restaurar backup
-- psql -U postgres -d nome_do_banco < backup_pre_migration.sql
```

---

## 9. Status Atual

✅ **Concluído:**
- Models.py atualizado
- Função de dados padrão criada
- Auth.py atualizado
- 4 vulnerabilidades críticas corrigidas

⚠️ **Pendente:**
- Atualizar todas as queries em configuracao.py
- Atualizar queries de formulário em despesas/receitas
- Executar migração de banco de dados
- Testes completos

---

**Data**: Dezembro 2025
**Versão**: 1.0
**Autor**: Sistema de Migração Automatizado

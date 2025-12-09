# 🚀 ATUALIZAR VPS AGORA - EXPORTAÇÃO SQLITE CORRIGIDA

## ⚠️ IMPORTANTE - LEIA PRIMEIRO!

O arquivo `financas.db` que você baixou está **INCOMPLETO** e por isso o relatório avançado não funciona.

## ✅ O Que Foi Corrigido (6 commits enviados)

### Commit 7854ab0 - Compatibilidade básica:
- ✅ Renomeada coluna `categoria_receita` → `conta_receita` em receitas
- ✅ Adicionadas tabelas auxiliares (categorias, meios_pagamento, etc.)
- ✅ Corrigido nome do arquivo: `financas_receitas.db` (com "s")

### Commit 98d3ab6 - Fechamento de cartões:
- ✅ Adicionada tabela `fechamento_cartoes` (estava faltando!)
- ✅ Necessária para previsão de pagamentos dos cartões

### Commit c93cbfc - View de compatibilidade:
- ✅ Adicionada coluna `user_id` na tabela despesas
- ✅ **Criada view `v_despesas_compat`** ← SOLUCIONA O SEU ERRO!
- ✅ View é usada pelos relatórios avançados do desktop

### Commit efc3f2c - Correção da query de fechamento:
- ✅ Query alterada para usar filtro IN ao invés de JOIN
- ✅ Melhora performance e garante exportação completa
- ✅ Filtro direto por meio_pagamento_id

### Commit f8cf3f1 - Debug de fechamento_cartoes:
- ✅ Adicionados logs de debug detalhados
- ✅ Monitora IDs, quantidade e dados dos fechamentos
- ✅ Facilita diagnóstico de problemas na exportação

### Commit 38edefb - Coluna data_vencimento (CRÍTICO):
- ✅ **Adicionar coluna `data_vencimento` na tabela fechamento_cartoes** ← CORRIGE ERRO!
- ✅ PostgreSQL tem dia_fechamento E dia_vencimento
- ✅ Exportação estava ignorando dia_vencimento
- ✅ Agora exporta ambas as informações

---

## 🎯 EXECUTE NA VPS AGORA

### Método Rápido (Copie e Cole Tudo):

```bash
cd /var/www/financeiro && \
sudo git config --global --add safe.directory /var/www/financeiro && \
echo "=== Parando serviço ===" && \
sudo systemctl stop financeiro && \
echo "" && \
echo "=== Baixando atualizações do GitHub ===" && \
sudo -u www-data git pull origin main && \
echo "" && \
echo "=== Ajustando permissões ===" && \
sudo chown -R www-data:www-data /var/www/financeiro && \
echo "" && \
echo "=== Reiniciando serviço ===" && \
sudo systemctl start financeiro && \
sleep 3 && \
echo "" && \
echo "=== Status do serviço ===" && \
sudo systemctl status financeiro --no-pager -l | head -n 15 && \
echo "" && \
echo "=== Últimas linhas do log ===" && \
sudo journalctl -u financeiro -n 10 --no-pager && \
echo "" && \
echo "========================================" && \
echo "✅ ATUALIZAÇÃO CONCLUÍDA!" && \
echo "========================================" && \
echo "" && \
echo "🌐 Acesse: https://finan.receberbemevinhos.com.br" && \
echo "" && \
echo "📤 Teste sincronização em:" && \
echo "   /configuracao/importar-dados-antigos" && \
echo "" && \
echo "👥 Teste usuários em:" && \
echo "   /configuracao/usuarios" && \
echo ""
```

---

## 📋 Ou Passo a Passo Manual

Se preferir executar passo a passo:

### 1. Conectar ao servidor
```bash
ssh root@SEU_IP_VPS
```

### 2. Ir para o diretório
```bash
cd /var/www/financeiro
```

### 3. Configurar repositório
```bash
sudo git config --global --add safe.directory /var/www/financeiro
```

### 4. Parar o serviço
```bash
sudo systemctl stop financeiro
```

### 5. Baixar atualizações
```bash
sudo -u www-data git pull origin main
```

**Saída esperada:**
```
remote: Enumerating objects: XX, done.
remote: Counting objects: 100% (XX/XX), done.
Updating XXXXXXX..c93cbfc
Fast-forward
 routes/configuracao.py | 97 +++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 97 insertions(+)
```

**Você deve ver os 6 commits:**
- `7854ab0` Corrigir exportação SQLite para compatibilidade
- `98d3ab6` Adicionar tabela fechamento_cartoes
- `c93cbfc` Adicionar coluna user_id e view v_despesas_compat
- `efc3f2c` Corrigir query de exportação de fechamento_cartoes
- `f8cf3f1` Adicionar debug na exportação de fechamento_cartoes
- `38edefb` Adicionar coluna data_vencimento à exportação

### 6. Ajustar permissões
```bash
sudo chown -R www-data:www-data /var/www/financeiro
```

### 7. Reiniciar serviço
```bash
sudo systemctl start financeiro
```

### 8. Verificar status
```bash
sudo systemctl status financeiro
```

Deve aparecer: **Active: active (running)**

### 9. Ver logs
```bash
sudo journalctl -u financeiro -n 20 --no-pager
```

---

## ✅ VERIFICAÇÃO PÓS-ATUALIZAÇÃO

### 1. Acessar a página de exportação
```
https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos
```

### 2. Baixar NOVAMENTE os 3 arquivos

**IMPORTANTE:** Delete os arquivos antigos primeiro!

1. **Baixar financas.db** (botão vermelho)
2. **Baixar financas_receitas.db** (botão verde)
3. **Baixar fluxo_caixa.db** (botão azul)

### 3. Verificar se a view foi criada

Execute este comando Python no seu computador:

```python
import sqlite3
conn = sqlite3.connect(r'C:\Users\orlei\Downloads\financas.db')
cursor = conn.cursor()
cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name")
print("Estrutura do banco exportado:")
for row in cursor.fetchall():
    print(f'  {row[1].upper()}: {row[0]}')
conn.close()
```

**Saída CORRETA esperada:**
```
Estrutura do banco exportado:
  TABLE: categorias
  TABLE: despesas
  TABLE: fechamento_cartoes          ← DEVE ESTAR PRESENTE!
  TABLE: meios_pagamento
  TABLE: orcamento
  TABLE: sqlite_sequence
  VIEW: v_despesas_compat             ← DEVE ESTAR PRESENTE!
```

### 3.1 Verificar estrutura de fechamento_cartoes:

```python
import sqlite3
conn = sqlite3.connect(r'C:\Users\orlei\Downloads\financas.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(fechamento_cartoes)")
print("Colunas da tabela fechamento_cartoes:")
for col in cursor.fetchall():
    print(f'  {col[1]} ({col[2]})')
cursor.execute("SELECT * FROM fechamento_cartoes")
print("\nDados de fechamento_cartoes:")
for row in cursor.fetchall():
    print(f'  {row}')
conn.close()
```

**Saída CORRETA esperada:**
```
Colunas da tabela fechamento_cartoes:
  id (INTEGER)
  meio_pagamento (TEXT)
  data_fechamento (INTEGER)
  data_vencimento (INTEGER)          ← DEVE ESTAR PRESENTE!

Dados de fechamento_cartoes:
  (1, 'Cartão Nubank', 15, 25)       ← Exemplo com seus dados
  (2, 'Cartão C6', 5, 15)            ← Exemplo com seus dados
```

### 4. Testar o relatório avançado no desktop

1. Abra o sistema desktop
2. Vá em **Despesas → Relatórios Avançados com Gráficos**
3. Selecione qualquer relatório (ex: "Por Categoria")
4. **DEVE FUNCIONAR** sem erro de "v_despesas_compat não encontrada"!

---

## 🆘 Se Algo Der Errado

### Erro: "Permission denied"
```bash
sudo chown -R www-data:www-data /var/www/financeiro
sudo systemctl restart financeiro
```

### Erro: Serviço não inicia
```bash
# Ver logs completos
sudo journalctl -u financeiro -n 50 --no-pager

# Verificar sintaxe Python
cd /var/www/financeiro
sudo -u www-data /var/www/financeiro/venv/bin/python -m py_compile routes/auth.py
sudo -u www-data /var/www/financeiro/venv/bin/python -m py_compile routes/configuracao.py
```

### Erro: Página em branco ou 500
```bash
# Limpar cache do navegador: Ctrl+Shift+R

# Ver logs em tempo real
sudo journalctl -u financeiro -f
```

### Rollback (reverter atualização)
```bash
cd /var/www/financeiro
sudo systemctl stop financeiro
sudo -u www-data git reset --hard dbf2602
sudo systemctl start financeiro
```

---

## 📊 Commits Aplicados Hoje

### 7854ab0 - Correção de compatibilidade básica:
- Renomear coluna categoria_receita → conta_receita
- Adicionar tabelas auxiliares (categorias, meios)
- Corrigir nome do arquivo receitas

### 98d3ab6 - Tabela de fechamento de cartões:
- Criar tabela fechamento_cartoes
- Popular com dados do PostgreSQL
- Necessária para previsões de pagamento

### c93cbfc - View de compatibilidade (CRÍTICO):
- Adicionar coluna user_id na tabela despesas
- **Criar view v_despesas_compat**
- Soluciona erro dos relatórios avançados

### efc3f2c - Correção da query de fechamento:
- Alterar query para usar filtro IN
- Melhorar performance da exportação
- Garantir exportação completa dos dados

### f8cf3f1 - Debug de fechamento_cartoes:
- Adicionar logs detalhados de debug
- Monitorar IDs e quantidade de fechamentos
- Facilitar diagnóstico de problemas

### 38edefb - Coluna data_vencimento (CRÍTICO):
- **Adicionar coluna data_vencimento**
- Corrigir exportação incompleta
- PostgreSQL tinha 2 colunas, SQLite exportava só 1
- Agora exporta dia_fechamento E dia_vencimento

---

## 🎯 RESUMO - O QUE FAZER

1. ✅ **ATUALIZAR VPS** (git pull + restart)
2. ✅ **BAIXAR NOVAMENTE** os 3 arquivos .db
3. ✅ **VERIFICAR** que v_despesas_compat existe
4. ✅ **TESTAR** relatório avançado no desktop
5. ✅ **CONFIRMAR** que funcionou!

---

## ❓ Por Que Deu Erro?

O arquivo que você baixou foi **ANTES** de atualizar a VPS.

**Arquivo antigo (Downloads):**
- ❌ Sem fechamento_cartoes
- ❌ Sem v_despesas_compat
- ❌ Sem user_id

**Arquivo novo (após atualizar VPS):**
- ✅ Com fechamento_cartoes
- ✅ Com v_despesas_compat
- ✅ Com user_id

---

**Data:** 2025-12-08 (atualizado)
**Commits:** 7854ab0, 98d3ab6, c93cbfc, efc3f2c, f8cf3f1, 38edefb
**Correção:** Exportação SQLite completa e compatível
**Soluciona:**
- Erro "v_despesas_compat não foi encontrada"
- Exportação incompleta de fechamento_cartoes (faltava dia_vencimento)

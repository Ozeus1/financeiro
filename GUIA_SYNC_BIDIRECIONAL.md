# 🔄 Guia de Sincronização Bidirecional - Desktop ↔ Servidor

Este guia explica como sincronizar dados entre o sistema Desktop (SQLite) e o sistema Web (PostgreSQL) **nos dois sentidos**, sem precisar abrir portas de banco de dados.

## 🎯 O Que Você Pode Fazer

✅ **Desktop → Servidor (Upload)**
- Enviar despesas do desktop para o servidor
- Enviar receitas do desktop para o servidor
- Atualizar orçamentos no servidor

✅ **Servidor → Desktop (Download)**
- Baixar despesas do servidor para o desktop
- Baixar receitas do servidor para o desktop
- Sincronizar orçamentos

## 📤 Desktop → Servidor (Upload)

### Método 1: Pelo Sistema Desktop (Mais Fácil)

1. **Abra o sistema desktop**

2. **Vá em: Arquivo → Sincronizar Bancos (Flask ↔ Desktop)**

3. **Clique em: 🌐 Upload via Web (Sem Porta)**

4. **O navegador abrirá automaticamente** na página de sincronização

5. **Faça upload dos bancos:**

   **Para Despesas:**
   - Seção: "📤 Fazer Upload do Banco de Despesas"
   - Arquivo: `financas.db` (já será mostrado o caminho correto)
   - Modo: Escolha **Parcial** (recomendado) ou **Total**
   - Clique: "📤 Fazer Upload e Importar Despesas"

   **Para Receitas:**
   - Seção: "📤 Fazer Upload do Banco de Receitas"
   - Arquivo: `financas_receita.db`
   - Modo: Escolha **Parcial** (recomendado) ou **Total**
   - Clique: "📤 Fazer Upload e Importar Receitas"

6. **Aguarde a confirmação**

### Método 2: Direto pelo Navegador

1. **Acesse:** https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos

2. **Faça login** (admin/admin123 ou sua senha)

3. **Selecione os arquivos:**
   - `financas.db` (despesas)
   - `financas_receita.db` (receitas)

4. **Escolha o modo e faça upload**

## 📥 Servidor → Desktop (Download)

### Como Baixar Dados do Servidor

1. **Acesse a página de sincronização:**
   - URL: https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos
   - Ou: Sistema Desktop → Arquivo → Sincronizar Bancos → Upload via Web

2. **Role até a seção "📥 Baixar Bancos para Desktop"**

3. **Baixe os arquivos:**

   **Despesas:**
   - Clique em: "Baixar financas.db"
   - Salve o arquivo `financas.db`

   **Receitas:**
   - Clique em: "Baixar financas_receita.db"
   - Salve o arquivo `financas_receita.db`

4. **Substitua os arquivos no desktop:**
   - Localize a pasta do sistema desktop
   - **FAÇA BACKUP dos arquivos atuais primeiro!**
   - Substitua `financas.db` pelo arquivo baixado
   - Substitua `financas_receita.db` pelo arquivo baixado

5. **Reabra o sistema desktop** para ver os dados atualizados

## 🔀 Modos de Importação

### 🟢 Modo Parcial (Adicionar) - RECOMENDADO

**Quando usar:**
- Sincronização diária/frequente
- Quer mesclar dados de ambos os lados
- Não quer perder dados

**O que faz:**
- ✅ Mantém dados existentes
- ✅ Adiciona novos dados
- ⚠️ Pode criar duplicatas se enviar os mesmos dados

**Exemplo:**
```
Servidor: 100 despesas
Upload:   50 despesas novas
Resultado: 150 despesas
```

### 🔴 Modo Total (Substituir) - CUIDADO!

**Quando usar:**
- Primeira sincronização
- Migração completa
- Resetar dados do servidor

**O que faz:**
- ❌ APAGA todos os dados do servidor
- ✅ Importa todos os dados do arquivo
- ⚠️ PERDA DE DADOS se não fizer backup!

**Exemplo:**
```
Servidor: 100 despesas (APAGADAS!)
Upload:   50 despesas
Resultado: 50 despesas (só do arquivo)
```

## 🎯 Fluxos de Trabalho Recomendados

### Cenário 1: Trabalho Principal no Desktop

```
📍 Rotina Diária:
1. Lançar despesas/receitas no desktop durante o dia
2. Fim do dia: Upload (Modo Parcial) → Servidor
3. Dados ficam disponíveis no site para consulta

📍 Resultado:
- Desktop sempre atualizado (você trabalha nele)
- Servidor sincronizado para consultas online
```

### Cenário 2: Trabalho Dividido (Desktop + Web)

```
📍 Manhã:
1. Download Servidor → Desktop (pegar atualizações da web)
2. Trabalhar no desktop durante o dia
3. Upload Desktop → Servidor (enviar atualizações)

📍 Tarde/Noite:
4. Fazer lançamentos no site (se necessário)
5. Repetir ciclo no dia seguinte

📍 Resultado:
- Dados sempre sincronizados
- Pode trabalhar em qualquer plataforma
```

### Cenário 3: Migração Completa

```
📍 Primeira Vez:
1. BACKUP do servidor (se tiver dados importantes)
2. Upload Desktop → Servidor (Modo TOTAL)
3. Verificar se tudo está correto
4. Usar Modo Parcial daqui em diante

📍 Resultado:
- Servidor tem cópia exata do desktop
- Dados iniciais migrados
```

### Cenário 4: Múltiplos Desktops

```
📍 Se você tem o desktop em vários computadores:
1. Computer A: Upload para servidor
2. Computer B: Download do servidor
3. Computer B: Fazer alterações
4. Computer B: Upload para servidor
5. Computer A: Download do servidor

📍 Resultado:
- Todos os desktops sincronizados via servidor
- Servidor como "fonte central de verdade"
```

## 📋 Dados Sincronizados

### ✅ Despesas (financas.db)

- Descrição
- Valor e número de parcelas
- Data de registro e pagamento
- Categoria (criada automaticamente se não existir)
- Meio de pagamento (criado automaticamente se não existir)
- **Orçamentos** (valores orçados por categoria)

### ✅ Receitas (financas_receita.db)

- Descrição
- Valor e número de parcelas
- Data de registro e recebimento
- Categoria de receita (criada automaticamente se não existir)
- Meio de recebimento (criado automaticamente se não existir)

### ❌ NÃO Sincroniza

- Usuários (cada sistema tem seus próprios usuários)
- Configurações de cartões
- Fluxo de caixa (tem processo separado)

## ⚠️ Boas Práticas e Segurança

### 1. SEMPRE Faça Backup Antes

```bash
# No servidor VPS
sudo -u postgres pg_dump financeiro > backup_antes_sync.sql

# No desktop
# Copie financas.db e financas_receita.db para outra pasta
```

### 2. Use Modo Parcial na Maioria dos Casos

- ✅ Seguro - não apaga dados
- ✅ Reversível - pode deletar duplicatas manualmente
- ❌ Pode criar duplicatas - atenção ao fazer múltiplos uploads

### 3. Use Modo Total Apenas Quando Necessário

- ✅ Primeira sincronização
- ✅ Resetar completamente os dados
- ❌ Sincronização diária (use Parcial!)

### 4. Verifique Após Sincronizar

**Após Upload:**
1. Vá para o Dashboard do site
2. Confira os totais de despesas/receitas
3. Verifique se os lançamentos recentes aparecem

**Após Download:**
1. Abra o sistema desktop
2. Confira os totais
3. Verifique os últimos lançamentos

### 5. Cuidado com Duplicatas

**Como evitar:**
- Não faça upload do mesmo período múltiplas vezes em Modo Parcial
- Use Modo Total se quiser "limpar e recomeçar"
- Mantenha um fluxo consistente (sempre Desktop → Servidor ou sempre Servidor → Desktop)

**Se criar duplicatas:**
- Delete manualmente no site ou desktop
- Ou: Use Modo Total para resetar e reimportar

## 🆘 Troubleshooting

### Erro: "Tipo de arquivo não permitido"

**Solução:**
- Use apenas arquivos .db, .sqlite ou .sqlite3
- Verifique se não corrompeu o arquivo ao transferir

### Erro: "Tabela não encontrada"

**Solução:**
- Despesas: Use `financas.db` (não `financas_receita.db`)
- Receitas: Use `financas_receita.db` (não `financas.db`)
- Verifique se o arquivo é do sistema correto

### Upload Muito Lento

**Causas:**
- Banco de dados muito grande (>50 MB)
- Conexão lenta

**Soluções:**
- Aguarde mais tempo (pode levar 1-2 minutos)
- Use conexão WiFi/cabo mais rápida
- Compacte dados antigos se possível

### Download Não Abre no Desktop

**Solução:**
1. Verifique se baixou o arquivo completo (não cortou)
2. Renomeie para o nome correto (`financas.db` ou `financas_receita.db`)
3. Coloque na pasta correta do sistema desktop
4. Verifique permissões do arquivo

### Dados Não Aparecem Após Download

**Solução:**
1. Feche completamente o sistema desktop
2. Verifique se substituiu os arquivos corretos
3. Reabra o sistema desktop
4. Se usar o sincronizador, clique em "Atualizar" ou "Recarregar"

## 🔐 Segurança

### Por Que É Seguro?

✅ **Upload via HTTPS:**
- Criptografia TLS/SSL
- Mesma segurança que sites de banco

✅ **Autenticação Obrigatória:**
- Apenas administradores podem fazer upload/download
- Login necessário

✅ **Sem Porta de Banco Exposta:**
- PostgreSQL só aceita conexões locais
- Banco não está acessível pela internet

✅ **Validações:**
- Tipo de arquivo verificado
- Estrutura do banco validada
- Apenas dados do usuário são afetados

### Permissões

**Quem pode fazer upload/download:**
- ✅ Usuário admin
- ❌ Usuários normais
- ❌ Gerentes

**O que cada usuário vê:**
- Cada usuário vê apenas seus próprios dados
- Admin não vê dados de outros usuários automaticamente
- Isolamento total por user_id

## 📊 Comparação dos Métodos de Sincronização

| Método | Facilidade | Velocidade | Segurança | Requer Configuração |
|--------|-----------|-----------|-----------|---------------------|
| **Upload Web** | 🟢 Fácil | 🟡 Média | 🟢 Alta | ❌ Não |
| **Túnel SSH** | 🟡 Média | 🟢 Rápida | 🟢 Alta | ✅ Sim |
| **Porta Aberta** | 🔴 Difícil | 🟢 Rápida | 🔴 Baixa | ✅ Sim |

**Recomendação:**
- 🥇 **Upload Web** - Para maioria dos usuários
- 🥈 **Túnel SSH** - Para sincronização automática frequente
- 🥉 **Porta Aberta** - ❌ Não recomendado

## 💡 Dicas Avançadas

### 1. Automatizar Backup Antes de Sincronizar

No desktop, antes de fazer upload:
```python
# Copiar arquivos antes de enviar
import shutil
shutil.copy('financas.db', 'financas_backup.db')
shutil.copy('financas_receita.db', 'financas_receita_backup.db')
```

### 2. Agendar Downloads Periódicos

Use o agendador do Windows (Task Scheduler) para:
- Abrir o navegador na página de download
- Executar script que baixa automaticamente
- Manter desktop sempre atualizado

### 3. Mesclar Dados de Múltiplas Fontes

Se tem dados em vários lugares:
1. Download do servidor
2. Mesclar com dados locais usando SQLite
3. Upload consolidado (Modo Total)

### 4. Verificar Integridade

Após sincronizar, compare totais:
```sql
-- No SQLite (desktop)
SELECT COUNT(*), SUM(valor) FROM despesas;

-- No PostgreSQL (via site)
-- Veja no Dashboard ou Relatórios
```

## 📞 Suporte

Se encontrar problemas:

1. ✅ Verifique se está logado como admin
2. ✅ Confirme que está usando os arquivos corretos
3. ✅ Faça backup antes de operações em Modo Total
4. ✅ Teste com dados pequenos primeiro
5. ✅ Aguarde a conclusão completa antes de fechar a página

---

**Última atualização:** Dezembro 2025
**Versão:** 2.0
**Sistema:** Financeiro v15 com Sincronização Bidirecional

# 🔄 Guia de Sincronização Remota - Desktop ↔ VPS

Este guia explica como sincronizar os dados entre a versão **Desktop** (SQLite local) e a versão **Web** (PostgreSQL no VPS).

## 📋 Visão Geral

O sistema de sincronização permite:

- ✅ **Sincronizar Desktop → VPS** - Enviar seus dados locais para o servidor
- ✅ **Sincronizar VPS → Desktop** - Baixar dados do servidor para o desktop
- ✅ **Backup e Restauração** - De ambos os bancos de dados
- ✅ **Modo Parcial ou Total** - Adicionar dados ou substituir completamente
- ✅ **Sincronizar Orçamentos** - Incluindo categorias e valores orçados

## 🚀 Como Usar

### Passo 1: Configurar Servidor Remoto

1. Abra o sistema desktop
2. Vá em: **Arquivo → Sincronizar Bancos (Flask ↔ Desktop)**
3. Clique em **⚙️ Configurar Servidor Remoto**
4. Preencha os dados:

```
Modo: 🌐 Remoto (Produção)
Host: finan.receberbemevinhos.com.br (ou IP do servidor)
Porta: 5432
Banco de Dados: financeiro
Usuário: financeiro_user
Senha: [senha configurada no setup_production.py]
```

5. Clique em **🔌 Testar Conexão** para verificar
6. Clique em **✓ Salvar Configuração**

### Passo 2: Sincronizar Dados

#### 📤 Desktop → VPS (Exportar)

Use quando você fez lançamentos no desktop e quer enviar para o servidor web.

1. No gerenciador de sincronização, clique em **⬆️ Desktop → Flask (Exportar)**
2. Escolha o modo:
   - **Parcial (Adicionar)**: Adiciona dados sem apagar os existentes
   - **Total (Substituir)**: ⚠️ Apaga tudo do servidor e substitui pelos dados do desktop
3. Aguarde a sincronização
4. Verifique no site se os dados apareceram

#### 📥 VPS → Desktop (Importar)

Use quando você fez lançamentos no site e quer baixar para o desktop.

1. No gerenciador de sincronização, clique em **⬇️ Flask → Desktop (Importar)**
2. Escolha o modo:
   - **Parcial (Adicionar)**: Adiciona dados sem apagar os existentes
   - **Total (Substituir)**: ⚠️ Apaga tudo do desktop e substitui pelos dados do servidor
3. Aguarde a sincronização
4. Verifique no desktop se os dados apareceram

## ⚠️ Importante - Boas Práticas

### 1. Escolha um Banco Principal

**Opção A - Desktop Principal:**
- Faça todos os lançamentos no desktop
- Sincronize para o VPS periodicamente (modo **Parcial**)
- Use o site apenas para consulta

**Opção B - VPS Principal:**
- Faça todos os lançamentos no site
- Sincronize para o desktop periodicamente (modo **Parcial**)
- Use o desktop apenas para relatórios locais

### 2. Evite Duplicação

⚠️ **NÃO** faça lançamentos nos dois lugares sem sincronizar antes!

**Fluxo correto:**
1. Sincronize ⬇️ (VPS → Desktop) antes de trabalhar
2. Faça seus lançamentos
3. Sincronize ⬆️ (Desktop → VPS) após terminar

### 3. Faça Backups Antes de Sincronizar

Sempre faça backup antes de usar o modo **Total**:

1. **📦 Backup Flask DB** - Salva o banco do servidor
2. **📦 Backup Desktop DBs** - Salva o banco local

## 🔧 Configurações Avançadas

### Modo Local vs Remoto

O sistema suporta dois modos:

**🏠 Local (Desenvolvimento):**
- Conecta ao PostgreSQL na sua máquina (localhost)
- Útil para testar a aplicação Flask localmente
- Usa o DATABASE_URL do arquivo `.env`

**🌐 Remoto (Produção):**
- Conecta ao PostgreSQL no servidor VPS
- Para sincronizar com a versão web em produção
- Usa as credenciais configuradas no configurador

### Alterar Configuração

Para mudar de Local para Remoto ou vice-versa:

1. **Arquivo → Sincronizar Bancos**
2. **⚙️ Configurar Servidor Remoto**
3. Selecione o modo desejado
4. **✓ Salvar Configuração**

## 🔐 Segurança

### Porta do PostgreSQL no VPS

Por padrão, o PostgreSQL só aceita conexões locais. Para permitir conexão remota:

1. **Opção 1 - Túnel SSH (Mais Seguro):**
```bash
ssh -L 5432:localhost:5432 root@seu-servidor
```
Depois configure o host como `localhost` no desktop

2. **Opção 2 - Liberar Porta no Firewall:**
```bash
# No servidor
sudo ufw allow 5432/tcp

# Editar postgresql.conf
sudo nano /etc/postgresql/*/main/postgresql.conf
# Alterar: listen_addresses = '*'

# Editar pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Adicionar: host all all 0.0.0.0/0 md5

# Reiniciar
sudo systemctl restart postgresql
```

⚠️ **Recomendamos a Opção 1 (SSH) por ser mais segura!**

### Senha do Banco

A senha fica salva localmente em:
- Banco SQLite: `financas.db` → tabela `configuracoes`
- Arquivo: `.env` (se modo local)

⚠️ **Não compartilhe esses arquivos!**

## 📊 O que é Sincronizado

### Dados Sincronizados

✅ **Despesas:**
- Descrição, valor, parcelas
- Data de registro e pagamento
- Categoria e meio de pagamento

✅ **Orçamentos:**
- Categorias de despesa
- Valores orçados

✅ **Categorias:**
- Criadas automaticamente se não existirem

### Dados NÃO Sincronizados

❌ **Receitas** - Apenas despesas são sincronizadas
❌ **Usuários** - Sincroniza apenas dados do admin
❌ **Cartões** - Configurações de cartões não são sincronizadas

## 🐛 Troubleshooting

### Erro: "Configuração do banco não encontrada"

**Solução:** Configure o servidor remoto primeiro (Passo 1)

### Erro: "Não foi possível conectar ao servidor"

**Possíveis causas:**
1. ✅ Servidor VPS está online?
2. ✅ Porta 5432 está aberta?
3. ✅ Credenciais estão corretas?
4. ✅ PostgreSQL está rodando? (`sudo systemctl status postgresql`)

**Teste:**
```bash
# No servidor
sudo -u postgres psql -c "\l"

# Do seu computador (se porta liberada)
psql -h finan.receberbemevinhos.com.br -U financeiro_user -d financeiro
```

### Erro: "psycopg2 não instalado"

**Solução:**
```bash
pip install psycopg2-binary
```

### Erro: "Categoria/Meio de pagamento não encontrado"

O sistema cria automaticamente, mas se der erro:
1. Verifique se os nomes estão corretos
2. Sincronize as configurações primeiro
3. Use modo **Total** para garantir que tudo está sincronizado

## 📈 Logs e Monitoramento

Durante a sincronização, o sistema mostra:

- 🔵 **Info** - Operações normais
- 🟢 **Sucesso** - Operações concluídas
- 🟠 **Aviso** - Atenção necessária
- 🔴 **Erro** - Falhas que precisam correção

Exemplo de log:
```
[10:30:15] Iniciando exportação (PARCIAL) de 150 despesas...
[10:30:20] Sincronizando orçamentos...
[10:30:22] ✓ 10 orçamentos sincronizados.
[10:30:25] ✓ Exportação concluída: 150 OK, 0 erros
```

## 🎯 Casos de Uso Comuns

### Caso 1: Trabalho Principal no Desktop

```
1. Manhã: Fazer lançamentos no desktop
2. Fim do dia: Sincronizar ⬆️ (Desktop → VPS) modo Parcial
3. No site: Consultar e compartilhar com outros usuários
```

### Caso 2: Trabalho Principal no Site

```
1. Durante o dia: Fazer lançamentos no site
2. Fim do semana: Sincronizar ⬇️ (VPS → Desktop) modo Parcial
3. No desktop: Gerar relatórios detalhados
```

### Caso 3: Migração de Dados

```
1. Fazer backup de ambos os bancos
2. Decidir qual será a fonte de verdade
3. Usar modo Total para substituir completamente
4. Verificar se tudo está correto
```

## 📞 Suporte

Se tiver problemas:

1. Verifique o log de operações
2. Teste a conexão
3. Confira as credenciais
4. Verifique se o servidor está online

---

**Última atualização:** Dezembro 2025
**Versão:** 1.0
**Sistema:** Financeiro v15 com Sincronização Remota

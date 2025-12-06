# Changelog - Sincronização Bidirecional

## Data: Dezembro 2025
## Versão: Sistema Financeiro v15

### 🎯 Objetivo

Implementar sincronização bidirecional completa entre Sistema Desktop (SQLite) e Sistema Web (PostgreSQL), permitindo:
- ✅ Upload de despesas (Desktop → Servidor)
- ✅ Upload de receitas (Desktop → Servidor)
- ✅ Download de despesas (Servidor → Desktop)
- ✅ Download de receitas (Servidor → Desktop)

### 📝 Alterações Realizadas

#### 1. **routes/configuracao.py**

**Funções adicionadas:**

##### `importar_sqlite_receitas(sqlite_path, user_id, modo='parcial')`
- **Localização:** Linhas 14-109
- **Função:** Importa receitas do SQLite desktop para PostgreSQL
- **Parâmetros:**
  - `sqlite_path`: Caminho do arquivo `financas_receita.db`
  - `user_id`: ID do usuário para associar os dados
  - `modo`: 'parcial' (adicionar) ou 'total' (substituir)
- **Retorno:** Dict com contadores de receitas, categorias, meios de recebimento e erros

**Funcionalidades:**
- Valida estrutura do banco (verifica tabela `receitas`)
- Modo Total: Apaga todas as receitas do usuário antes de importar
- Cria automaticamente categorias de receita se não existirem
- Cria automaticamente meios de recebimento se não existirem
- Trata erros individualmente sem interromper importação

##### `exportar_sqlite_despesas()`
- **Localização:** Linhas 898-986
- **Rota:** `/configuracao/exportar-sqlite-despesas`
- **Função:** Exporta despesas do PostgreSQL para SQLite
- **Acesso:** Apenas admin (@admin_required)
- **Retorno:** Arquivo `financas.db` para download

**Funcionalidades:**
- Cria banco SQLite temporário
- Estrutura idêntica ao banco desktop:
  - Tabela `despesas` com todos os campos
  - Tabela `orcamento` com valores orçados
- Busca apenas dados do usuário logado
- Converte datas para formato SQLite (YYYY-MM-DD)
- Envia arquivo via `send_file` com nome `financas.db`

##### `exportar_sqlite_receitas()`
- **Localização:** Linhas 988-1054
- **Rota:** `/configuracao/exportar-sqlite-receitas`
- **Função:** Exporta receitas do PostgreSQL para SQLite
- **Acesso:** Apenas admin (@admin_required)
- **Retorno:** Arquivo `financas_receita.db` para download

**Funcionalidades:**
- Cria banco SQLite temporário
- Estrutura idêntica ao banco desktop de receitas:
  - Tabela `receitas` com todos os campos
- Busca apenas dados do usuário logado
- Converte datas para formato SQLite
- Envia arquivo via `send_file` com nome `financas_receita.db`

**Modificações em funções existentes:**

##### `importar_dados_antigos()` (linhas 247-442)
- Adicionado suporte para `tipo_banco` ('despesas' ou 'receitas')
- Campos de upload diferenciados:
  - `arquivo_sqlite_despesas` para despesas
  - `arquivo_sqlite_receitas` para receitas
- Lógica de roteamento:
  ```python
  if tipo_banco == 'despesas':
      resultado = importar_sqlite_desktop(...)
  else:  # receitas
      resultado = importar_sqlite_receitas(...)
  ```
- Mensagens de sucesso personalizadas para cada tipo

#### 2. **templates/config/importar_dados.html**

**Seção 1: Upload de Despesas (NOVA)**
- **Localização:** Linhas 13-91
- **Título:** "📤 Fazer Upload do Banco de Despesas"
- **Cor:** Borda vermelha (border-danger)
- **Campo:** `arquivo_sqlite_despesas`
- **Formulário:** `formUploadDespesas`
- **Campos ocultos:**
  - `tipo_importacao=upload`
  - `tipo_banco=despesas`
- **Modos:** Parcial (padrão) ou Total
- **Botão:** "📤 Fazer Upload e Importar Despesas" (btn-danger)

**Seção 2: Upload de Receitas (NOVA)**
- **Localização:** Linhas 93-171
- **Título:** "📤 Fazer Upload do Banco de Receitas"
- **Cor:** Borda verde (border-success)
- **Campo:** `arquivo_sqlite_receitas`
- **Formulário:** `formUploadReceitas`
- **Campos ocultos:**
  - `tipo_importacao=upload`
  - `tipo_banco=receitas`
- **Modos:** Parcial (padrão) ou Total
- **Botão:** "📤 Fazer Upload e Importar Receitas" (btn-success)

**Seção 3: Download de Bancos (NOVA)**
- **Localização:** Linhas 173-218
- **Título:** "📥 Baixar Bancos para Desktop"
- **Cor:** Borda azul (border-info)
- **Layout:** 2 colunas (row/col-md-6)

**Card 1 - Despesas:**
- Ícone: 🎴 wallet2 (vermelho)
- Botão: "Baixar financas.db"
- Link: `url_for('config.exportar_sqlite_despesas')`
- Classe: btn-danger

**Card 2 - Receitas:**
- Ícone: 💰 cash-coin (verde)
- Botão: "Baixar financas_receita.db"
- Link: `url_for('config.exportar_sqlite_receitas')`
- Classe: btn-success

**JavaScript atualizado (linhas 470-528):**
- **Separado em duas seções:**
  1. Validação para upload de despesas
  2. Validação para upload de receitas
- **Elementos por seção:**
  - Radio buttons de modo (parcial/total)
  - Alert de aviso
  - Formulário
- **Eventos:**
  - Change em radio buttons: mostra/oculta aviso
  - Submit: confirmação se modo total selecionado
- **Mensagens personalizadas:**
  - Despesas: "APAGAR todas as suas DESPESAS"
  - Receitas: "APAGAR todas as suas RECEITAS"

#### 3. **GUIA_SYNC_BIDIRECIONAL.md (NOVO)**

Documentação completa incluindo:
- Explicação de ambos os sentidos (Upload e Download)
- Instruções passo a passo para cada operação
- Diferença entre Modo Parcial e Modo Total
- 4 fluxos de trabalho recomendados
- Boas práticas e segurança
- Troubleshooting detalhado
- Comparação de métodos de sincronização
- Dicas avançadas

### 🔧 Tecnologias Utilizadas

- **Flask:** Framework web
- **SQLite3:** Manipulação de bancos SQLite
- **SQLAlchemy:** ORM para PostgreSQL
- **Werkzeug:** secure_filename, file uploads
- **Tempfile:** Arquivos temporários
- **Bootstrap 5:** Interface (cards, alerts, buttons)
- **Bootstrap Icons:** Ícones visuais

### 📊 Estrutura de Dados

#### Desktop (SQLite)

**Despesas - financas.db:**
```sql
CREATE TABLE despesas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    meio_pagamento TEXT NOT NULL,
    conta_despesa TEXT NOT NULL,
    valor REAL NOT NULL,
    num_parcelas INTEGER DEFAULT 1,
    data_registro TEXT,
    data_pagamento TEXT
)

CREATE TABLE orcamento (
    conta_despesa TEXT PRIMARY KEY,
    valor_orcado REAL NOT NULL
)
```

**Receitas - financas_receita.db:**
```sql
CREATE TABLE receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    meio_recebimento TEXT NOT NULL,
    categoria_receita TEXT NOT NULL,
    valor REAL NOT NULL,
    num_parcelas INTEGER DEFAULT 1,
    data_registro TEXT,
    data_recebimento TEXT
)
```

#### Servidor (PostgreSQL)

- **Tabelas:** `despesas`, `receitas`, `categoria_despesa`, `categoria_receita`, `meio_pagamento`, `meio_recebimento`, `orcamento`
- **Relacionamentos:** Foreign keys para user_id, categoria_id, meio_id
- **Isolamento:** Cada usuário vê apenas seus dados (WHERE user_id = current_user.id)

### 🔐 Segurança Implementada

1. **Autenticação:**
   - `@login_required` em todas as rotas
   - `@admin_required` em rotas de upload/download
   - Apenas admin pode importar/exportar dados

2. **Validação de Arquivos:**
   - Extensões permitidas: .db, .sqlite, .sqlite3
   - Verificação de estrutura (tabelas despesas/receitas)
   - secure_filename() para nomes de arquivo

3. **Isolamento de Dados:**
   - Queries filtradas por user_id
   - Cada usuário acessa apenas seus dados
   - Sem acesso cross-user

4. **Temporários Seguros:**
   - Arquivos salvos em tempfile.gettempdir()
   - Removidos após processamento
   - Nomes únicos com timestamp

5. **Confirmações:**
   - JavaScript confirma ações em Modo Total
   - Alertas visuais de perigo
   - Mensagens claras sobre consequências

### 🧪 Testes Sugeridos

#### Teste 1: Upload de Despesas (Modo Parcial)
1. Criar 5 despesas no desktop
2. Fazer upload via web
3. Verificar no dashboard que as 5 aparecem
4. Criar mais 3 despesas no desktop
5. Upload novamente (Parcial)
6. Verificar total de 8 despesas

#### Teste 2: Upload de Receitas (Modo Total)
1. Criar 10 receitas no servidor
2. Criar 5 receitas diferentes no desktop
3. Upload via web (Modo Total)
4. Verificar que servidor tem apenas as 5 do desktop

#### Teste 3: Download de Despesas
1. Criar 7 despesas no servidor
2. Download via web
3. Substituir financas.db no desktop
4. Abrir desktop e verificar 7 despesas

#### Teste 4: Download de Receitas
1. Criar 12 receitas no servidor
2. Download via web
3. Substituir financas_receita.db no desktop
4. Abrir desktop e verificar 12 receitas

#### Teste 5: Ciclo Completo Bidirecional
1. Desktop: 10 despesas
2. Upload → Servidor (Modo Total)
3. Servidor: Adicionar 5 despesas
4. Download → Desktop
5. Desktop: Verificar 15 despesas
6. Desktop: Adicionar 3 despesas
7. Upload → Servidor (Modo Parcial)
8. Servidor: Verificar 18 despesas

### 📈 Melhorias Futuras (Opcional)

1. **Sincronização Automática:**
   - Botão no desktop que faz upload e download automaticamente
   - Detecção de conflitos (mesma despesa modificada em ambos lados)
   - Merge inteligente de dados

2. **Histórico de Sincronizações:**
   - Tabela de log com data/hora de cada sync
   - Quantidade de registros sincronizados
   - Usuário que fez a sincronização

3. **Sincronização Incremental:**
   - Apenas dados modificados desde última sync
   - Baseado em timestamps
   - Mais rápido para bancos grandes

4. **Validação de Integridade:**
   - Checksums MD5/SHA para verificar arquivos
   - Comparação de totais antes/depois
   - Alertas se divergências grandes

5. **Suporte a Fluxo de Caixa:**
   - Upload/Download de fluxo_caixa.db
   - Balanços mensais
   - Eventos de caixa

### ✅ Checklist de Implementação

- [x] Função `importar_sqlite_receitas()` criada
- [x] Função `exportar_sqlite_despesas()` criada
- [x] Função `exportar_sqlite_receitas()` criada
- [x] Rota `/exportar-sqlite-despesas` registrada
- [x] Rota `/exportar-sqlite-receitas` registrada
- [x] HTML template atualizado com dual upload
- [x] JavaScript de validação atualizado
- [x] Seção de download adicionada ao template
- [x] Botões de download criados
- [x] Documentação completa (GUIA_SYNC_BIDIRECIONAL.md)
- [x] Changelog criado (este arquivo)

### 🚀 Como Usar

1. **Deploy no servidor:**
   ```bash
   cd /var/www/financeiro
   git pull
   sudo systemctl restart financeiro
   ```

2. **Acessar no navegador:**
   - URL: https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos

3. **Fazer upload:**
   - Selecionar `financas.db` para despesas
   - Selecionar `financas_receita.db` para receitas
   - Escolher modo (Parcial/Total)
   - Clicar em "Fazer Upload e Importar"

4. **Fazer download:**
   - Clicar em "Baixar financas.db" ou "Baixar financas_receita.db"
   - Salvar arquivo
   - Substituir no desktop

### 📞 Suporte

Para problemas ou dúvidas:
1. Consultar GUIA_SYNC_BIDIRECIONAL.md
2. Consultar GUIA_UPLOAD_WEB.md (upload apenas)
3. Verificar logs do servidor: `sudo journalctl -u financeiro -f`

---

**Desenvolvido em:** Dezembro 2025
**Versão Sistema:** v15
**Funcionalidade:** Sincronização Bidirecional Completa

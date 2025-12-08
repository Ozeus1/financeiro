# 🔄 Atualização: Fluxo de Caixa Adicionado!

## ✅ O Que Foi Adicionado

### Upload (Desktop → Servidor):
- ✅ Upload de `fluxo_caixa.db` via web
- ✅ Importa balanços mensais
- ✅ Importa eventos de caixa avulsos
- ✅ Modo Parcial: Atualiza balanços existentes + adiciona novos
- ✅ Modo Total: Substitui todos os dados

### Download (Servidor → Desktop):
- ✅ Download de `fluxo_caixa.db`
- ✅ Exporta todos os balanços mensais
- ✅ Exporta todos os eventos de caixa
- ✅ Formato SQLite compatível com desktop

## 🚀 ATUALIZAR SERVIDOR VPS AGORA

Execute este comando no servidor:

```bash
cd /var/www/financeiro && \
sudo -u www-data git pull origin main && \
sudo systemctl restart financeiro && \
sudo systemctl status financeiro
```

## ✅ Verificação Pós-Atualização

### 1. Acesse a página de importação:
```
https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos
```

### 2. Você deve ver 4 seções agora:

**Upload:**
1. 📤 Fazer Upload do Banco de Despesas (vermelho)
2. 📤 Fazer Upload do Banco de Receitas (verde)
3. 📤 **Fazer Upload do Fluxo de Caixa (azul)** ← NOVO!

**Download:**
4. 📥 Baixar Bancos para Desktop (3 botões):
   - Despesas (financas.db)
   - Receitas (financas_receita.db)
   - **Fluxo de Caixa (fluxo_caixa.db)** ← NOVO!

### 3. Testar Upload de Fluxo de Caixa:

1. Clique em "Escolher arquivo" na seção de Fluxo de Caixa
2. Selecione `fluxo_caixa.db` do seu desktop
3. Escolha modo:
   - **Parcial**: Atualiza balanços existentes, adiciona novos eventos
   - **Total**: Apaga tudo e reimporta
4. Clique em "📤 Fazer Upload e Importar Fluxo de Caixa"

**Resultado esperado:**
```
✓ Importação de FLUXO DE CAIXA concluída!
Balanços Mensais: X
Eventos de Caixa: Y
```

### 4. Testar Download de Fluxo de Caixa:

1. Na seção "📥 Baixar Bancos para Desktop"
2. Clique em "Baixar fluxo_caixa.db"
3. Arquivo deve fazer download
4. Verificar que não está vazio (> 0 KB)

## 📊 Dados Sincronizados

### Balanços Mensais:
- Ano e mês
- Total de entradas
- Total de saídas
- Saldo do mês
- Observações

### Eventos de Caixa Avulsos:
- Data do evento
- Descrição
- Valor

## 🎯 Casos de Uso

### Caso 1: Sincronizar Desktop → Servidor
```
1. Desktop tem fluxo de caixa atualizado
2. Fazer upload do fluxo_caixa.db (Modo Parcial)
3. Servidor fica com os mesmos dados
```

### Caso 2: Sincronizar Servidor → Desktop
```
1. Servidor tem dados mais recentes
2. Baixar fluxo_caixa.db
3. Substituir no desktop
4. Desktop fica atualizado
```

### Caso 3: Migração Completa
```
1. Primeira sincronização
2. Upload fluxo_caixa.db (Modo Total)
3. Servidor tem cópia exata do desktop
```

## 🔀 Modos de Importação

### Modo Parcial (Recomendado):
- ✅ Mantém balanços existentes
- ✅ Atualiza balanços se ano/mês já existe
- ✅ Adiciona novos eventos
- ⚠️ Pode duplicar eventos se importar múltiplas vezes

### Modo Total (Cuidado!):
- ❌ APAGA todos os balanços
- ❌ APAGA todos os eventos
- ✅ Importa tudo do arquivo
- ⚠️ Perda de dados se não fizer backup!

## 📋 Estrutura do Banco SQLite

### fluxo_caixa.db contém:

```sql
CREATE TABLE balanco_mensal (
    id INTEGER PRIMARY KEY,
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    total_entradas REAL DEFAULT 0.0,
    total_saidas REAL DEFAULT 0.0,
    saldo_mes REAL DEFAULT 0.0,
    observacoes TEXT
);

CREATE TABLE eventos_caixa_avulsos (
    id INTEGER PRIMARY KEY,
    data TEXT NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL
);
```

## 🆘 Troubleshooting

### Erro: "Arquivo não é um banco de fluxo de caixa válido"
**Solução:**
- Verifique se é realmente o arquivo `fluxo_caixa.db`
- Arquivo deve ter tabelas `balanco_mensal` ou `eventos_caixa_avulsos`

### Erro: "Permission denied"
**Solução:**
```bash
sudo chown -R www-data:www-data /var/www/financeiro
sudo systemctl restart financeiro
```

### Balanços Não Aparecem Após Upload
**Causas possíveis:**
- Arquivo vazio
- Modo Parcial e balanços já existiam (foram atualizados, não duplicados)
- Erro durante importação

**Verificar:**
1. Ver mensagem de sucesso
2. Conferir contadores (Balanços: X, Eventos: Y)
3. Acessar página de Fluxo de Caixa no sistema

### Download Retorna Arquivo Vazio
**Causa:** Usuário não tem dados de fluxo de caixa
**Solução:** Criar balanços/eventos primeiro, ou importar do desktop

## 📊 Completude da Funcionalidade

Agora você tem sincronização bidirecional COMPLETA:

| Tipo | Upload | Download |
|------|--------|----------|
| **Despesas** | ✅ | ✅ |
| **Receitas** | ✅ | ✅ |
| **Fluxo de Caixa** | ✅ | ✅ |
| **Orçamentos** | ✅ (com despesas) | ✅ (com despesas) |

## 🎉 Próximos Passos

1. ✅ Atualizar servidor (comando acima)
2. ✅ Testar upload de fluxo de caixa
3. ✅ Testar download de fluxo de caixa
4. ✅ Verificar dados no sistema
5. ✅ Usar no dia a dia!

---

**Data:** Dezembro 2025
**Commit:** 430c31a
**Funcionalidade:** Sincronização de Fluxo de Caixa
**Status:** ✅ Completo

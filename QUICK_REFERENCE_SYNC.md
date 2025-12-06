# 🚀 Referência Rápida - Sincronização Bidirecional

## 📤 Upload (Desktop → Servidor)

### Via Sistema Desktop
```
1. Arquivo → Sincronizar Bancos
2. 🌐 Upload via Web (Sem Porta)
3. Login no site (se necessário)
4. Escolher arquivo e modo
5. Fazer Upload
```

### Via Navegador Direto
```
URL: https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos
Login: admin / admin123
```

## 📥 Download (Servidor → Desktop)

### Passos
```
1. Acessar mesma URL acima
2. Rolar até "📥 Baixar Bancos para Desktop"
3. Clicar em "Baixar financas.db" ou "Baixar financas_receita.db"
4. Salvar arquivo
5. BACKUP do arquivo atual no desktop!
6. Substituir arquivo no desktop
7. Reabrir sistema desktop
```

## 🎯 Arquivos

| Tipo | Desktop | Servidor | URL Download |
|------|---------|----------|--------------|
| **Despesas** | `financas.db` | PostgreSQL | `/configuracao/exportar-sqlite-despesas` |
| **Receitas** | `financas_receita.db` | PostgreSQL | `/configuracao/exportar-sqlite-receitas` |

## 🔀 Modos de Importação

| Modo | Quando Usar | O Que Faz | Risco |
|------|-------------|-----------|-------|
| **Parcial** | Sync diária | Adiciona dados | Duplicatas |
| **Total** | Primeira vez | Substitui tudo | Perda de dados |

## ⚠️ Regra de Ouro

```
SEMPRE faça backup antes de:
- Usar Modo Total
- Substituir arquivos no desktop
- Fazer sincronização importante
```

## 🔄 Fluxos Comuns

### Rotina Diária (Desktop → Web)
```
Desktop: Trabalhar o dia todo
      ↓
    Upload (Parcial)
      ↓
Servidor: Dados atualizados
```

### Sincronizar Tudo (Web → Desktop)
```
Servidor: Tem dados mais recentes
      ↓
   Download
      ↓
Desktop: Substituir arquivos
      ↓
Desktop: Dados atualizados
```

### Migração Completa
```
Desktop: Dados completos
      ↓
    Upload (TOTAL)
      ↓
Servidor: Cópia exata
```

## 🆘 SOS Rápido

| Problema | Solução |
|----------|---------|
| Arquivo não aceito | Use apenas .db |
| Tabela não encontrada | Arquivo errado (despesas vs receitas) |
| Dados duplicados | Use Modo Total para resetar |
| Download não abre | Renomeie para nome correto |
| Muito lento | Aguarde 1-2 min para bancos grandes |

## 🔐 Segurança

✅ HTTPS criptografado
✅ Apenas admin pode fazer upload/download
✅ Banco PostgreSQL não exposto
✅ Cada usuário vê só seus dados

## 📱 Acesso Rápido

**URL Completa:**
```
https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos
```

**Ou pelo Desktop:**
```
Arquivo → Sincronizar Bancos → Upload via Web
```

---

**Guia Completo:** Ver `GUIA_SYNC_BIDIRECIONAL.md`
**Detalhes Técnicos:** Ver `CHANGELOG_SYNC_BIDIRECIONAL.md`

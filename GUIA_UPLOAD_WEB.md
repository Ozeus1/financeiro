# 📤 Guia de Upload via Web - Sincronização Sem Abrir Porta

Este guia explica como sincronizar Desktop → VPS **sem precisar abrir a porta 5432 do PostgreSQL**, usando upload via navegador.

## 🎯 Vantagens desta Solução

✅ **Não precisa abrir porta PostgreSQL** - Mais seguro!
✅ **Não precisa túnel SSH** - Mais simples!
✅ **Funciona de qualquer lugar** - Só precisa de internet
✅ **Interface amigável** - Upload via navegador
✅ **Sem configuração de firewall** - Usa porta 80/443 (HTTP/HTTPS)

## 🚀 Como Usar

### Método 1: Pelo Sistema Desktop (Recomendado)

1. **Abra o sistema desktop**

2. **Vá em: Arquivo → Sincronizar Bancos (Flask ↔ Desktop)**

3. **Clique em: 🌐 Upload via Web (Sem Porta)**

4. **O navegador abrirá automaticamente** na página de upload

5. **Faça login** no sistema web (se ainda não estiver logado)
   - Usuário: admin
   - Senha: admin123 (ou a senha que você alterou)

6. **Na página de upload:**
   - Clique em "Escolher arquivo"
   - Selecione o arquivo `financas.db` (localização mostrada no desktop)
   - Escolha o modo:
     - **Parcial (Adicionar)**: Adiciona aos dados existentes ✅ Recomendado
     - **Total (Substituir)**: ⚠️ Apaga tudo e substitui
   - Clique em "📤 Fazer Upload e Importar"

7. **Aguarde a confirmação** (pode levar alguns segundos)

8. **Pronto!** Seus dados estão no servidor

### Método 2: Direto pelo Navegador

1. **Acesse o site:** https://finan.receberbemevinhos.com.br/config/upload_database

2. **Faça login** (se necessário)

3. **Selecione o arquivo do banco:**
   - Arquivo: `financas.db`
   - Localização: Mesma pasta do executável do sistema desktop

4. **Escolha o modo e faça upload**

## 📋 Instruções Detalhadas

### Localizar o Arquivo do Banco

O arquivo `financas.db` normalmente está em:

**Windows:**
- `C:\Users\SEU_USUARIO\OneDrive\ProjPython\FINAN\financas.db`
- Ou na mesma pasta onde está o executável do sistema

**Como encontrar:**
1. No sistema desktop, vá em: Arquivo → Sincronizar Bancos
2. A janela mostrará o caminho completo do arquivo
3. Anote ou copie este caminho

### Modos de Importação

#### 🟢 Parcial (Adicionar) - RECOMENDADO

**Use quando:**
- Já tem dados no servidor
- Quer adicionar novos lançamentos
- Quer sincronizar sem perder dados

**O que faz:**
- ✅ Mantém dados existentes no servidor
- ✅ Adiciona novos dados do arquivo
- ⚠️ Pode criar duplicatas se os mesmos dados já existirem

**Exemplo:**
```
Servidor: 100 despesas
Arquivo:  50 despesas (novas)
Resultado: 150 despesas
```

#### 🔴 Total (Substituir) - CUIDADO!

**Use quando:**
- Primeira sincronização
- Quer fazer migração completa
- Tem certeza que quer apagar tudo do servidor

**O que faz:**
- ❌ APAGA todos os dados do servidor
- ✅ Importa todos os dados do arquivo
- ⚠️ PERDA DE DADOS se não fizer backup antes!

**Exemplo:**
```
Servidor: 100 despesas (SERÃO APAGADAS!)
Arquivo:  50 despesas
Resultado: 50 despesas (apenas do arquivo)
```

### Dados Sincronizados

✅ **Despesas completas:**
- Descrição, valor, parcelas
- Datas (registro e pagamento)
- Categoria e meio de pagamento

✅ **Orçamentos:**
- Categorias
- Valores orçados

✅ **Categorias e Meios de Pagamento:**
- Criados automaticamente se não existirem

❌ **NÃO sincroniza:**
- Receitas
- Usuários
- Cartões

## 🔐 Segurança

### Por que é mais seguro?

**Sem abrir porta PostgreSQL:**
- ✅ Banco PostgreSQL só aceita conexões locais (localhost)
- ✅ Não expõe o banco de dados para a internet
- ✅ Usa HTTPS (porta 443) que já está aberta e criptografada
- ✅ Requer login no sistema web (autenticação)

**Com porta PostgreSQL aberta:**
- ❌ Banco exposto para a internet
- ❌ Risco de ataques diretos ao banco
- ❌ Precisa configurar firewall corretamente
- ❌ Mais complexo de gerenciar

### Permissões

**Apenas administradores** podem fazer upload:
- O sistema verifica se você é admin antes de permitir
- Usuários normais não têm acesso a esta funcionalidade

## ⚠️ Boas Práticas

### 1. Faça Backup Antes de Usar Modo Total

```bash
# No servidor VPS
sudo -u postgres pg_dump financeiro > backup_antes_upload.sql
```

Ou use o sistema desktop:
- Arquivo → Sincronizar Bancos
- 📦 Backup Flask DB

### 2. Use Modo Parcial na Maioria dos Casos

O modo **Parcial** é mais seguro porque:
- Não apaga dados existentes
- Permite reverter se algo der errado
- Evita perda acidental de dados

Use **Total** apenas quando:
- É a primeira vez que sincroniza
- Tem backup e quer migração completa
- Sabe exatamente o que está fazendo

### 3. Verifique o Resultado

Após o upload:
1. Vá para o Dashboard
2. Confira se os dados apareceram
3. Verifique os totais
4. Teste algumas funcionalidades

## 🆘 Troubleshooting

### Erro: "Tipo de arquivo não permitido"

**Causa:** Arquivo não é .db, .sqlite ou .sqlite3

**Solução:**
- Verifique se selecionou o arquivo correto
- O arquivo deve ter extensão `.db`
- Arquivo: `financas.db` (não `financas_receitas.db`)

### Erro: "Tabela despesas não encontrada"

**Causa:** Arquivo não é um banco de dados válido

**Solução:**
- Verifique se o arquivo é realmente o banco do sistema desktop
- Não envie o banco de receitas (`financas_receitas.db`)
- Use apenas `financas.db`

### Erro: "Apenas administradores podem fazer upload"

**Causa:** Usuário logado não é admin

**Solução:**
- Faça login com usuário admin
- Usuário padrão: admin / admin123

### Upload Travou ou Demorou Muito

**Possíveis causas:**
- Banco de dados muito grande
- Conexão lenta
- Timeout do servidor

**Solução:**
1. Aguarde mais um pouco (pode levar 1-2 minutos para bancos grandes)
2. Se travar, recarregue a página
3. Tente usar modo Parcial com menos dados
4. Use sincronização direta se o upload não funcionar

### Dados Duplicados Após Upload Parcial

**Causa:** Upload do mesmo arquivo várias vezes em modo Parcial

**Solução:**
1. Use modo Total para limpar e recomeçar
2. Ou delete as duplicatas manualmente no sistema web
3. Da próxima vez, use upload apenas para dados novos

## 📊 Comparação dos Métodos

| Método | Porta 5432 | Complexidade | Segurança | Velocidade |
|--------|------------|--------------|-----------|------------|
| **Upload Web** | ❌ Não precisa | 🟢 Fácil | 🟢 Alta | 🟡 Média |
| **Túnel SSH** | ❌ Não precisa | 🟡 Média | 🟢 Alta | 🟢 Rápida |
| **Porta Aberta** | ✅ Precisa | 🔴 Difícil | 🔴 Baixa | 🟢 Rápida |

**Recomendação:**
- 🥇 **Upload Web** - Para usuários comuns
- 🥈 **Túnel SSH** - Para técnicos/desenvolvedores
- 🥉 **Porta Aberta** - ❌ Não recomendado

## 🎯 Fluxos de Trabalho Recomendados

### Fluxo 1: Trabalho Diário no Desktop

```
1. Fazer lançamentos no sistema desktop durante o dia
   ↓
2. Fim do dia: Fazer upload via web (Modo Parcial)
   ↓
3. Dados aparecem no site para consulta
   ↓
4. Repetir diariamente
```

### Fluxo 2: Primeira Sincronização

```
1. Fazer backup do servidor (se já tiver dados)
   ↓
2. Fazer upload do banco desktop (Modo Total)
   ↓
3. Verificar se tudo está correto no site
   ↓
4. Usar Modo Parcial nas próximas sincronizações
```

### Fluxo 3: Sincronização Bidirecional

```
Desktop:
  1. Sincronizar VPS → Desktop (via sincronizador)
  2. Fazer lançamentos
  3. Upload via Web (Modo Parcial)
     ↓
Site:
  Consultar dados atualizados
```

## 📞 Suporte

Se tiver problemas:

1. ✅ Verifique se está logado como admin
2. ✅ Confirme que o arquivo é `financas.db`
3. ✅ Teste com arquivo pequeno primeiro (modo Parcial)
4. ✅ Faça backup antes de usar modo Total
5. ✅ Aguarde a confirmação antes de fechar a página

---

**Última atualização:** Dezembro 2025
**Versão:** 1.0
**Sistema:** Financeiro v15 com Upload via Web

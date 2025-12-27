# 📤 IMPORTAR FECHAMENTOS DE CARTÕES NA VPS

## ✅ Dados que serão importados (do sistema desktop)

- **Cartão Azul** → Fecha: dia 1, Vence: dia 11
- **Cartão BB** → Fecha: dia 30, Vence: dia 9
- **Cartão C6** → Fecha: dia 4, Vence: dia 14
- **Cartão Gol** → Fecha: dia 1, Vence: dia 11
- **Cartão Latam** → Fecha: dia 1, Vence: dia 11
- **Cartão Mercado Pago** → Fecha: dia 8, Vence: dia 18
- **Cartão Nubank** → Fecha: dia 30, Vence: dia 9
- **Cartão Pão de Açúcar** → Fecha: dia 30, Vence: dia 9
- **Cartão Unlimited Master** → Fecha: dia 3, Vence: dia 13
- **Cartão Unlimited Visa** → Fecha: dia 1, Vence: dia 11

**Total:** 10 cartões

---

## 🚀 PASSO A PASSO - Execute na VPS

### 1. Conectar na VPS via SSH

```bash
ssh root@SEU_IP_VPS
```

### 2. Ir para o diretório da aplicação

```bash
cd /var/www/financeiro
```

### 3. Fazer upload do arquivo Python

**Opção A - Criar arquivo direto na VPS:**

```bash
nano importar_fechamentos.py
```

Copie e cole TODO o conteúdo do arquivo `importar_fechamentos_vps.py` e salve:
- Ctrl+O (salvar)
- Enter (confirmar)
- Ctrl+X (sair)

**Opção B - Fazer upload via SCP (do seu PC):**

```bash
scp C:\Users\orlei\OneDrive\ProjPython\FINAN\importar_fechamentos_vps.py root@SEU_IP:/var/www/financeiro/
```

### 4. Executar o script

```bash
cd /var/www/financeiro
source venv/bin/activate
python importar_fechamentos.py
```

**Saída esperada:**

```
[OK] Adicionado: Cartão Azul - Fecha: 1, Vence: 11
[OK] Adicionado: Cartão BB - Fecha: 30, Vence: 9
[OK] Adicionado: Cartão C6 - Fecha: 4, Vence: 14
[OK] Adicionado: Cartão Gol - Fecha: 1, Vence: 11
[OK] Adicionado: Cartão Latam - Fecha: 1, Vence: 11
[OK] Adicionado: Cartão Mercado Pago - Fecha: 8, Vence: 18
[OK] Adicionado: Cartão Nubank - Fecha: 30, Vence: 9
[OK] Adicionado: Cartão Pão de Açúcar - Fecha: 30, Vence: 9
[OK] Adicionado: Cartão Unlimited Master - Fecha: 3, Vence: 13
[OK] Adicionado: Cartão Unlimited Visa - Fecha: 1, Vence: 11
[OK] Fechamentos salvos com sucesso!
```

### 5. Verificar na aplicação web

Acesse: https://finan.receberbemevinhos.com.br/configuracao/cartoes

Você deve ver os 10 cartões configurados com suas datas de fechamento e vencimento.

### 6. Baixar NOVAMENTE os arquivos .db

Acesse: https://finan.receberbemevinhos.com.br/configuracao/importar-dados-antigos

Baixe os 3 arquivos:
1. **financas.db** (botão vermelho)
2. **financas_receitas.db** (botão verde)
3. **fluxo_caixa.db** (botão azul)

### 7. Testar no sistema desktop

Abra o `sistema_financeiro_v15.py` e teste o relatório de previsão de fatura dos cartões.

Agora deve funcionar! ✅

---

## ⚠️ IMPORTANTE - Dias de Vencimento

O banco desktop **NÃO** tem a coluna `dia_vencimento`.

Os dias de vencimento foram **estimados** usando a fórmula:
```
vencimento = fechamento + 10 dias
```

**Exemplo:**
- Cartão C6: Fecha dia 4 → Vence dia 14 (4 + 10)
- Cartão BB: Fecha dia 30 → Vence dia 9 ((30 + 10) % 31 = 9)

**VERIFIQUE** se os dias de vencimento estão corretos!

Se precisar ajustar:
1. Acesse: https://finan.receberbemevinhos.com.br/configuracao/cartoes
2. Edite manualmente os dias de vencimento incorretos
3. Baixe novamente os arquivos .db

---

## 🆘 Se algo der errado

### Script não encontra um cartão

Se aparecer:
```
[AVISO] Meio de pagamento nao encontrado: Cartão XXX
```

**Causa:** O cartão tem nome diferente no Flask do que no desktop.

**Solução:**
1. Acesse `/configuracao/meios-pagamento` no Flask
2. Verifique o nome exato do cartão
3. Edite o script `importar_fechamentos.py` e corrija o nome
4. Execute novamente

### Erro ao salvar

Se aparecer:
```
[ERRO] Falha ao salvar: ...
```

**Verifique:**
- Permissões do PostgreSQL
- Conexão com o banco de dados
- Logs da aplicação: `sudo journalctl -u financeiro -n 50`

### Rollback (reverter importação)

Se quiser remover os fechamentos importados:

```bash
cd /var/www/financeiro
source venv/bin/activate
python
```

```python
from models import db, FechamentoCartao
from app import app

with app.app_context():
    FechamentoCartao.query.delete()
    db.session.commit()
    print("Todos os fechamentos foram removidos!")
```

---

## 📊 Resumo

1. ✅ Upload do script Python na VPS
2. ✅ Executar script para importar fechamentos
3. ✅ Verificar na página de configuração de cartões
4. ✅ Baixar novamente os arquivos .db
5. ✅ Testar no sistema desktop

**Data:** 2025-12-08
**Arquivo:** importar_fechamentos_vps.py
**Cartões:** 10 configurações

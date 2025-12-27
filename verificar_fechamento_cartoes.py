"""
Script para verificar dados de fechamento_cartoes no arquivo financas.db
"""
import sqlite3
import os
import sys

# Configurar encoding para UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Caminhos para os arquivos
db_flask = r'C:\Users\orlei\Downloads\bkp\financas.db'  # Arquivo do Flask
db_desktop = r'C:\Users\orlei\OneDrive\Área de Trabalho\Financas\bkp_0812\financas.db'  # Arquivo do desktop

print("Verificando arquivo do FLASK...")
if not os.path.exists(db_flask):
    print(f"[ERRO] Arquivo Flask nao encontrado: {db_flask}")
    db_flask = None

print("Verificando arquivo do DESKTOP...")
if not os.path.exists(db_desktop):
    print(f"[ERRO] Arquivo Desktop nao encontrado: {db_desktop}")
    db_desktop = None

if not db_flask and not db_desktop:
    print("[ERRO] Nenhum arquivo encontrado!")
    exit(1)

print("="*60)
print("VERIFICAÇÃO DE FECHAMENTO DE CARTÕES")
print("="*60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Verificar estrutura da tabela
print("\n1. ESTRUTURA DA TABELA fechamento_cartoes:")
print("-"*60)
try:
    cursor.execute("PRAGMA table_info(fechamento_cartoes)")
    colunas = cursor.fetchall()
    if colunas:
        for col in colunas:
            print(f"  [OK] {col[1]} ({col[2]})")
    else:
        print("  [ERRO] Tabela nao existe!")
except Exception as e:
    print(f"  [ERRO] Erro ao verificar tabela: {e}")

# 2. Verificar dados na tabela
print("\n2. DADOS NA TABELA fechamento_cartoes:")
print("-"*60)
try:
    cursor.execute("SELECT COUNT(*) FROM fechamento_cartoes")
    total = cursor.fetchone()[0]
    print(f"  Total de registros: {total}")

    if total > 0:
        cursor.execute("SELECT * FROM fechamento_cartoes")
        rows = cursor.fetchall()
        print("\n  Registros encontrados:")
        for row in rows:
            print(f"    {row}")
    else:
        print("  [AVISO] TABELA VAZIA - Nenhum fechamento cadastrado!")
        print("\n  SOLUCAO:")
        print("  1. Acesse: https://finan.receberbemevinhos.com.br/configuracao/cartoes")
        print("  2. Configure o fechamento dos seus cartoes")
        print("  3. Baixe o arquivo financas.db novamente")
except Exception as e:
    print(f"  [ERRO] Erro ao ler dados: {e}")

# 3. Verificar meios de pagamento
print("\n3. MEIOS DE PAGAMENTO (CARTÕES):")
print("-"*60)
try:
    cursor.execute("SELECT nome FROM meios_pagamento WHERE nome LIKE '%Cartão%' OR nome LIKE '%cartão%'")
    cartoes = cursor.fetchall()
    if cartoes:
        print(f"  Total de cartões cadastrados: {len(cartoes)}")
        for cartao in cartoes:
            print(f"    - {cartao[0]}")
    else:
        print("  [AVISO] Nenhum cartao encontrado nos meios de pagamento")
except Exception as e:
    print(f"  [ERRO] Erro ao ler meios de pagamento: {e}")

# 4. Verificar se existe view v_despesas_compat
print("\n4. VIEWS E TABELAS NO BANCO:")
print("-"*60)
try:
    cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY type, name")
    objetos = cursor.fetchall()
    for obj in objetos:
        tipo = obj[1].upper()
        nome = obj[0]
        if nome.startswith('sqlite_'):
            continue
        print(f"  {tipo}: {nome}")
except Exception as e:
    print(f"  [ERRO] Erro ao listar objetos: {e}")

conn.close()

print("\n" + "="*60)
print("VERIFICAÇÃO CONCLUÍDA")
print("="*60)

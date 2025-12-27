# -*- coding: utf-8 -*-
"""
Script para comparar dados de fechamento_cartoes entre Flask e Desktop
"""
import sqlite3
import os
import sys

# Configurar encoding para UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Caminhos para os arquivos
db_flask = r'C:\Users\orlei\Downloads\bkp\financas.db'
db_desktop = r'C:\Users\orlei\OneDrive\Área de Trabalho\Financas\bkp_0812\financas.db'

def verificar_fechamento(db_path, nome):
    """Verifica dados de fechamento_cartoes em um banco"""
    print(f"\n{'='*70}")
    print(f"VERIFICANDO: {nome}")
    print(f"Arquivo: {db_path}")
    print(f"{'='*70}")

    if not os.path.exists(db_path):
        print(f"[ERRO] Arquivo nao encontrado!")
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    resultado = {}

    # 1. Estrutura da tabela
    print("\n1. ESTRUTURA DA TABELA fechamento_cartoes:")
    print("-"*70)
    try:
        cursor.execute("PRAGMA table_info(fechamento_cartoes)")
        colunas = cursor.fetchall()
        if colunas:
            resultado['colunas'] = colunas
            for col in colunas:
                print(f"  [OK] Coluna: {col[1]:20s} Tipo: {col[2]}")
        else:
            print("  [ERRO] Tabela nao existe!")
            resultado['colunas'] = []
    except Exception as e:
        print(f"  [ERRO] {e}")
        resultado['colunas'] = []

    # 2. Dados na tabela
    print("\n2. DADOS NA TABELA fechamento_cartoes:")
    print("-"*70)
    try:
        cursor.execute("SELECT COUNT(*) FROM fechamento_cartoes")
        total = cursor.fetchone()[0]
        print(f"  Total de registros: {total}")

        if total > 0:
            cursor.execute("SELECT * FROM fechamento_cartoes")
            rows = cursor.fetchall()
            resultado['dados'] = rows
            print("\n  Registros:")
            # Descobrir nomes das colunas
            col_names = [desc[0] for desc in cursor.description]
            print(f"    Colunas: {col_names}")
            for row in rows:
                print(f"    {row}")
        else:
            print("  [AVISO] TABELA VAZIA!")
            resultado['dados'] = []
    except Exception as e:
        print(f"  [ERRO] {e}")
        resultado['dados'] = []

    # 3. Meios de pagamento (cartões)
    print("\n3. MEIOS DE PAGAMENTO (CARTOES):")
    print("-"*70)
    try:
        cursor.execute("SELECT nome FROM meios_pagamento WHERE nome LIKE '%Cartão%' OR nome LIKE '%cartão%' OR nome LIKE '%Cartao%'")
        cartoes = cursor.fetchall()
        resultado['cartoes'] = cartoes
        if cartoes:
            print(f"  Total: {len(cartoes)}")
            for cartao in cartoes:
                print(f"    - {cartao[0]}")
        else:
            print("  [AVISO] Nenhum cartao encontrado")
    except Exception as e:
        print(f"  [ERRO] {e}")
        resultado['cartoes'] = []

    conn.close()
    return resultado


# Verificar ambos os bancos
flask_result = verificar_fechamento(db_flask, "FLASK (exportado da aplicacao web)")
desktop_result = verificar_fechamento(db_desktop, "DESKTOP (sistema_financeiro_v15.py)")

# Comparação
print(f"\n{'='*70}")
print("COMPARACAO ENTRE FLASK E DESKTOP")
print(f"{'='*70}")

if flask_result and desktop_result:
    print("\nCOLUNAS:")
    flask_cols = [col[1] for col in flask_result['colunas']]
    desktop_cols = [col[1] for col in desktop_result['colunas']]

    print(f"  Flask:   {flask_cols}")
    print(f"  Desktop: {desktop_cols}")

    faltando_flask = set(desktop_cols) - set(flask_cols)
    faltando_desktop = set(flask_cols) - set(desktop_cols)

    if faltando_flask:
        print(f"\n  [PROBLEMA] Colunas no Desktop que faltam no Flask: {faltando_flask}")
    if faltando_desktop:
        print(f"\n  [INFO] Colunas no Flask que faltam no Desktop: {faltando_desktop}")
    if not faltando_flask and not faltando_desktop:
        print(f"\n  [OK] Estrutura identica!")

    print("\nDADOS:")
    print(f"  Flask:   {len(flask_result['dados'])} registros")
    print(f"  Desktop: {len(desktop_result['dados'])} registros")

    if len(flask_result['dados']) == 0:
        print("\n  [PROBLEMA] Flask nao tem NENHUM fechamento cadastrado!")
        print("  SOLUCAO:")
        print("    1. Acesse: https://finan.receberbemevinhos.com.br/configuracao/cartoes")
        print("    2. Configure o fechamento de cada cartao")
        print("    3. Baixe novamente o arquivo financas.db")
    elif len(flask_result['dados']) < len(desktop_result['dados']):
        print(f"\n  [AVISO] Flask tem MENOS fechamentos que Desktop!")

print(f"\n{'='*70}")
print("VERIFICACAO CONCLUIDA")
print(f"{'='*70}")

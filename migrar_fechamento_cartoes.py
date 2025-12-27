# -*- coding: utf-8 -*-
"""
Script para migrar dados de fechamento_cartoes do Desktop para Flask/PostgreSQL

Lê os dados do banco SQLite do desktop e gera comandos SQL para inserir
no PostgreSQL do Flask.
"""
import sqlite3
import os
import sys

# Configurar encoding para UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Caminho do banco desktop
db_desktop = r'C:\Users\orlei\OneDrive\Área de Trabalho\Financas\bkp_0812\financas.db'

print("="*70)
print("MIGRACAO DE FECHAMENTO DE CARTOES")
print("Desktop SQLite -> Flask PostgreSQL")
print("="*70)

if not os.path.exists(db_desktop):
    print(f"\n[ERRO] Arquivo desktop nao encontrado: {db_desktop}")
    exit(1)

# Conectar ao banco desktop
conn = sqlite3.connect(db_desktop)
cursor = conn.cursor()

# Ler dados de fechamento_cartoes
print("\n1. Lendo dados do banco DESKTOP...")
print("-"*70)

try:
    cursor.execute("SELECT meio_pagamento, data_fechamento FROM fechamento_cartoes ORDER BY meio_pagamento")
    fechamentos = cursor.fetchall()

    if not fechamentos:
        print("[ERRO] Nenhum fechamento encontrado no banco desktop!")
        conn.close()
        exit(1)

    print(f"[OK] Encontrados {len(fechamentos)} fechamentos:")
    for f in fechamentos:
        print(f"  - {f[0]:30s} -> Dia {f[1]}")

except Exception as e:
    print(f"[ERRO] Falha ao ler dados: {e}")
    conn.close()
    exit(1)

conn.close()

# Gerar script SQL para PostgreSQL
print("\n2. Gerando script SQL para PostgreSQL...")
print("-"*70)

sql_commands = []

print("\n-- Script SQL para executar no Flask (PostgreSQL)")
print("-- Copie e cole os comandos abaixo no console Python do Flask\n")

print("# Importe os modelos necessarios")
print("from models import db, FechamentoCartao, MeioPagamento")
print("from app import app")
print()
print("# Execute dentro do contexto da aplicacao")
print("with app.app_context():")

for meio_nome, dia_fechamento in fechamentos:
    # Gerar comando Python/SQLAlchemy
    # Precisamos encontrar o meio_pagamento_id pelo nome
    # Como não temos dia_vencimento no desktop, vamos usar um padrão (10 dias após fechamento)
    dia_vencimento = (dia_fechamento + 10) % 31
    if dia_vencimento == 0:
        dia_vencimento = 1

    print(f"    # {meio_nome}")
    print(f"    meio = MeioPagamento.query.filter_by(nome='{meio_nome}').first()")
    print(f"    if meio:")
    print(f"        # Verificar se ja existe fechamento para este cartao")
    print(f"        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()")
    print(f"        if not existe:")
    print(f"            fechamento = FechamentoCartao(")
    print(f"                meio_pagamento_id=meio.id,")
    print(f"                dia_fechamento={dia_fechamento},")
    print(f"                dia_vencimento={dia_vencimento}  # Estimado: {dia_fechamento} + 10 dias")
    print(f"            )")
    print(f"            db.session.add(fechamento)")
    print(f"            print(f'[OK] Adicionado: {meio_nome} - Fecha: {dia_fechamento}, Vence: {dia_vencimento}')")
    print(f"        else:")
    print(f"            print(f'[SKIP] Ja existe: {meio_nome}')")
    print(f"    else:")
    print(f"        print(f'[AVISO] Meio de pagamento nao encontrado: {meio_nome}')")
    print()

print("    # Salvar no banco")
print("    try:")
print("        db.session.commit()")
print("        print('[OK] Fechamentos salvos com sucesso!')")
print("    except Exception as e:")
print("        db.session.rollback()")
print("        print(f'[ERRO] Falha ao salvar: {e}')")

print("\n" + "="*70)
print("IMPORTANTE - DIAS DE VENCIMENTO")
print("="*70)
print("\nO banco desktop NAO tem a coluna 'dia_vencimento'.")
print("O script acima usa a formula: vencimento = fechamento + 10 dias")
print("\nVERIFIQUE os dias de vencimento na aplicacao Flask apos importar:")
print("https://finan.receberbemevinhos.com.br/configuracao/cartoes")
print("\nAjuste manualmente se necessario!")

print("\n" + "="*70)
print("COMO EXECUTAR")
print("="*70)
print("\n1. Conecte na VPS via SSH")
print("2. Ative o ambiente virtual:")
print("   cd /var/www/financeiro")
print("   source venv/bin/activate")
print("\n3. Abra o console Python:")
print("   python")
print("\n4. Copie e cole o script SQL gerado acima")
print("\n5. Verifique na aplicacao web se os fechamentos foram cadastrados")
print("\n6. Baixe novamente o arquivo financas.db")
print("\n" + "="*70)

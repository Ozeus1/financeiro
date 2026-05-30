"""
Migration: adiciona suporte ao nível ProMax
- users.modo_conta VARCHAR(10) DEFAULT 'pf'
- despesas.entidade VARCHAR(5) NULL
- receitas.entidade VARCHAR(5) NULL
"""
import os
import sys

# Adiciona o diretório flask ao path para importar app e models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask'))

from app import create_app
from models import db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            # users.modo_conta
            try:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN modo_conta VARCHAR(10) NOT NULL DEFAULT 'pf'"
                ))
                conn.commit()
                print("OK: users.modo_conta adicionado")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("SKIP: users.modo_conta ja existe")
                else:
                    print(f"ERRO users.modo_conta: {e}")

            # despesas.entidade
            try:
                conn.execute(text(
                    "ALTER TABLE despesas ADD COLUMN entidade VARCHAR(5)"
                ))
                conn.commit()
                print("OK: despesas.entidade adicionado")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("SKIP: despesas.entidade ja existe")
                else:
                    print(f"ERRO despesas.entidade: {e}")

            # receitas.entidade
            try:
                conn.execute(text(
                    "ALTER TABLE receitas ADD COLUMN entidade VARCHAR(5)"
                ))
                conn.commit()
                print("OK: receitas.entidade adicionado")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print("SKIP: receitas.entidade ja existe")
                else:
                    print(f"ERRO receitas.entidade: {e}")

        print("\nMigration concluida.")

if __name__ == '__main__':
    migrate()

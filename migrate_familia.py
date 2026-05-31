"""Migration: plano família — grupos, convites e novos campos"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask'))

from app import create_app
from models import db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            cmds = [
                # Tabela grupos_familia
                """CREATE TABLE IF NOT EXISTS grupos_familia (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL DEFAULT 'Minha Família',
                    assinante_id INTEGER NOT NULL,
                    data_criacao TIMESTAMP DEFAULT NOW(),
                    ativo BOOLEAN NOT NULL DEFAULT TRUE,
                    max_membros INTEGER NOT NULL DEFAULT 5
                )""",
                # Tabela convites_familia
                """CREATE TABLE IF NOT EXISTS convites_familia (
                    id SERIAL PRIMARY KEY,
                    grupo_id INTEGER NOT NULL REFERENCES grupos_familia(id),
                    email_convidado VARCHAR(120),
                    token VARCHAR(100) UNIQUE NOT NULL,
                    usado BOOLEAN NOT NULL DEFAULT FALSE,
                    data_criacao TIMESTAMP DEFAULT NOW(),
                    data_expiracao TIMESTAMP
                )""",
                # Colunas novas em users
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS grupo_familia_id INTEGER REFERENCES grupos_familia(id)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS eh_assinante_familia BOOLEAN NOT NULL DEFAULT FALSE",
                # Colunas novas em despesas
                "ALTER TABLE despesas ADD COLUMN IF NOT EXISTS registrado_por INTEGER REFERENCES users(id)",
                # Colunas novas em receitas
                "ALTER TABLE receitas ADD COLUMN IF NOT EXISTS registrado_por INTEGER REFERENCES users(id)",
            ]
            for cmd in cmds:
                try:
                    conn.execute(text(cmd))
                    conn.commit()
                    print(f"OK: {cmd[:60]}...")
                except Exception as e:
                    if 'already exists' in str(e).lower():
                        print(f"SKIP: já existe")
                    else:
                        print(f"ERRO: {e}")

        print("\nMigration família concluída.")

if __name__ == '__main__':
    migrate()

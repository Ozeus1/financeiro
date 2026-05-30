"""Migration: cria tabela assinaturas"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask'))

from app import create_app
from models import db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS assinaturas (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        plano VARCHAR(20) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'pendente',
                        valor FLOAT NOT NULL,
                        mp_payment_id VARCHAR(100),
                        mp_preference_id VARCHAR(200),
                        data_criacao TIMESTAMP DEFAULT NOW(),
                        data_aprovacao TIMESTAMP,
                        data_expiracao DATE
                    )
                """))
                conn.commit()
                print("OK: tabela assinaturas criada")
            except Exception as e:
                print(f"ERRO: {e}")

if __name__ == '__main__':
    migrate()

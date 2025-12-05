"""
WSGI Entry Point para Produção

Este arquivo é usado pelo Gunicorn para iniciar a aplicação Flask em produção.
"""
import os
from app import create_app
from models import db, populate_db

# Criar aplicação usando ambiente de produção
app = create_app('production')

# Inicializar banco de dados na primeira execução
with app.app_context():
    try:
        db.create_all()
        populate_db(app)
        print("✓ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"Nota: Tabelas já existem ou erro: {e}")

if __name__ == "__main__":
    app.run()

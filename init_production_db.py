#!/usr/bin/env python3
"""
Script para inicializar o banco de dados em produção

Uso:
    python init_production_db.py
"""
import sys
from app import create_app
from models import db, populate_db

def init_database():
    """Inicializa o banco de dados em produção"""
    print("=" * 60)
    print("INICIALIZANDO BANCO DE DADOS - PRODUÇÃO")
    print("=" * 60)

    try:
        # Criar aplicação em modo produção
        app = create_app('production')

        with app.app_context():
            # Verificar configuração do banco
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"\n✓ Conectando ao banco: {db_url.split('@')[1] if '@' in db_url else db_url}")

            # Criar todas as tabelas
            print("\n→ Criando tabelas no banco de dados...")
            db.create_all()
            print("✓ Tabelas criadas com sucesso!")

            # Popular com dados iniciais
            print("\n→ Populando banco com dados iniciais...")
            populate_db(app)
            print("✓ Dados iniciais inseridos!")

            print("\n" + "=" * 60)
            print("BANCO DE DADOS INICIALIZADO COM SUCESSO!")
            print("=" * 60)
            print("\nCredenciais padrão do administrador:")
            print("  Usuário: admin")
            print("  Senha: admin123")
            print("\n⚠️  IMPORTANTE: Altere a senha do admin após o primeiro login!")
            print("=" * 60)

            return True

    except Exception as e:
        print(f"\n❌ ERRO ao inicializar banco de dados: {e}")
        print("\nVerifique se:")
        print("  1. PostgreSQL está rodando")
        print("  2. As credenciais no arquivo .env estão corretas")
        print("  3. O banco de dados especificado existe")
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)

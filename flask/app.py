from flask import Flask
from flask_login import LoginManager
from config import config
from models import db, init_db, User
import os

def create_app(config_name='default'):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)

    # Carregar configurações
    app.config.from_object(config[config_name])

    # Pasta de upload de fotos de perfil
    upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'perfil')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_PERFIL_FOLDER'] = upload_folder
    app.config['ALLOWED_PHOTO_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'webp'}
    
    # Inicializar extensões
    init_db(app)
    
    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Filtro customizado para formatar valores monetários com separador de milhares
    @app.template_filter('moeda')
    def formatar_moeda(valor):
        """Formata valor como moeda brasileira com separador de milhares"""
        try:
            valor_float = float(valor)
            # Formatar com 2 casas decimais e separador de milhares
            valor_formatado = f"{valor_float:,.2f}"
            # Trocar . por , e , por .
            valor_formatado = valor_formatado.replace(',', 'X').replace('.', ',').replace('X', '.')
            return valor_formatado
        except (ValueError, TypeError):
            return "0,00"

    # Migração automática
    with app.app_context():
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                for col, col_type in [('nome', 'VARCHAR(150)'), ('whatsapp', 'VARCHAR(20)'), ('foto_perfil', 'VARCHAR(255)')]:
                    conn.execute(text(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {col_type}'))
                conn.execute(text('CREATE TABLE IF NOT EXISTS config_sistema (id SERIAL PRIMARY KEY, chave VARCHAR(80) UNIQUE NOT NULL, valor TEXT)'))
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS api_keys (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                        key_hash VARCHAR(64) NOT NULL UNIQUE,
                        key_prefix VARCHAR(16) NOT NULL,
                        descricao VARCHAR(200),
                        ativo BOOLEAN NOT NULL DEFAULT TRUE,
                        data_criacao TIMESTAMP DEFAULT NOW(),
                        data_ultimo_uso TIMESTAMP,
                        total_requests INTEGER NOT NULL DEFAULT 0
                    )
                '''))
                # Renomear nivel_acesso 'usuario' → 'pro'
                conn.execute(text(
                    "UPDATE users SET nivel_acesso = 'pro' WHERE nivel_acesso = 'usuario'"
                ))
                # Novos campos de CPF e confirmação de e-mail
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS cpf VARCHAR(11) UNIQUE"
                ))
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_confirmado BOOLEAN NOT NULL DEFAULT FALSE"
                ))
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS token_confirmacao VARCHAR(200)"
                ))
                # Admin e usuários existentes já confirmados
                conn.execute(text(
                    "UPDATE users SET email_confirmado = TRUE WHERE email_confirmado = FALSE AND ativo = TRUE"
                ))
                # Tabelas do módulo Investimentos (Pro/ProMax)
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS invest_renda_fixa (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        category VARCHAR(20) NOT NULL,
                        product_type VARCHAR(20),
                        institution VARCHAR(50) NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        value FLOAT NOT NULL DEFAULT 0,
                        rate VARCHAR(50),
                        maturity_date DATE
                    )
                '''))
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS invest_fundo (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        institution VARCHAR(50) NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        value FLOAT NOT NULL DEFAULT 0,
                        indexer VARCHAR(20),
                        maturity_date DATE
                    )
                '''))
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS invest_cripto (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        institution VARCHAR(50) NOT NULL,
                        name VARCHAR(50) NOT NULL,
                        quantity FLOAT,
                        avg_price FLOAT DEFAULT 0,
                        invested_value FLOAT,
                        current_value FLOAT NOT NULL DEFAULT 0,
                        quote FLOAT
                    )
                '''))
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS invest_previdencia (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        institution VARCHAR(50) NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        value FLOAT NOT NULL DEFAULT 0,
                        type VARCHAR(20),
                        certificate VARCHAR(50)
                    )
                '''))
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS invest_internacional (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        institution VARCHAR(50) NOT NULL,
                        name VARCHAR(20) NOT NULL,
                        quantity FLOAT,
                        avg_price FLOAT,
                        quote FLOAT,
                        value_usd FLOAT NOT NULL DEFAULT 0,
                        rate_usd FLOAT,
                        category VARCHAR(10) DEFAULT 'RV',
                        invested_value FLOAT,
                        current_price FLOAT,
                        daily_change FLOAT DEFAULT 0,
                        description VARCHAR(100)
                    )
                '''))
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS invest_ativo (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        ticker VARCHAR(10) NOT NULL,
                        type VARCHAR(10) NOT NULL,
                        strategy VARCHAR(10) NOT NULL DEFAULT 'HOLDER',
                        quantity INTEGER NOT NULL DEFAULT 0,
                        avg_price FLOAT NOT NULL DEFAULT 0,
                        current_price FLOAT DEFAULT 0,
                        daily_change FLOAT DEFAULT 0,
                        last_update TIMESTAMP,
                        last_dividend FLOAT,
                        last_dividend_date DATE,
                        dividend_yield FLOAT,
                        entry_date DATE,
                        fii_type VARCHAR(50),
                        sector VARCHAR(50)
                    )
                '''))
                conn.commit()
        except Exception:
            pass

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.despesas import despesas_bp
    from routes.receitas import receitas_bp
    from routes.configuracao import config_bp
    from routes.relatorios import relatorios_bp
    from routes.fluxo_caixa import fluxo_caixa_bp
    from routes.upload_database import bp as upload_database_bp
    from routes.api_v1 import api_bp
    from routes.assinatura import assinatura_bp
    from routes.familia import familia_bp
    from routes.investimentos import investimentos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(assinatura_bp)
    app.register_blueprint(familia_bp)
    app.register_blueprint(despesas_bp, url_prefix='/despesas')
    app.register_blueprint(receitas_bp, url_prefix='/receitas')
    app.register_blueprint(config_bp, url_prefix='/configuracao')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(fluxo_caixa_bp)
    app.register_blueprint(upload_database_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(investimentos_bp, url_prefix='/investimentos')
    
    return app

if __name__ == '__main__':
    # Obter ambiente da variável de ambiente ou usar 'development'
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)
    app.run(host='0.0.0.0', port=5000, debug=True)

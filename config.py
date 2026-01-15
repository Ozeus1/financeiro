import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações base da aplicação"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/financeiro'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de Banco de Dados (Resiliência)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    # Configurações de paginação
    ITEMS_PER_PAGE = 20
    
    # Configurações de locale para formatação de moeda
    LOCALE = 'pt_BR.UTF-8'
    CURRENCY_SYMBOL = 'R$'
    
    # Pluggy OpenFinance Configuration
    PLUGGY_CLIENT_ID = os.environ.get('PLUGGY_CLIENT_ID')
    PLUGGY_CLIENT_SECRET = os.environ.get('PLUGGY_CLIENT_SECRET')

class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Configurações para ambiente de produção"""
    DEBUG = False
    FLASK_ENV = 'production'

class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

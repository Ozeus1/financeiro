#!/usr/bin/env python3
"""
Script de configuração automática do PostgreSQL para produção
Execute este script no servidor VPS com: sudo python3 setup_production.py
"""

import os
import sys
import secrets
import string
import subprocess
from pathlib import Path

def gerar_senha_forte(tamanho=20):
    """Gera uma senha forte aleatória"""
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(caracteres) for _ in range(tamanho))

def gerar_secret_key(tamanho=50):
    """Gera uma SECRET_KEY para Flask"""
    return secrets.token_hex(tamanho)

def executar_comando(comando, shell=True):
    """Executa um comando e retorna o resultado"""
    try:
        resultado = subprocess.run(
            comando,
            shell=shell,
            capture_output=True,
            text=True,
            check=True
        )
        return True, resultado.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def verificar_postgres_instalado():
    """Verifica se o PostgreSQL está instalado"""
    print("🔍 Verificando instalação do PostgreSQL...")
    sucesso, _ = executar_comando("which psql")
    if sucesso:
        print("✓ PostgreSQL está instalado")
        return True
    else:
        print("✗ PostgreSQL não encontrado")
        return False

def criar_banco_e_usuario(db_name, db_user, db_password):
    """Cria o banco de dados e usuário no PostgreSQL"""
    print(f"\n📦 Criando banco de dados '{db_name}' e usuário '{db_user}'...")

    # SQL para criar usuário e banco
    sql_commands = f"""
-- Criar usuário se não existir
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '{db_user}') THEN
        CREATE USER {db_user} WITH PASSWORD '{db_password}';
    END IF;
END
$$;

-- Criar banco se não existir
SELECT 'CREATE DATABASE {db_name} OWNER {db_user}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{db_name}')\\gexec

-- Conectar ao banco e dar privilégios
\\c {db_name}
GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};
GRANT ALL ON SCHEMA public TO {db_user};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {db_user};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {db_user};
"""

    # Salvar SQL em arquivo temporário
    sql_file = "/tmp/setup_db.sql"
    with open(sql_file, 'w') as f:
        f.write(sql_commands)

    # Executar SQL como usuário postgres
    sucesso, saida = executar_comando(f"sudo -u postgres psql -f {sql_file}")

    # Remover arquivo temporário
    os.remove(sql_file)

    if sucesso:
        print("✓ Banco de dados e usuário criados com sucesso")
        return True
    else:
        print(f"✗ Erro ao criar banco: {saida}")
        return False

def criar_arquivo_env(db_name, db_user, db_password, db_host="localhost", db_port="5432"):
    """Cria o arquivo .env de produção"""
    print("\n📝 Criando arquivo .env de produção...")

    secret_key = gerar_secret_key()

    env_content = f"""# Configurações de Produção - Sistema Financeiro
# Gerado automaticamente em {os.popen('date').read().strip()}

# Flask
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY={secret_key}

# Database PostgreSQL
DATABASE_URL=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}
DB_TYPE=postgresql
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}

# Configurações da aplicação
DEBUG=False
TESTING=False

# Sessão
SESSION_TYPE=filesystem
PERMANENT_SESSION_LIFETIME=3600

# Upload
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=/var/www/financeiro/uploads

# Logs
LOG_LEVEL=INFO
LOG_FILE=/var/log/financeiro/app.log
"""

    # Determinar caminho do projeto
    caminho_atual = os.getcwd()
    env_path = os.path.join(caminho_atual, '.env')

    # Fazer backup se já existir
    if os.path.exists(env_path):
        backup_path = f"{env_path}.backup"
        print(f"⚠️  Arquivo .env existente. Criando backup em {backup_path}")
        os.rename(env_path, backup_path)

    # Criar novo arquivo .env
    with open(env_path, 'w') as f:
        f.write(env_content)

    # Definir permissões seguras (apenas owner pode ler/escrever)
    os.chmod(env_path, 0o600)

    print(f"✓ Arquivo .env criado em: {env_path}")
    print(f"✓ Permissões configuradas (600)")

    return env_path

def testar_conexao(db_name, db_user, db_password, db_host="localhost", db_port="5432"):
    """Testa a conexão com o banco de dados"""
    print("\n🔌 Testando conexão com o banco de dados...")

    comando = f"PGPASSWORD='{db_password}' psql -h {db_host} -p {db_port} -U {db_user} -d {db_name} -c '\\dt'"
    sucesso, saida = executar_comando(comando)

    if sucesso:
        print("✓ Conexão bem-sucedida!")
        return True
    else:
        print(f"✗ Erro na conexão: {saida}")
        return False

def criar_diretorios_necessarios():
    """Cria diretórios necessários para a aplicação"""
    print("\n📁 Criando diretórios necessários...")

    diretorios = [
        '/var/www/financeiro/uploads',
        '/var/log/financeiro'
    ]

    for diretorio in diretorios:
        try:
            os.makedirs(diretorio, exist_ok=True)
            print(f"✓ Diretório criado: {diretorio}")
        except PermissionError:
            print(f"⚠️  Execute com sudo para criar: {diretorio}")
            executar_comando(f"sudo mkdir -p {diretorio}")
            print(f"✓ Diretório criado: {diretorio}")

def main():
    print("=" * 60)
    print("  SETUP AUTOMÁTICO - SISTEMA FINANCEIRO (PRODUÇÃO)")
    print("=" * 60)

    # Verificar se está rodando como root/sudo
    if os.geteuid() != 0:
        print("\n⚠️  ATENÇÃO: Este script precisa ser executado com sudo!")
        print("Execute: sudo python3 setup_production.py")
        sys.exit(1)

    # Verificar PostgreSQL
    if not verificar_postgres_instalado():
        print("\n⚠️  Instale o PostgreSQL primeiro:")
        print("sudo apt update && sudo apt install postgresql postgresql-contrib -y")
        sys.exit(1)

    # Configurações
    DB_NAME = "financeiro"
    DB_USER = "financeiro_user"
    DB_PASSWORD = gerar_senha_forte()
    DB_HOST = "localhost"
    DB_PORT = "5432"

    print(f"\n📋 Configurações:")
    print(f"   Banco de dados: {DB_NAME}")
    print(f"   Usuário: {DB_USER}")
    print(f"   Senha: {DB_PASSWORD}")
    print(f"   Host: {DB_HOST}")
    print(f"   Porta: {DB_PORT}")

    resposta = input("\n❓ Deseja continuar? (s/n): ")
    if resposta.lower() != 's':
        print("❌ Setup cancelado")
        sys.exit(0)

    # Executar setup
    sucesso = True

    # 1. Criar banco e usuário
    if not criar_banco_e_usuario(DB_NAME, DB_USER, DB_PASSWORD):
        sucesso = False

    # 2. Criar arquivo .env
    if sucesso:
        env_path = criar_arquivo_env(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

    # 3. Testar conexão
    if sucesso:
        if not testar_conexao(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT):
            sucesso = False

    # 4. Criar diretórios
    if sucesso:
        criar_diretorios_necessarios()

    # Resultado final
    print("\n" + "=" * 60)
    if sucesso:
        print("✅ SETUP CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"\n📝 Credenciais do banco (GUARDE COM SEGURANÇA):")
        print(f"   Database: {DB_NAME}")
        print(f"   User: {DB_USER}")
        print(f"   Password: {DB_PASSWORD}")
        print(f"   Connection String: postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        print(f"\n📄 Arquivo .env criado em: {env_path}")
        print("\n🚀 Próximos passos:")
        print("   1. Copie o arquivo .env para o servidor")
        print("   2. Execute: pip install -r requirements.txt")
        print("   3. Inicialize o banco: python init_production_db.py")
        print("   4. Inicie a aplicação: gunicorn -c gunicorn_config.py wsgi:app")
    else:
        print("❌ SETUP FALHOU - Verifique os erros acima")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()

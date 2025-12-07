"""
Script de Migração: Adicionar user_id às Tabelas Compartilhadas
Executa migração para isolar dados por usuário
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def confirm_migration():
    """Solicita confirmação do usuário antes de prosseguir"""
    print("=" * 70)
    print("MIGRAÇÃO: Adicionar user_id às Tabelas Compartilhadas")
    print("=" * 70)
    print()
    print("Esta migração irá:")
    print("  1. Adicionar coluna user_id em categorias_despesa, categorias_receita,")
    print("     meios_pagamento e meios_recebimento")
    print("  2. Migrar todos os dados existentes para user_id = 1 (admin)")
    print("  3. Alterar constraints UNIQUE para permitir duplicatas entre usuários")
    print()
    print("⚠️  IMPORTANTE:")
    print("  - Faça backup do banco ANTES de prosseguir!")
    print("  - Este script altera a estrutura do banco de dados")
    print("  - Todos os dados existentes serão atribuídos ao usuário admin (id=1)")
    print()

    resposta = input("Você fez backup e deseja continuar? (digite 'SIM' para confirmar): ")
    return resposta.strip().upper() == 'SIM'

def get_database_url():
    """Obtém a URL do banco de dados"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ Erro: DATABASE_URL não encontrada no arquivo .env")
        sys.exit(1)
    return db_url

def executar_migracao():
    """Executa a migração do banco de dados"""

    # Confirmar
    if not confirm_migration():
        print("\n❌ Migração cancelada pelo usuário")
        return False

    # Conectar ao banco
    db_url = get_database_url()
    print(f"\n🔗 Conectando ao banco de dados...")

    try:
        engine = create_engine(db_url)
        conn = engine.connect()
        print("✅ Conexão estabelecida\n")
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return False

    try:
        # Iniciar transação
        trans = conn.begin()

        print("📊 Iniciando migração...\n")

        # ==== PASSO 1: Adicionar colunas user_id ====
        print("PASSO 1: Adicionando colunas user_id...")

        tabelas = [
            'categorias_despesa',
            'categorias_receita',
            'meios_pagamento',
            'meios_recebimento'
        ]

        for tabela in tabelas:
            print(f"  - Adicionando user_id em {tabela}...")
            conn.execute(text(f"""
                ALTER TABLE {tabela}
                ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
            """))

        print("✅ Colunas user_id adicionadas\n")

        # ==== PASSO 2: Migrar dados existentes para admin ====
        print("PASSO 2: Migrando dados existentes para admin (user_id=1)...")

        for tabela in tabelas:
            print(f"  - Atualizando {tabela}...")
            result = conn.execute(text(f"""
                UPDATE {tabela} SET user_id = 1 WHERE user_id IS NULL
            """))
            print(f"    {result.rowcount} registros atualizados")

        print("✅ Dados migrados\n")

        # ==== PASSO 3: Tornar user_id NOT NULL ====
        print("PASSO 3: Tornando user_id obrigatório...")

        for tabela in tabelas:
            print(f"  - Alterando {tabela}...")
            conn.execute(text(f"""
                ALTER TABLE {tabela}
                ALTER COLUMN user_id SET NOT NULL
            """))

        print("✅ Colunas user_id agora são obrigatórias\n")

        # ==== PASSO 4: Remover constraints UNIQUE antigos ====
        print("PASSO 4: Removendo constraints UNIQUE antigos...")

        constraints_antigos = {
            'categorias_despesa': 'categorias_despesa_nome_key',
            'categorias_receita': 'categorias_receita_nome_key',
            'meios_pagamento': 'meios_pagamento_nome_key',
            'meios_recebimento': 'meios_recebimento_nome_key'
        }

        for tabela, constraint in constraints_antigos.items():
            print(f"  - Removendo {constraint}...")
            try:
                conn.execute(text(f"""
                    ALTER TABLE {tabela}
                    DROP CONSTRAINT IF EXISTS {constraint}
                """))
            except Exception as e:
                print(f"    ⚠️  Aviso: {e}")

        print("✅ Constraints antigos removidos\n")

        # ==== PASSO 5: Adicionar novos constraints UNIQUE compostos ====
        print("PASSO 5: Adicionando novos constraints UNIQUE compostos...")

        novos_constraints = {
            'categorias_despesa': '_categoria_despesa_usuario_uc',
            'categorias_receita': '_categoria_receita_usuario_uc',
            'meios_pagamento': '_meio_pagamento_usuario_uc',
            'meios_recebimento': '_meio_recebimento_usuario_uc'
        }

        for tabela, constraint in novos_constraints.items():
            print(f"  - Adicionando {constraint}...")
            try:
                conn.execute(text(f"""
                    ALTER TABLE {tabela}
                    ADD CONSTRAINT {constraint} UNIQUE (nome, user_id)
                """))
            except Exception as e:
                print(f"    ⚠️  Erro: {e}")
                raise

        print("✅ Novos constraints adicionados\n")

        # ==== PASSO 6: Criar índices para performance ====
        print("PASSO 6: Criando índices para otimização de performance...")

        indices = {
            'categorias_despesa': 'idx_categoria_despesa_user',
            'categorias_receita': 'idx_categoria_receita_user',
            'meios_pagamento': 'idx_meio_pagamento_user',
            'meios_recebimento': 'idx_meio_recebimento_user'
        }

        for tabela, indice in indices.items():
            print(f"  - Criando índice {indice}...")
            try:
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS {indice} ON {tabela}(user_id)
                """))
            except Exception as e:
                print(f"    ⚠️  Aviso: {e}")

        print("✅ Índices criados\n")

        # ==== COMMIT ====
        print("💾 Confirmando alterações no banco...")
        trans.commit()
        print("✅ Migração concluída com sucesso!\n")

        # ==== RESUMO ====
        print("=" * 70)
        print("RESUMO DA MIGRAÇÃO")
        print("=" * 70)
        print("✅ Colunas user_id adicionadas em 4 tabelas")
        print("✅ Todos os dados existentes atribuídos ao admin (user_id=1)")
        print("✅ Constraints UNIQUE atualizados para permitir duplicatas entre usuários")
        print("✅ Índices criados para otimização")
        print()
        print("📌 PRÓXIMOS PASSOS:")
        print("  1. Reiniciar a aplicação Flask")
        print("  2. Criar novos usuários (dados padrão serão criados automaticamente)")
        print("  3. Testar isolamento de dados entre usuários")
        print("  4. Se necessário, duplicar categorias/meios para outros usuários")
        print()
        print("⚠️  NOTA: Gerentes e usuários comuns agora veem APENAS seus próprios dados")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ ERRO durante a migração: {e}")
        print("🔄 Revertendo alterações...")
        trans.rollback()
        print("✅ Alterações revertidas. Banco de dados não foi modificado.")
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    print()
    print(" ██████╗ ███╗   ███╗██╗ ██████╗ ██████╗  █████╗  ██████╗  █████╗  ██████╗ ")
    print("██╔════╝ ████╗ ████║██║██╔════╝ ██╔══██╗██╔══██╗██╔════╝ ██╔══██╗██╔═══██╗")
    print("██║  ███╗██╔████╔██║██║██║  ███╗██████╔╝███████║██║  ███╗███████║██║   ██║")
    print("██║   ██║██║╚██╔╝██║██║██║   ██║██╔══██╗██╔══██║██║   ██║██╔══██║██║   ██║")
    print("╚██████╔╝██║ ╚═╝ ██║██║╚██████╔╝██║  ██║██║  ██║╚██████╔╝██║  ██║╚██████╔╝")
    print(" ╚═════╝ ╚═╝     ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ")
    print()

    sucesso = executar_migracao()
    sys.exit(0 if sucesso else 1)

"""
Rota para Upload e Importação de Banco de Dados SQLite
Permite enviar o banco desktop (SQLite) e importar para PostgreSQL
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Despesa, Orcamento, CategoriaDespesa, MeioPagamento
import sqlite3
import os
from datetime import datetime
import tempfile

bp = Blueprint('upload_database', __name__, url_prefix='/config')

ALLOWED_EXTENSIONS = {'db', 'sqlite', 'sqlite3'}

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload_database', methods=['GET', 'POST'])
@login_required
def upload_database():
    """Interface para upload do banco de dados"""
    # Verificar se é admin
    if not current_user.is_admin:
        flash('Apenas administradores podem fazer upload de banco de dados.', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Verificar se o arquivo foi enviado
        if 'database_file' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400

        file = request.files['database_file']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Tipo de arquivo não permitido. Use .db, .sqlite ou .sqlite3'}), 400

        # Obter modo de importação
        modo = request.form.get('modo', 'parcial')

        try:
            # Salvar arquivo temporariamente
            temp_dir = tempfile.gettempdir()
            filename = secure_filename(file.filename)
            temp_path = os.path.join(temp_dir, f'upload_{datetime.now().strftime("%Y%m%d%H%M%S")}_{filename}')
            file.save(temp_path)

            # Importar dados
            resultado = importar_sqlite_para_postgres(temp_path, current_user.id, modo)

            # Remover arquivo temporário
            os.remove(temp_path)

            if resultado['success']:
                flash(f"✓ Importação concluída! {resultado['importadas']} despesas importadas.", 'success')
                return jsonify(resultado), 200
            else:
                flash(f"✗ Erro na importação: {resultado['error']}", 'error')
                return jsonify(resultado), 500

        except Exception as e:
            # Limpar arquivo temporário em caso de erro
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return jsonify({'success': False, 'error': str(e)}), 500

    # GET - Mostrar formulário
    return render_template('config/upload_database.html')

def importar_sqlite_para_postgres(sqlite_path, user_id, modo='parcial'):
    """
    Importa dados do SQLite para PostgreSQL

    Args:
        sqlite_path: Caminho do arquivo SQLite
        user_id: ID do usuário para associar os dados
        modo: 'parcial' (adicionar) ou 'total' (substituir)

    Returns:
        Dict com resultado da importação
    """
    try:
        # Conectar ao SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()

        # Verificar se é um banco válido
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='despesas'")
        if not sqlite_cursor.fetchone():
            return {'success': False, 'error': 'Arquivo não é um banco de dados válido (tabela despesas não encontrada)'}

        # Se modo total, limpar dados do usuário
        if modo == 'total':
            Despesa.query.filter_by(user_id=user_id).delete()
            Orcamento.query.filter_by(user_id=user_id).delete()
            db.session.commit()

        # Importar despesas
        sqlite_cursor.execute("""
            SELECT descricao, meio_pagamento, conta_despesa, valor,
                   num_parcelas, data_registro, data_pagamento
            FROM despesas
            ORDER BY data_registro
        """)

        importadas = 0
        erros = 0
        erros_detalhes = []

        for row in sqlite_cursor.fetchall():
            try:
                descricao, meio_pagamento_nome, categoria_nome, valor, num_parcelas, data_registro, data_pagamento = row

                # Obter ou criar categoria
                categoria = CategoriaDespesa.query.filter_by(nome=categoria_nome, user_id=user_id).first()
                if not categoria:
                    categoria = CategoriaDespesa(nome=categoria_nome, ativo=True, user_id=user_id)
                    db.session.add(categoria)
                    db.session.flush()

                # Obter ou criar meio de pagamento
                meio_pagamento = MeioPagamento.query.filter_by(nome=meio_pagamento_nome, user_id=user_id).first()
                if not meio_pagamento:
                    meio_pagamento = MeioPagamento(nome=meio_pagamento_nome, tipo='outros', ativo=True, user_id=user_id)
                    db.session.add(meio_pagamento)
                    db.session.flush()

                # Criar despesa
                despesa = Despesa(
                    descricao=descricao,
                    valor=float(valor),
                    num_parcelas=int(num_parcelas) if num_parcelas else 1,
                    data_registro=datetime.strptime(data_registro, '%Y-%m-%d').date() if data_registro else datetime.now().date(),
                    data_pagamento=datetime.strptime(data_pagamento, '%Y-%m-%d').date() if data_pagamento else None,
                    user_id=user_id,
                    categoria_id=categoria.id,
                    meio_pagamento_id=meio_pagamento.id
                )
                db.session.add(despesa)
                importadas += 1

            except Exception as e:
                erros += 1
                erros_detalhes.append(str(e))
                continue

        # Importar orçamentos
        try:
            sqlite_cursor.execute("SELECT conta_despesa, valor_orcado FROM orcamento")
            orcamentos = sqlite_cursor.fetchall()

            orcamentos_importados = 0
            for categoria_nome, valor_orcado in orcamentos:
                # Obter ou criar categoria
                categoria = CategoriaDespesa.query.filter_by(nome=categoria_nome, user_id=user_id).first()
                if not categoria:
                    categoria = CategoriaDespesa(nome=categoria_nome, ativo=True, user_id=user_id)
                    db.session.add(categoria)
                    db.session.flush()

                # Verificar se orçamento já existe
                orcamento = Orcamento.query.filter_by(
                    user_id=user_id,
                    categoria_id=categoria.id
                ).first()

                if orcamento:
                    orcamento.valor_orcado = float(valor_orcado)
                else:
                    orcamento = Orcamento(
                        user_id=user_id,
                        categoria_id=categoria.id,
                        valor_orcado=float(valor_orcado)
                    )
                    db.session.add(orcamento)

                orcamentos_importados += 1

        except Exception as e:
            # Se não existir tabela de orçamento, continuar
            orcamentos_importados = 0

        # Commit final
        db.session.commit()
        sqlite_conn.close()

        return {
            'success': True,
            'importadas': importadas,
            'erros': erros,
            'orcamentos': orcamentos_importados,
            'erros_detalhes': erros_detalhes[:10] if erros_detalhes else []
        }

    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }

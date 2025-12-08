from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from routes.auth import admin_required, gerente_required
from models import db, User, CategoriaDespesa, CategoriaReceita, MeioPagamento, MeioRecebimento, Orcamento, FechamentoCartao, Configuracao, Despesa, Receita, BalancoMensal, EventoCaixaAvulso
from utils.supabase_client import SupabaseClient
import json
from datetime import datetime
import os
import sqlite3
from datetime import datetime

config_bp = Blueprint('config', __name__)

def importar_sqlite_receitas(sqlite_path, user_id, modo='parcial'):
    """
    Importa dados de RECEITAS do SQLite desktop para PostgreSQL

    Args:
        sqlite_path: Caminho do arquivo SQLite (financas_receita.db)
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
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='receitas'")
        if not sqlite_cursor.fetchone():
            return {'sucesso': False, 'erro': 'Arquivo não é um banco de receitas válido (tabela receitas não encontrada)'}

        # Descobrir quais colunas existem na tabela
        sqlite_cursor.execute("PRAGMA table_info(receitas)")
        colunas_info = sqlite_cursor.fetchall()
        colunas_disponiveis = [col[1] for col in colunas_info]  # col[1] é o nome da coluna

        # Determinar nome da coluna de categoria (pode variar)
        coluna_categoria = None
        for possivel_nome in ['categoria_receita', 'categoria', 'conta_receita']:
            if possivel_nome in colunas_disponiveis:
                coluna_categoria = possivel_nome
                break

        if not coluna_categoria:
            return {'sucesso': False, 'erro': f'Coluna de categoria não encontrada. Colunas disponíveis: {", ".join(colunas_disponiveis)}'}

        # Determinar nome da coluna de meio de recebimento (pode variar)
        coluna_meio = None
        for possivel_nome in ['meio_recebimento', 'meio', 'forma_recebimento']:
            if possivel_nome in colunas_disponiveis:
                coluna_meio = possivel_nome
                break

        if not coluna_meio:
            return {'sucesso': False, 'erro': f'Coluna de meio de recebimento não encontrada. Colunas disponíveis: {", ".join(colunas_disponiveis)}'}

        # Se modo total, limpar dados do usuário
        if modo == 'total':
            Receita.query.filter_by(user_id=user_id).delete()
            db.session.commit()

        # Montar query dinamicamente com os nomes corretos das colunas
        query = f"""
            SELECT descricao, {coluna_meio}, {coluna_categoria}, valor,
                   num_parcelas, data_registro, data_recebimento
            FROM receitas
            ORDER BY data_registro
        """
        sqlite_cursor.execute(query)

        receitas_importadas = 0
        categorias_criadas = 0
        meios_criados = 0
        erros = 0

        for row in sqlite_cursor.fetchall():
            try:
                descricao, meio_recebimento_nome, categoria_nome, valor, num_parcelas, data_registro, data_recebimento = row

                # Obter ou criar categoria
                categoria = CategoriaReceita.query.filter_by(nome=categoria_nome, user_id=user_id).first()
                if not categoria:
                    categoria = CategoriaReceita(nome=categoria_nome, ativo=True, user_id=user_id)
                    db.session.add(categoria)
                    db.session.flush()
                    categorias_criadas += 1

                # Obter ou criar meio de recebimento
                meio_recebimento = MeioRecebimento.query.filter_by(nome=meio_recebimento_nome, user_id=user_id).first()
                if not meio_recebimento:
                    meio_recebimento = MeioRecebimento(nome=meio_recebimento_nome, tipo='outros', ativo=True, user_id=user_id)
                    db.session.add(meio_recebimento)
                    db.session.flush()
                    meios_criados += 1

                # Criar receita
                receita = Receita(
                    descricao=descricao,
                    valor=float(valor),
                    num_parcelas=int(num_parcelas) if num_parcelas else 1,
                    data_registro=datetime.strptime(data_registro, '%Y-%m-%d').date() if data_registro else datetime.now().date(),
                    data_recebimento=datetime.strptime(data_recebimento, '%Y-%m-%d').date() if data_recebimento else None,
                    user_id=user_id,
                    categoria_id=categoria.id,
                    meio_recebimento_id=meio_recebimento.id
                )
                db.session.add(receita)
                receitas_importadas += 1

            except Exception as e:
                erros += 1
                continue

        # Commit final
        db.session.commit()
        sqlite_conn.close()

        return {
            'sucesso': True,
            'receitas': receitas_importadas,
            'categorias': categorias_criadas,
            'meios_recebimento': meios_criados,
            'erros': erros
        }

    except Exception as e:
        db.session.rollback()
        return {
            'sucesso': False,
            'erro': str(e)
        }

def importar_sqlite_fluxo_caixa(sqlite_path, user_id, modo='parcial'):
    """
    Importa dados de FLUXO DE CAIXA do SQLite desktop para PostgreSQL

    Args:
        sqlite_path: Caminho do arquivo SQLite (fluxo_caixa.db)
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
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [row[0] for row in sqlite_cursor.fetchall()]

        if 'balanco_mensal' not in tabelas and 'eventos_caixa_avulsos' not in tabelas:
            return {'sucesso': False, 'erro': 'Arquivo não é um banco de fluxo de caixa válido (tabelas não encontradas)'}

        # Se modo total, limpar dados do usuário
        if modo == 'total':
            BalancoMensal.query.filter_by(user_id=user_id).delete()
            EventoCaixaAvulso.query.filter_by(user_id=user_id).delete()
            db.session.commit()

        balancos_importados = 0
        eventos_importados = 0
        erros = 0

        # Importar balanços mensais
        if 'balanco_mensal' in tabelas:
            try:
                sqlite_cursor.execute("""
                    SELECT ano, mes, total_entradas, total_saidas, saldo_mes, observacoes
                    FROM balanco_mensal
                    ORDER BY ano, mes
                """)

                for row in sqlite_cursor.fetchall():
                    try:
                        ano, mes, total_entradas, total_saidas, saldo_mes, observacoes = row

                        # Verificar se já existe (apenas em modo parcial)
                        if modo == 'parcial':
                            balanco_existente = BalancoMensal.query.filter_by(
                                user_id=user_id,
                                ano=ano,
                                mes=mes
                            ).first()

                            if balanco_existente:
                                # Atualizar valores
                                balanco_existente.total_entradas = float(total_entradas) if total_entradas else 0.0
                                balanco_existente.total_saidas = float(total_saidas) if total_saidas else 0.0
                                balanco_existente.saldo_mes = float(saldo_mes) if saldo_mes else 0.0
                                balanco_existente.observacoes = observacoes
                                balancos_importados += 1
                                continue

                        # Criar novo balanço
                        balanco = BalancoMensal(
                            ano=int(ano),
                            mes=int(mes),
                            total_entradas=float(total_entradas) if total_entradas else 0.0,
                            total_saidas=float(total_saidas) if total_saidas else 0.0,
                            saldo_mes=float(saldo_mes) if saldo_mes else 0.0,
                            observacoes=observacoes,
                            user_id=user_id
                        )
                        db.session.add(balanco)
                        balancos_importados += 1

                    except Exception as e:
                        erros += 1
                        continue

            except Exception as e:
                pass  # Tabela pode não existir ou estar vazia

        # Importar eventos de caixa avulsos
        if 'eventos_caixa_avulsos' in tabelas:
            try:
                sqlite_cursor.execute("""
                    SELECT data, descricao, valor
                    FROM eventos_caixa_avulsos
                    ORDER BY data
                """)

                for row in sqlite_cursor.fetchall():
                    try:
                        data_str, descricao, valor = row

                        # Criar evento
                        evento = EventoCaixaAvulso(
                            data=datetime.strptime(data_str, '%Y-%m-%d').date() if data_str else datetime.now().date(),
                            descricao=descricao,
                            valor=float(valor) if valor else 0.0,
                            user_id=user_id
                        )
                        db.session.add(evento)
                        eventos_importados += 1

                    except Exception as e:
                        erros += 1
                        continue

            except Exception as e:
                pass  # Tabela pode não existir ou estar vazia

        # Commit final
        db.session.commit()
        sqlite_conn.close()

        return {
            'sucesso': True,
            'balancos': balancos_importados,
            'eventos': eventos_importados,
            'erros': erros
        }

    except Exception as e:
        db.session.rollback()
        return {
            'sucesso': False,
            'erro': str(e)
        }

def importar_sqlite_desktop(sqlite_path, user_id, modo='parcial'):
    """
    Importa dados do SQLite desktop para PostgreSQL

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
            return {'sucesso': False, 'erro': 'Arquivo não é um banco de dados válido (tabela despesas não encontrada)'}

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

        despesas_importadas = 0
        categorias_criadas = 0
        meios_criados = 0
        erros = 0

        for row in sqlite_cursor.fetchall():
            try:
                descricao, meio_pagamento_nome, categoria_nome, valor, num_parcelas, data_registro, data_pagamento = row

                # Obter ou criar categoria
                categoria = CategoriaDespesa.query.filter_by(nome=categoria_nome, user_id=user_id).first()
                if not categoria:
                    categoria = CategoriaDespesa(nome=categoria_nome, ativo=True, user_id=user_id)
                    db.session.add(categoria)
                    db.session.flush()
                    categorias_criadas += 1

                # Obter ou criar meio de pagamento
                meio_pagamento = MeioPagamento.query.filter_by(nome=meio_pagamento_nome, user_id=user_id).first()
                if not meio_pagamento:
                    meio_pagamento = MeioPagamento(nome=meio_pagamento_nome, tipo='outros', ativo=True, user_id=user_id)
                    db.session.add(meio_pagamento)
                    db.session.flush()
                    meios_criados += 1

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
                despesas_importadas += 1

            except Exception as e:
                erros += 1
                continue

        # Importar orçamentos
        orcamentos_importados = 0
        try:
            sqlite_cursor.execute("SELECT conta_despesa, valor_orcado FROM orcamento")
            orcamentos = sqlite_cursor.fetchall()

            for categoria_nome, valor_orcado in orcamentos:
                # Obter ou criar categoria
                categoria = CategoriaDespesa.query.filter_by(nome=categoria_nome, user_id=user_id).first()
                if not categoria:
                    categoria = CategoriaDespesa(nome=categoria_nome, ativo=True, user_id=user_id)
                    db.session.add(categoria)
                    db.session.flush()
                    categorias_criadas += 1

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
            # Tabela de orçamento pode não existir
            pass

        # Commit final
        db.session.commit()
        sqlite_conn.close()

        return {
            'sucesso': True,
            'despesas': despesas_importadas,
            'orcamentos': orcamentos_importados,
            'categorias': categorias_criadas,
            'meios_pagamento': meios_criados,
            'erros': erros
        }

    except Exception as e:
        db.session.rollback()
        return {
            'sucesso': False,
            'erro': str(e)
        }

@config_bp.route('/importar-dados-antigos', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_dados_antigos():
    """Importar dados do sistema desktop (SQLite) para PostgreSQL (apenas admin)"""
    if request.method == 'POST':
        from flask import current_app
        import tempfile
        from werkzeug.utils import secure_filename

        # Verificar se é upload de arquivo ou seleção de arquivo local
        tipo_importacao = request.form.get('tipo_importacao', 'upload')

        if tipo_importacao == 'upload':
            # NOVO: Upload de arquivo SQLite do desktop
            tipo_banco = request.form.get('tipo_banco', 'despesas')  # 'despesas', 'receitas' ou 'fluxo_caixa'

            if tipo_banco == 'despesas':
                campo_arquivo = 'arquivo_sqlite_despesas'
            elif tipo_banco == 'receitas':
                campo_arquivo = 'arquivo_sqlite_receitas'
            else:  # fluxo_caixa
                campo_arquivo = 'arquivo_sqlite_fluxo_caixa'

            if campo_arquivo not in request.files:
                flash('Nenhum arquivo foi enviado!', 'warning')
                return redirect(url_for('config.importar_dados_antigos'))

            file = request.files[campo_arquivo]

            if file.filename == '':
                flash('Nenhum arquivo selecionado!', 'warning')
                return redirect(url_for('config.importar_dados_antigos'))

            if not file.filename.endswith(('.db', '.sqlite', '.sqlite3')):
                flash('Tipo de arquivo inválido! Use arquivos .db, .sqlite ou .sqlite3', 'danger')
                return redirect(url_for('config.importar_dados_antigos'))

            try:
                # Salvar arquivo temporariamente
                temp_dir = tempfile.gettempdir()
                filename = secure_filename(file.filename)
                temp_path = os.path.join(temp_dir, f'upload_{datetime.now().strftime("%Y%m%d%H%M%S")}_{filename}')
                file.save(temp_path)

                # Importar do arquivo SQLite
                modo = request.form.get('modo_importacao', 'parcial')

                if tipo_banco == 'despesas':
                    resultado = importar_sqlite_desktop(temp_path, current_user.id, modo)

                    if resultado['sucesso']:
                        flash(f"""✓ Importação de DESPESAS concluída!
                            Despesas: {resultado.get('despesas', 0)}
                            Orçamentos: {resultado.get('orcamentos', 0)}
                            Categorias criadas: {resultado.get('categorias', 0)}
                            Meios de Pagamento criados: {resultado.get('meios_pagamento', 0)}
                            {f"Erros: {resultado.get('erros', 0)}" if resultado.get('erros', 0) > 0 else ""}
                        """, 'success')
                    else:
                        flash(f"✗ Erro na importação: {resultado.get('erro', 'Erro desconhecido')}", 'danger')

                elif tipo_banco == 'receitas':
                    resultado = importar_sqlite_receitas(temp_path, current_user.id, modo)

                    if resultado['sucesso']:
                        flash(f"""✓ Importação de RECEITAS concluída!
                            Receitas: {resultado.get('receitas', 0)}
                            Categorias criadas: {resultado.get('categorias', 0)}
                            Meios de Recebimento criados: {resultado.get('meios_recebimento', 0)}
                            {f"Erros: {resultado.get('erros', 0)}" if resultado.get('erros', 0) > 0 else ""}
                        """, 'success')
                    else:
                        flash(f"✗ Erro na importação: {resultado.get('erro', 'Erro desconhecido')}", 'danger')

                else:  # fluxo_caixa
                    resultado = importar_sqlite_fluxo_caixa(temp_path, current_user.id, modo)

                    if resultado['sucesso']:
                        flash(f"""✓ Importação de FLUXO DE CAIXA concluída!
                            Balanços Mensais: {resultado.get('balancos', 0)}
                            Eventos de Caixa: {resultado.get('eventos', 0)}
                            {f"Erros: {resultado.get('erros', 0)}" if resultado.get('erros', 0) > 0 else ""}
                        """, 'success')
                    else:
                        flash(f"✗ Erro na importação: {resultado.get('erro', 'Erro desconhecido')}", 'danger')

                # Remover arquivo temporário
                os.remove(temp_path)

            except Exception as e:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
                flash(f'Erro ao processar arquivo: {str(e)}', 'danger')

            return redirect(url_for('config.importar_dados_antigos'))

        # Importação antiga (arquivos locais)
        from utils.importador import importar_dados_antigos, importar_fluxo_caixa

        # Obter caminhos dos arquivos selecionados
        caminho_financas = request.form.get('caminho_financas')
        caminho_receitas = request.form.get('caminho_receitas')
        caminho_fluxo_caixa = request.form.get('caminho_fluxo_caixa')
        
        # Verificar qual tipo de importação fazer
        if caminho_fluxo_caixa:
            # Importar fluxo de caixa
            if not os.path.exists(caminho_fluxo_caixa):
                flash(f'Arquivo de fluxo de caixa não encontrado: {caminho_fluxo_caixa}', 'danger')
                return redirect(url_for('config.importar_dados_antigos'))
            
            try:
                relatorio = importar_fluxo_caixa(
                    current_app._get_current_object(),
                    caminho_fluxo_caixa,
                    user_id=current_user.id
                )
                
                if relatorio['sucesso']:
                    flash(f"""Importação de Fluxo de Caixa concluída!
                        Balanços Mensais: {relatorio['balancos_mensais']}
                        Eventos de Caixa: {relatorio['eventos_caixa']}
                    """, 'success')
                else:
                    flash(f"Erro na importação: {'; '.join(relatorio['erros'])}", 'danger')
                    
            except Exception as e:
                flash(f'Erro ao importar fluxo de caixa: {str(e)}', 'danger')
                
        elif caminho_financas and caminho_receitas:
            # Importar despesas e receitas
            # Verificar se os arquivos foram selecionados
            if not caminho_financas or not caminho_receitas:
                flash('Por favor, selecione os arquivos de despesas e receitas para importar!', 'warning')
                return redirect(url_for('config.importar_dados_antigos'))
            
            # Verificar se os arquivos existem
            if not os.path.exists(caminho_financas):
                flash(f'Arquivo de despesas não encontrado: {caminho_financas}', 'danger')
                return redirect(url_for('config.importar_dados_antigos'))
            
            if not os.path.exists(caminho_receitas):
                flash(f'Arquivo de receitas não encontrado: {caminho_receitas}', 'danger')
                return redirect(url_for('config.importar_dados_antigos'))
            
            try:
                # Executar importação
                relatorio = importar_dados_antigos(
                    current_app._get_current_object(),
                    caminho_financas,
                    caminho_receitas,
                    user_id=current_user.id
                )
                
                if relatorio['sucesso']:
                    flash(f"""Importação concluída com sucesso!
                        Categorias de Despesa: {relatorio['categorias_despesa']}
                        Categorias de Receita: {relatorio['categorias_receita']}
                        Meios de Pagamento: {relatorio['meios_pagamento']}
                        Meios de Recebimento: {relatorio['meios_recebimento']}
                        Despesas: {relatorio['despesas']}
                        Receitas: {relatorio['receitas']}
                    """, 'success')
                else:
                    flash(f"Erro na importação: {'; '.join(relatorio['erros'])}", 'danger')
                    
            except Exception as e:
                flash(f'Erro ao importar dados: {str(e)}', 'danger')
        else:
            flash('Selecione arquivos para importar!', 'warning')
        
        return redirect(url_for('config.importar_dados_antigos'))
    
    # GET - mostrar formulário
    # Buscar todos os arquivos .db na pasta do projeto
    diretorio_atual = os.getcwd()
    arquivos_db = []
    
    try:
        for arquivo in os.listdir(diretorio_atual):
            if arquivo.endswith('.db'):
                caminho_completo = os.path.join(diretorio_atual, arquivo)
                tamanho = os.path.getsize(caminho_completo)
                tamanho_mb = tamanho / (1024 * 1024)
                
                # Determinar tipo do banco
                tipo = 'desconhecido'
                if 'receita' in arquivo.lower():
                    tipo = 'receitas'
                elif 'fluxo' in arquivo.lower() or 'caixa' in arquivo.lower():
                    tipo = 'fluxo_caixa'
                elif arquivo.startswith('financas') and 'receita' not in arquivo.lower():
                    tipo = 'despesas'
                elif arquivo == 'financeiro.db':
                    tipo = 'sistema_novo'
                
                arquivos_db.append({
                    'nome': arquivo,
                    'caminho': caminho_completo,
                    'tamanho_mb': tamanho_mb,
                    'tipo': tipo
                })
    except Exception as e:
        flash(f'Erro ao listar arquivos: {str(e)}', 'warning')
    
    # Ordenar: despesas primeiro, depois receitas, depois outros
    ordem_tipo = {'despesas': 0, 'receitas': 1, 'fluxo_caixa': 2, 'desconhecido': 3, 'sistema_novo': 4}
    arquivos_db.sort(key=lambda x: (ordem_tipo.get(x['tipo'], 99), x['nome']))
    
    return render_template('config/importar_dados.html', 
                         arquivos_db=arquivos_db,
                         total_arquivos=len(arquivos_db))

@config_bp.route('/categorias-despesa', methods=['GET', 'POST'])
@login_required
def categorias_despesa():
    """Gerenciar categorias de despesa"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'criar':
            nome = request.form.get('nome')
            if CategoriaDespesa.query.filter_by(nome=nome, user_id=current_user.id).first():
                flash('Categoria já existe.', 'warning')
            else:
                nova_categoria = CategoriaDespesa(nome=nome, ativo=True, user_id=current_user.id)
                db.session.add(nova_categoria)
                db.session.commit()
                flash('Categoria criada com sucesso!', 'success')
        
        elif action == 'editar':
            id = int(request.form.get('id'))
            nome = request.form.get('nome')
            categoria = CategoriaDespesa.query.filter_by(id=id, user_id=current_user.id).first()
            if categoria:
                categoria.nome = nome
                db.session.commit()
                flash('Categoria atualizada!', 'success')
        
        elif action == 'ativar_desativar':
            id = int(request.form.get('id'))
            categoria = CategoriaDespesa.query.filter_by(id=id, user_id=current_user.id).first()
            if categoria:
                categoria.ativo = not categoria.ativo
                db.session.commit()
                status = 'ativada' if categoria.ativo else 'desativada'
                flash(f'Categoria {status}!', 'success')

        return redirect(url_for('config.categorias_despesa'))

    categorias = CategoriaDespesa.query.filter_by(user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
    return render_template('config/categorias_despesa.html', categorias=categorias)

@config_bp.route('/categorias-receita', methods=['GET', 'POST'])
@login_required
def categorias_receita():
    """Gerenciar categorias de receita"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'criar':
            nome = request.form.get('nome')
            if CategoriaReceita.query.filter_by(nome=nome, user_id=current_user.id).first():
                flash('Categoria já existe.', 'warning')
            else:
                nova_categoria = CategoriaReceita(nome=nome, ativo=True, user_id=current_user.id)
                db.session.add(nova_categoria)
                db.session.commit()
                flash('Categoria criada com sucesso!', 'success')
        
        elif action == 'editar':
            id = int(request.form.get('id'))
            nome = request.form.get('nome')
            categoria = CategoriaReceita.query.filter_by(id=id, user_id=current_user.id).first()
            if categoria:
                categoria.nome = nome
                db.session.commit()
                flash('Categoria atualizada!', 'success')
        
        elif action == 'ativar_desativar':
            id = int(request.form.get('id'))
            categoria = CategoriaReceita.query.filter_by(id=id, user_id=current_user.id).first()
            if categoria:
                categoria.ativo = not categoria.ativo
                db.session.commit()
                status = 'ativada' if categoria.ativo else 'desativada'
                flash(f'Categoria {status}!', 'success')

        return redirect(url_for('config.categorias_receita'))

    categorias = CategoriaReceita.query.filter_by(user_id=current_user.id).order_by(CategoriaReceita.nome).all()
    return render_template('config/categorias_receita.html', categorias=categorias)

@config_bp.route('/meios-pagamento', methods=['GET', 'POST'])
@login_required
def meios_pagamento():
    """Gerenciar meios de pagamento"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'criar':
            nome = request.form.get('nome')
            tipo = request.form.get('tipo')
            if MeioPagamento.query.filter_by(nome=nome, user_id=current_user.id).first():
                flash('Meio de pagamento já existe.', 'warning')
            else:
                novo_meio = MeioPagamento(nome=nome, tipo=tipo, ativo=True, user_id=current_user.id)
                db.session.add(novo_meio)
                db.session.commit()
                flash('Meio de pagamento criado com sucesso!', 'success')
        
        elif action == 'editar':
            id = int(request.form.get('id'))
            nome = request.form.get('nome')
            tipo = request.form.get('tipo')
            meio = MeioPagamento.query.filter_by(id=id, user_id=current_user.id).first()
            if meio:
                meio.nome = nome
                meio.tipo = tipo
                db.session.commit()
                flash('Meio de pagamento atualizado!', 'success')
        
        elif action == 'ativar_desativar':
            id = int(request.form.get('id'))
            meio = MeioPagamento.query.filter_by(id=id, user_id=current_user.id).first()
            if meio:
                meio.ativo = not meio.ativo
                db.session.commit()
                status = 'ativado' if meio.ativo else 'desativado'
                flash(f'Meio de pagamento {status}!', 'success')

        return redirect(url_for('config.meios_pagamento'))

    meios = MeioPagamento.query.filter_by(user_id=current_user.id).order_by(MeioPagamento.nome).all()
    return render_template('config/meios_pagamento.html', meios=meios)

@config_bp.route('/meios-recebimento', methods=['GET', 'POST'])
@login_required
def meios_recebimento():
    """Gerenciar meios de recebimento"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'criar':
            nome = request.form.get('nome')
            if MeioRecebimento.query.filter_by(nome=nome, user_id=current_user.id).first():
                flash('Meio de recebimento já existe.', 'warning')
            else:
                novo_meio = MeioRecebimento(nome=nome, ativo=True, user_id=current_user.id)
                db.session.add(novo_meio)
                db.session.commit()
                flash('Meio de recebimento criado com sucesso!', 'success')
        
        elif action == 'editar':
            id = int(request.form.get('id'))
            nome = request.form.get('nome')
            meio = MeioRecebimento.query.filter_by(id=id, user_id=current_user.id).first()
            if meio:
                meio.nome = nome
                db.session.commit()
                flash('Meio de recebimento atualizado!', 'success')
        
        elif action == 'ativar_desativar':
            id = int(request.form.get('id'))
            meio = MeioRecebimento.query.filter_by(id=id, user_id=current_user.id).first()
            if meio:
                meio.ativo = not meio.ativo
                db.session.commit()
                status = 'ativado' if meio.ativo else 'desativado'
                flash(f'Meio de recebimento {status}!', 'success')

        return redirect(url_for('config.meios_recebimento'))

    meios = MeioRecebimento.query.filter_by(user_id=current_user.id).order_by(MeioRecebimento.nome).all()
    return render_template('config/meios_recebimento.html', meios=meios)

@config_bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
@admin_required
def usuarios():
    """Gerenciar usuários (apenas admin)"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'criar':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            nivel = request.form.get('nivel')
            data_validade_str = request.form.get('data_validade')

            if User.query.filter_by(username=username).first():
                flash('Nome de usuário já existe!', 'warning')
            elif User.query.filter_by(email=email).first():
                flash('E-mail já cadastrado!', 'warning')
            else:
                # Processar data de validade (apenas para usuários normais)
                data_validade = None
                if nivel != 'admin' and data_validade_str:
                    from datetime import datetime
                    data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date()

                novo_usuario = User(
                    username=username,
                    email=email,
                    nivel_acesso=nivel,
                    ativo=True,
                    data_validade=data_validade
                )
                novo_usuario.set_password(password)
                db.session.add(novo_usuario)
                db.session.commit()

                # Criar dados padrão
                from models import criar_dados_padrao_usuario
                criar_dados_padrao_usuario(novo_usuario)

                flash('Usuário criado com sucesso!', 'success')

        elif action == 'editar':
            id = int(request.form.get('id'))
            username = request.form.get('username')
            email = request.form.get('email')
            
            user = User.query.get(id)
            if user:
                # Verificar duplicidade apenas se mudou o valor
                if user.username != username and User.query.filter_by(username=username).first():
                    flash('Nome de usuário já existe!', 'warning')
                elif user.email != email and User.query.filter_by(email=email).first():
                    flash('E-mail já cadastrado!', 'warning')
                else:
                    user.username = username
                    user.email = email
                    db.session.commit()
                    flash('Dados do usuário atualizados!', 'success')

        elif action == 'alterar_senha':
            id = int(request.form.get('id'))
            password = request.form.get('password')
            
            user = User.query.get(id)
            if user:
                user.set_password(password)
                db.session.commit()
                flash('Senha alterada com sucesso!', 'success')

        elif action == 'ativar_desativar':
            id = int(request.form.get('id'))
            user = User.query.get(id)
            if user and user.id != current_user.id:  # Não pode desativar a si mesmo
                user.ativo = not user.ativo
                db.session.commit()
                status = 'ativado' if user.ativo else 'desativado'
                flash(f'Usuário {status}!', 'success')
            elif user and user.id == current_user.id:
                flash('Você não pode desativar sua própria conta!', 'danger')
        
        elif action == 'alterar_nivel':
            id = int(request.form.get('id'))
            nivel = request.form.get('nivel')
            user = User.query.get(id)
            if user and user.id != current_user.id:
                user.nivel_acesso = nivel
                # Se mudou para admin, remover data de validade
                if nivel == 'admin':
                    user.data_validade = None
                db.session.commit()
                flash('Nível de acesso alterado!', 'success')

        elif action == 'definir_validade':
            id = int(request.form.get('id'))
            data_validade_str = request.form.get('data_validade')
            user = User.query.get(id)

            if user and user.nivel_acesso != 'admin':
                # Se forneceu data, converter; senão, deixar None (sem limite)
                if data_validade_str:
                    from datetime import datetime
                    user.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date()
                else:
                    user.data_validade = None
                db.session.commit()

                if user.data_validade:
                    flash(f'Data de validade definida para {user.data_validade.strftime("%d/%m/%Y")}!', 'success')
                else:
                    flash('Prazo de validade removido (acesso ilimitado)!', 'success')
            elif user and user.nivel_acesso == 'admin':
                flash('Admin não pode ter data de validade!', 'warning')

        return redirect(url_for('config.usuarios'))
    
    usuarios = User.query.order_by(User.username).all()
    return render_template('config/usuarios.html', usuarios=usuarios)

@config_bp.route('/orcamento', methods=['GET', 'POST'])
@login_required
def orcamento():
    """Gerenciar orçamento geral por categoria"""
    if request.method == 'POST':
        action = request.form.get('action', 'salvar')
        
        if action == 'excluir':
            orcamento_id = int(request.form.get('orcamento_id'))
            orcamento = Orcamento.query.get(orcamento_id)
            if orcamento and orcamento.user_id == current_user.id:
                db.session.delete(orcamento)
                db.session.commit()
                flash('Orçamento excluído!', 'success')
            return redirect(url_for('config.orcamento'))
        
        categoria_id = int(request.form.get('categoria_id'))
        valor_orcado = float(request.form.get('valor_orcado').replace(',', '.'))
        
        # Verificar se já existe orçamento para esta categoria
        orcamento_existente = Orcamento.query.filter_by(
            categoria_id=categoria_id,
            user_id=current_user.id
        ).first()
        
        if orcamento_existente:
            orcamento_existente.valor_orcado = valor_orcado
            flash('Orçamento atualizado!', 'success')
        else:
            novo_orcamento = Orcamento(
                categoria_id=categoria_id,
                valor_orcado=valor_orcado,
                user_id=current_user.id
            )
            db.session.add(novo_orcamento)
            flash('Orçamento cadastrado!', 'success')
        
        db.session.commit()
        return redirect(url_for('config.orcamento'))
    
    categorias = CategoriaDespesa.query.filter_by(ativo=True, user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
    orcamentos = Orcamento.query.filter_by(user_id=current_user.id).all()

    return render_template('config/orcamento.html',
                          categorias=categorias,
                          orcamentos=orcamentos)

@config_bp.route('/cartoes', methods=['GET', 'POST'])
@login_required
def cartoes():
    """Configurar fechamento de cartões"""
    if request.method == 'POST':
        meio_pagamento_id = int(request.form.get('meio_pagamento_id'))
        dia_fechamento = int(request.form.get('dia_fechamento'))
        dia_vencimento = int(request.form.get('dia_vencimento'))
        
        # Verificar se já existe configuração para este cartão
        config_existente = FechamentoCartao.query.filter_by(meio_pagamento_id=meio_pagamento_id).first()
        
        if config_existente:
            config_existente.dia_fechamento = dia_fechamento
            config_existente.dia_vencimento = dia_vencimento
            flash('Configuração de cartão atualizada!', 'success')
        else:
            nova_config = FechamentoCartao(
                meio_pagamento_id=meio_pagamento_id,
                dia_fechamento=dia_fechamento,
                dia_vencimento=dia_vencimento
            )
            db.session.add(nova_config)
            flash('Configuração de cartão cadastrada!', 'success')
        
        db.session.commit()
        return redirect(url_for('config.cartoes'))
    
    # Buscar apenas meios de pagamento do tipo cartão
    cartoes = MeioPagamento.query.filter_by(tipo='cartao', ativo=True, user_id=current_user.id).order_by(MeioPagamento.nome).all()
    configuracoes = FechamentoCartao.query.all()

    return render_template('config/cartoes.html', cartoes=cartoes, configuracoes=configuracoes)


@config_bp.route('/importar-supabase', methods=['GET'])
@login_required
@admin_required
def importar_supabase():
    """Página de importação do Supabase"""
    # Buscar configurações salvas
    config_url = Configuracao.query.filter_by(chave='supabase_url').first()
    config_key = Configuracao.query.filter_by(chave='supabase_key').first()
    config_table = Configuracao.query.filter_by(chave='supabase_table').first()
    
    return render_template('config/importar_supabase.html',
                         supabase_url=config_url.valor if config_url else '',
                         supabase_key=config_key.valor if config_key else '',
                         supabase_table=config_table.valor if config_table else '')

@config_bp.route('/importar-supabase/salvar-config', methods=['POST'])
@login_required
@admin_required
def salvar_config_supabase():
    """Salvar configurações do Supabase"""
    try:
        data = request.get_json()
        url = data.get('url')
        key = data.get('key')
        table = data.get('table')
        
        configs = {
            'supabase_url': url,
            'supabase_key': key,
            'supabase_table': table
        }
        
        for chave, valor in configs.items():
            config = Configuracao.query.filter_by(chave=chave).first()
            if config:
                config.valor = valor
            else:
                new_config = Configuracao(chave=chave, valor=valor)
                db.session.add(new_config)
        
        db.session.commit()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'message': str(e)}

@config_bp.route('/importar-supabase/testar', methods=['POST'])
@login_required
@admin_required
def testar_conexao_supabase():
    """Testar conexão com Supabase"""
    try:
        data = request.get_json()
        client = SupabaseClient(data.get('url'), data.get('key'))
        result = client.test_connection(data.get('table'))
        return result
    except Exception as e:
        return {'success': False, 'message': str(e)}

@config_bp.route('/importar-supabase/buscar', methods=['POST'])
@login_required
@admin_required
def buscar_dados_supabase():
    """Buscar dados do Supabase"""
    try:
        data = request.get_json()
        client = SupabaseClient(data.get('url'), data.get('key'))
        result = client.fetch_data(data.get('table'))
        return result
    except Exception as e:
        return {'success': False, 'message': str(e)}

@config_bp.route('/importar-supabase/importar', methods=['POST'])
@login_required
@admin_required
def importar_dados_supabase():
    """Importar dados selecionados"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        config_data = data.get('config', {})
        
        client = SupabaseClient(config_data.get('url'), config_data.get('key'))
        table = config_data.get('table')
        
        importados = 0
        erros = []
        
        for item in items:
            try:
                # Verificar/Criar Categoria
                cat_nome = item.get('categoria', 'Outros')
                categoria = CategoriaDespesa.query.filter_by(nome=cat_nome, user_id=current_user.id).first()
                if not categoria:
                    categoria = CategoriaDespesa(nome=cat_nome, ativo=True, user_id=current_user.id)
                    db.session.add(categoria)
                    db.session.commit()
                
                # Verificar/Criar Meio de Pagamento
                mp_nome = item.get('meio_pagamento', 'Outros')
                meio_pagamento = MeioPagamento.query.filter_by(nome=mp_nome, user_id=current_user.id).first()
                if not meio_pagamento:
                    meio_pagamento = MeioPagamento(nome=mp_nome, tipo='outros', ativo=True, user_id=current_user.id)
                    db.session.add(meio_pagamento)
                    db.session.commit()
                
                # Criar Despesa
                valor_str = str(item.get('valor', '0'))
                # Remove thousand separator (.) and replace decimal separator (,) with (.)
                valor_str = valor_str.replace('.', '').replace(',', '.')
                valor = float(valor_str)
                
                # Converter data (assumindo formato YYYY-MM-DD ou DD/MM/YYYY)
                data_str = item.get('data_despesa')
                try:
                    if '/' in data_str:
                        data_despesa = datetime.strptime(data_str, '%d/%m/%Y').date()
                    else:
                        data_despesa = datetime.strptime(data_str, '%Y-%m-%d').date()
                except:
                    data_despesa = datetime.today().date()
                
                nova_despesa = Despesa(
                    descricao=item.get('descricao'),
                    valor=valor,
                    data_pagamento=data_despesa,
                    num_parcelas=int(item.get('parcelas', 1)),
                    categoria_id=categoria.id,
                    meio_pagamento_id=meio_pagamento.id,
                    user_id=current_user.id
                )
                db.session.add(nova_despesa)
                
                # Marcar como importado no Supabase
                supabase_id = item.get('id')
                if supabase_id:
                    client.update_record(table, supabase_id, {'migrado': True})
                
                importados += 1
                
            except Exception as e:
                erros.append(f"Erro no item {item.get('descricao')}: {str(e)}")
        
        db.session.commit()
        
        return {
            'success': True, 
            'message': f'{importados} itens importados com sucesso!',
            'erros': erros
        }
        
    except Exception as e:
        return {'success': False, 'message': str(e)}

@config_bp.route('/importar-supabase/excluir-item', methods=['POST'])
@login_required
@admin_required
def excluir_item_supabase():
    """Excluir item do Supabase"""
    try:
        data = request.get_json()
        id = data.get('id')
        config_data = data.get('config', {})

        client = SupabaseClient(config_data.get('url'), config_data.get('key'))
        result = client.delete_record(config_data.get('table'), id)

        return result
    except Exception as e:
        return {'success': False, 'message': str(e)}

@config_bp.route('/exportar-sqlite-despesas')
@login_required
@admin_required
def exportar_sqlite_despesas():
    """
    Exporta despesas do PostgreSQL para arquivo SQLite (financas.db)
    para popular o sistema desktop
    """
    import tempfile
    from flask import send_file

    try:
        # Criar banco SQLite temporário
        temp_dir = tempfile.gettempdir()
        sqlite_path = os.path.join(temp_dir, f'financas_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.db')

        # Conectar ao SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()

        # Criar estrutura do banco desktop
        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                meio_pagamento TEXT NOT NULL,
                conta_despesa TEXT NOT NULL,
                valor REAL NOT NULL,
                num_parcelas INTEGER DEFAULT 1,
                data_registro TEXT,
                data_pagamento TEXT
            )
        """)

        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS orcamento (
                conta_despesa TEXT PRIMARY KEY,
                valor_orcado REAL NOT NULL
            )
        """)

        # Buscar despesas do usuário logado
        despesas = Despesa.query.filter_by(user_id=current_user.id).all()

        for despesa in despesas:
            sqlite_cursor.execute("""
                INSERT INTO despesas (descricao, meio_pagamento, conta_despesa, valor,
                                    num_parcelas, data_registro, data_pagamento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                despesa.descricao,
                despesa.meio_pagamento.nome if despesa.meio_pagamento else 'Outros',
                despesa.categoria.nome if despesa.categoria else 'Outros',
                despesa.valor,
                despesa.num_parcelas or 1,
                despesa.data_registro.strftime('%Y-%m-%d') if despesa.data_registro else None,
                despesa.data_pagamento.strftime('%Y-%m-%d') if despesa.data_pagamento else None
            ))

        # Buscar orçamentos do usuário logado
        orcamentos = Orcamento.query.filter_by(user_id=current_user.id).all()

        for orcamento in orcamentos:
            try:
                sqlite_cursor.execute("""
                    INSERT OR REPLACE INTO orcamento (conta_despesa, valor_orcado)
                    VALUES (?, ?)
                """, (
                    orcamento.categoria.nome if orcamento.categoria else 'Outros',
                    orcamento.valor_orcado
                ))
            except:
                continue

        # Commit e fechar
        sqlite_conn.commit()
        sqlite_conn.close()

        # Enviar arquivo para download
        return send_file(
            sqlite_path,
            as_attachment=True,
            download_name='financas.db',
            mimetype='application/x-sqlite3'
        )

    except Exception as e:
        flash(f'Erro ao exportar despesas: {str(e)}', 'danger')
        return redirect(url_for('config.importar_dados_antigos'))

@config_bp.route('/exportar-sqlite-receitas')
@login_required
@admin_required
def exportar_sqlite_receitas():
    """
    Exporta receitas do PostgreSQL para arquivo SQLite (financas_receita.db)
    para popular o sistema desktop
    """
    import tempfile
    from flask import send_file

    try:
        # Criar banco SQLite temporário
        temp_dir = tempfile.gettempdir()
        sqlite_path = os.path.join(temp_dir, f'financas_receita_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.db')

        # Conectar ao SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()

        # Criar estrutura do banco desktop de receitas
        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                meio_recebimento TEXT NOT NULL,
                categoria_receita TEXT NOT NULL,
                valor REAL NOT NULL,
                num_parcelas INTEGER DEFAULT 1,
                data_registro TEXT,
                data_recebimento TEXT
            )
        """)

        # Buscar receitas do usuário logado
        receitas = Receita.query.filter_by(user_id=current_user.id).all()

        for receita in receitas:
            sqlite_cursor.execute("""
                INSERT INTO receitas (descricao, meio_recebimento, categoria_receita, valor,
                                    num_parcelas, data_registro, data_recebimento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                receita.descricao,
                receita.meio_recebimento.nome if receita.meio_recebimento else 'Outros',
                receita.categoria.nome if receita.categoria else 'Outros',
                receita.valor,
                receita.num_parcelas or 1,
                receita.data_registro.strftime('%Y-%m-%d') if receita.data_registro else None,
                receita.data_recebimento.strftime('%Y-%m-%d') if receita.data_recebimento else None
            ))

        # Commit e fechar
        sqlite_conn.commit()
        sqlite_conn.close()

        # Enviar arquivo para download
        return send_file(
            sqlite_path,
            as_attachment=True,
            download_name='financas_receita.db',
            mimetype='application/x-sqlite3'
        )

    except Exception as e:
        flash(f'Erro ao exportar receitas: {str(e)}', 'danger')
        return redirect(url_for('config.importar_dados_antigos'))

@config_bp.route('/exportar-sqlite-fluxo-caixa')
@login_required
@admin_required
def exportar_sqlite_fluxo_caixa():
    """
    Exporta fluxo de caixa do PostgreSQL para arquivo SQLite (fluxo_caixa.db)
    para popular o sistema desktop
    """
    import tempfile
    from flask import send_file

    try:
        # Criar banco SQLite temporário
        temp_dir = tempfile.gettempdir()
        sqlite_path = os.path.join(temp_dir, f'fluxo_caixa_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.db')

        # Conectar ao SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()

        # Criar estrutura do banco desktop de fluxo de caixa
        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS balanco_mensal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ano INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                total_entradas REAL DEFAULT 0.0,
                total_saidas REAL DEFAULT 0.0,
                saldo_mes REAL DEFAULT 0.0,
                observacoes TEXT
            )
        """)

        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS eventos_caixa_avulsos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL
            )
        """)

        # Buscar balanços mensais do usuário logado
        balancos = BalancoMensal.query.filter_by(user_id=current_user.id).order_by(BalancoMensal.ano, BalancoMensal.mes).all()

        for balanco in balancos:
            sqlite_cursor.execute("""
                INSERT INTO balanco_mensal (ano, mes, total_entradas, total_saidas, saldo_mes, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                balanco.ano,
                balanco.mes,
                balanco.total_entradas,
                balanco.total_saidas,
                balanco.saldo_mes,
                balanco.observacoes
            ))

        # Buscar eventos de caixa avulsos do usuário logado
        eventos = EventoCaixaAvulso.query.filter_by(user_id=current_user.id).order_by(EventoCaixaAvulso.data).all()

        for evento in eventos:
            sqlite_cursor.execute("""
                INSERT INTO eventos_caixa_avulsos (data, descricao, valor)
                VALUES (?, ?, ?)
            """, (
                evento.data.strftime('%Y-%m-%d') if evento.data else None,
                evento.descricao,
                evento.valor
            ))

        # Commit e fechar
        sqlite_conn.commit()
        sqlite_conn.close()

        # Enviar arquivo para download
        return send_file(
            sqlite_path,
            as_attachment=True,
            download_name='fluxo_caixa.db',
            mimetype='application/x-sqlite3'
        )

    except Exception as e:
        flash(f'Erro ao exportar fluxo de caixa: {str(e)}', 'danger')
        return redirect(url_for('config.importar_dados_antigos'))

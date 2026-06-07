from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_file
from flask_login import login_required, current_user
from routes.auth import admin_required, gerente_required, nao_free_required
from models import db, User, CategoriaDespesa, CategoriaReceita, MeioPagamento, MeioRecebimento, Orcamento, FechamentoCartao, Configuracao, Despesa, Receita, BalancoMensal, EventoCaixaAvulso, ConfigSistema, ApiKey
from utils.supabase_client import SupabaseClient
import json
from datetime import datetime
import os
import sqlite3
from datetime import datetime
from utils.pluggy_client import PluggyClient


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

        elif action == 'excluir':
            id = int(request.form.get('id'))
            transfer_id = request.form.get('transfer_id')
            categoria = CategoriaDespesa.query.filter_by(id=id, user_id=current_user.id).first()
            if categoria:
                count = Despesa.query.filter_by(categoria_id=id, user_id=current_user.id).count()
                if count > 0 and not transfer_id:
                    flash(f'Selecione uma categoria de destino para as {count} despesas vinculadas.', 'warning')
                    return redirect(url_for('config.categorias_despesa'))
                if count > 0 and transfer_id:
                    Despesa.query.filter_by(categoria_id=id, user_id=current_user.id)\
                                 .update({'categoria_id': int(transfer_id)}, synchronize_session=False)
                # Remover orçamentos vinculados (sem transferência)
                Orcamento.query.filter_by(categoria_id=id, user_id=current_user.id)\
                               .delete(synchronize_session=False)
                db.session.flush()           # persiste no banco antes do DELETE
                db.session.expunge(categoria)  # remove do cache da sessão
                CategoriaDespesa.query.filter_by(id=id, user_id=current_user.id).delete(synchronize_session=False)
                db.session.commit()
                flash('Categoria excluída com sucesso!', 'success')

        return redirect(url_for('config.categorias_despesa'))

    categorias = CategoriaDespesa.query.filter_by(user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
    desp_counts = dict(db.session.query(Despesa.categoria_id, db.func.count(Despesa.id))
                       .filter(Despesa.user_id == current_user.id)
                       .group_by(Despesa.categoria_id).all())
    return render_template('config/categorias_despesa.html', categorias=categorias, desp_counts=desp_counts)

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

        elif action == 'excluir':
            id = int(request.form.get('id'))
            transfer_id = request.form.get('transfer_id')
            categoria = CategoriaReceita.query.filter_by(id=id, user_id=current_user.id).first()
            if categoria:
                count = Receita.query.filter_by(categoria_id=id, user_id=current_user.id).count()
                if count > 0 and not transfer_id:
                    flash(f'Selecione uma categoria de destino para as {count} receitas vinculadas.', 'warning')
                    return redirect(url_for('config.categorias_receita'))
                if count > 0 and transfer_id:
                    Receita.query.filter_by(categoria_id=id, user_id=current_user.id)\
                                 .update({'categoria_id': int(transfer_id)}, synchronize_session=False)
                db.session.flush()
                db.session.expunge(categoria)
                CategoriaReceita.query.filter_by(id=id, user_id=current_user.id).delete(synchronize_session=False)
                db.session.commit()
                flash('Categoria excluída com sucesso!', 'success')

        return redirect(url_for('config.categorias_receita'))

    categorias = CategoriaReceita.query.filter_by(user_id=current_user.id).order_by(CategoriaReceita.nome).all()
    rec_counts = dict(db.session.query(Receita.categoria_id, db.func.count(Receita.id))
                      .filter(Receita.user_id == current_user.id)
                      .group_by(Receita.categoria_id).all())
    return render_template('config/categorias_receita.html', categorias=categorias, rec_counts=rec_counts)

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

        elif action == 'excluir':
            id = int(request.form.get('id'))
            transfer_id = request.form.get('transfer_id')
            meio = MeioPagamento.query.filter_by(id=id, user_id=current_user.id).first()
            if meio:
                count = Despesa.query.filter_by(meio_pagamento_id=id, user_id=current_user.id).count()
                if count > 0 and not transfer_id:
                    flash(f'Selecione um meio de destino para as {count} despesas vinculadas.', 'warning')
                    return redirect(url_for('config.meios_pagamento'))
                if count > 0 and transfer_id:
                    Despesa.query.filter_by(meio_pagamento_id=id, user_id=current_user.id)\
                                 .update({'meio_pagamento_id': int(transfer_id)}, synchronize_session=False)
                # Remover configurações de fechamento vinculadas ao cartão
                FechamentoCartao.query.filter_by(meio_pagamento_id=id).delete(synchronize_session=False)
                db.session.flush()
                db.session.expunge(meio)
                MeioPagamento.query.filter_by(id=id, user_id=current_user.id).delete(synchronize_session=False)
                db.session.commit()
                flash('Meio de pagamento excluído com sucesso!', 'success')

        return redirect(url_for('config.meios_pagamento'))

    meios = MeioPagamento.query.filter_by(user_id=current_user.id).order_by(MeioPagamento.nome).all()
    desp_counts = dict(db.session.query(Despesa.meio_pagamento_id, db.func.count(Despesa.id))
                       .filter(Despesa.user_id == current_user.id)
                       .group_by(Despesa.meio_pagamento_id).all())
    return render_template('config/meios_pagamento.html', meios=meios, desp_counts=desp_counts)

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

        elif action == 'excluir':
            id = int(request.form.get('id'))
            transfer_id = request.form.get('transfer_id')
            meio = MeioRecebimento.query.filter_by(id=id, user_id=current_user.id).first()
            if meio:
                count = Receita.query.filter_by(meio_recebimento_id=id, user_id=current_user.id).count()
                if count > 0 and not transfer_id:
                    flash(f'Selecione um meio de destino para as {count} receitas vinculadas.', 'warning')
                    return redirect(url_for('config.meios_recebimento'))
                if count > 0 and transfer_id:
                    Receita.query.filter_by(meio_recebimento_id=id, user_id=current_user.id)\
                                 .update({'meio_recebimento_id': int(transfer_id)}, synchronize_session=False)
                db.session.flush()
                db.session.expunge(meio)
                MeioRecebimento.query.filter_by(id=id, user_id=current_user.id).delete(synchronize_session=False)
                db.session.commit()
                flash('Meio de recebimento excluído com sucesso!', 'success')

        return redirect(url_for('config.meios_recebimento'))

    meios = MeioRecebimento.query.filter_by(user_id=current_user.id).order_by(MeioRecebimento.nome).all()
    rec_counts = dict(db.session.query(Receita.meio_recebimento_id, db.func.count(Receita.id))
                      .filter(Receita.user_id == current_user.id)
                      .group_by(Receita.meio_recebimento_id).all())
    return render_template('config/meios_recebimento.html', meios=meios, rec_counts=rec_counts)

@config_bp.route('/usuarios/<int:id>/exportar-dados')
@login_required
@gerente_required
def exportar_dados_usuario(id):
    """Exporta todos os dados de um usuário para um arquivo Excel (uma aba por tabela)."""
    import pandas as pd
    from io import BytesIO

    usuario = User.query.get_or_404(id)

    planilhas = {
        'Despesas': [
            {
                'Data': d.data_pagamento.strftime('%d/%m/%Y') if d.data_pagamento else '',
                'Descrição': d.descricao,
                'Categoria': d.categoria.nome if d.categoria else '',
                'Meio de Pagamento': d.meio_pagamento.nome if d.meio_pagamento else '',
                'Valor': d.valor,
                'Parcelas': d.num_parcelas,
            } for d in Despesa.query.filter_by(user_id=usuario.id).all()
        ],
        'Receitas': [
            {
                'Data': r.data_recebimento.strftime('%d/%m/%Y') if r.data_recebimento else '',
                'Descrição': r.descricao,
                'Categoria': r.categoria.nome if r.categoria else '',
                'Meio de Recebimento': r.meio_recebimento.nome if r.meio_recebimento else '',
                'Valor': r.valor,
                'Parcelas': r.num_parcelas,
            } for r in Receita.query.filter_by(user_id=usuario.id).all()
        ],
        'Categorias Despesa': [
            {'Nome': c.nome, 'Ativo': 'Sim' if c.ativo else 'Não'}
            for c in CategoriaDespesa.query.filter_by(user_id=usuario.id).all()
        ],
        'Categorias Receita': [
            {'Nome': c.nome, 'Ativo': 'Sim' if c.ativo else 'Não'}
            for c in CategoriaReceita.query.filter_by(user_id=usuario.id).all()
        ],
        'Meios de Pagamento': [
            {'Nome': m.nome, 'Tipo': m.tipo, 'Ativo': 'Sim' if m.ativo else 'Não'}
            for m in MeioPagamento.query.filter_by(user_id=usuario.id).all()
        ],
        'Meios de Recebimento': [
            {'Nome': m.nome, 'Ativo': 'Sim' if m.ativo else 'Não'}
            for m in MeioRecebimento.query.filter_by(user_id=usuario.id).all()
        ],
        'Orçamentos': [
            {
                'Categoria': o.categoria.nome if o.categoria else '',
                'Valor Orçado': o.valor_orcado,
            } for o in Orcamento.query.filter_by(user_id=usuario.id).all()
        ],
        'Balanço Mensal': [
            {
                'Mês': b.mes, 'Ano': b.ano,
                'Total Entradas': b.total_entradas,
                'Total Saídas': b.total_saidas,
                'Saldo': b.saldo_mes,
            } for b in BalancoMensal.query.filter_by(user_id=usuario.id).all()
        ],
        'Eventos de Caixa': [
            {
                'Data': e.data.strftime('%d/%m/%Y') if e.data else '',
                'Descrição': e.descricao,
                'Valor': e.valor,
            } for e in EventoCaixaAvulso.query.filter_by(user_id=usuario.id).all()
        ],
    }

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Aba de identificação do usuário
        pd.DataFrame([{
            'Nome': usuario.nome or '',
            'Usuário': usuario.username,
            'E-mail': usuario.email,
            'Nível de Acesso': usuario.nivel_acesso,
            'CPF': usuario.cpf or '',
            'WhatsApp': usuario.whatsapp or '',
            'Data de Criação': usuario.data_criacao.strftime('%d/%m/%Y') if usuario.data_criacao else '',
        }]).to_excel(writer, index=False, sheet_name='Usuário')

        for nome_aba, dados in planilhas.items():
            df = pd.DataFrame(dados) if dados else pd.DataFrame(columns=['(sem registros)'])
            df.to_excel(writer, index=False, sheet_name=nome_aba[:31])

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'dados_{usuario.username}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )


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
            nome = request.form.get('nome', '').strip() or None
            whatsapp = request.form.get('whatsapp', '').strip() or None
            import re as _re
            cpf_raw = _re.sub(r'\D', '', request.form.get('cpf', '').strip()) or None

            if User.query.filter_by(username=username).first():
                flash('Nome de usuário já existe!', 'warning')
            elif User.query.filter_by(email=email).first():
                flash('E-mail já cadastrado!', 'warning')
            elif cpf_raw and User.query.filter_by(cpf=cpf_raw).first():
                flash('CPF já cadastrado!', 'warning')
            else:
                data_validade = None
                if nivel != 'admin' and data_validade_str:
                    from datetime import datetime
                    data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date()

                novo_usuario = User(
                    username=username,
                    email=email,
                    nivel_acesso=nivel,
                    ativo=True,
                    email_confirmado=True,
                    data_validade=data_validade,
                    nome=nome,
                    whatsapp=whatsapp,
                    cpf=cpf_raw,
                )
                novo_usuario.set_password(password)
                db.session.add(novo_usuario)
                db.session.commit()

                # Salvar foto de perfil se enviada
                foto_file = request.files.get('foto_perfil')
                if foto_file and foto_file.filename:
                    ext = foto_file.filename.rsplit('.', 1)[-1].lower()
                    if ext in current_app.config.get('ALLOWED_PHOTO_EXTENSIONS', {'jpg','jpeg','png','webp'}):
                        import os
                        foto_nome = f"user_{novo_usuario.id}.{ext}"
                        foto_file.save(os.path.join(current_app.config['UPLOAD_PERFIL_FOLDER'], foto_nome))
                        novo_usuario.foto_perfil = foto_nome
                        db.session.commit()

                from models import criar_dados_padrao_usuario
                criar_dados_padrao_usuario(novo_usuario)

                flash('Usuário criado com sucesso!', 'success')

        elif action == 'editar':
            id = int(request.form.get('id'))
            username = request.form.get('username')
            email = request.form.get('email')
            nome = request.form.get('nome', '').strip() or None
            whatsapp = request.form.get('whatsapp', '').strip() or None
            import re as _re
            cpf_edit = _re.sub(r'\D', '', request.form.get('cpf', '').strip()) or None

            user = User.query.get(id)
            if user:
                cpf_conflict = cpf_edit and User.query.filter(
                    User.cpf == cpf_edit, User.id != id).first()
                if user.username != username and User.query.filter_by(username=username).first():
                    flash('Nome de usuário já existe!', 'warning')
                elif user.email != email and User.query.filter_by(email=email).first():
                    flash('E-mail já cadastrado!', 'warning')
                elif cpf_conflict:
                    flash('CPF já cadastrado para outro usuário!', 'warning')
                else:
                    user.username = username
                    user.email = email
                    user.nome = nome
                    user.whatsapp = whatsapp
                    user.cpf = cpf_edit

                    # Foto de perfil
                    foto_file = request.files.get('foto_perfil')
                    if foto_file and foto_file.filename:
                        ext = foto_file.filename.rsplit('.', 1)[-1].lower()
                        if ext in current_app.config.get('ALLOWED_PHOTO_EXTENSIONS', {'jpg','jpeg','png','webp'}):
                            import os
                            foto_nome = f"user_{user.id}.{ext}"
                            foto_file.save(os.path.join(current_app.config['UPLOAD_PERFIL_FOLDER'], foto_nome))
                            user.foto_perfil = foto_nome

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

        elif action == 'importar_dados':
            id = int(request.form.get('id'))
            user = User.query.get(id)
            planilha = request.files.get('planilha_dados')

            if not user:
                flash('Usuário não encontrado.', 'danger')
            elif not (planilha and planilha.filename):
                flash('Selecione um arquivo .xlsx para importar.', 'warning')
            elif not planilha.filename.lower().endswith('.xlsx'):
                flash('Formato inválido: envie um arquivo .xlsx exportado pelo FiNan.', 'danger')
            else:
                from routes.auth import _importar_planilha_dados_usuario
                ok, msg = _importar_planilha_dados_usuario(user, planilha)
                flash(f'{user.nome or user.username}: {msg}', 'success' if ok else 'warning')

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

        elif action == 'excluir':
            id = int(request.form.get('id'))
            user = User.query.get(id)
            if user and user.id == current_user.id:
                flash('Você não pode excluir sua própria conta!', 'danger')
            elif user:
                if user.is_admin() and not current_user.is_admin():
                    flash('Apenas administradores podem excluir contas de administrador!', 'danger')
                else:
                    nome_excluido = user.nome or user.username

                    # Apagar primeiro os lançamentos e vínculos que referenciam
                    # categorias/meios — senão a FK impede excluir as próprias
                    # categorias/meios na sequência
                    Despesa.query.filter_by(user_id=user.id).delete()
                    Receita.query.filter_by(user_id=user.id).delete()
                    Orcamento.query.filter_by(user_id=user.id).delete()

                    cartao_ids = [m.id for m in MeioPagamento.query.filter_by(user_id=user.id).all()]
                    if cartao_ids:
                        FechamentoCartao.query.filter(FechamentoCartao.meio_pagamento_id.in_(cartao_ids)).delete(synchronize_session=False)

                    # Apagar registros que não possuem cascade configurado em User
                    CategoriaDespesa.query.filter_by(user_id=user.id).delete()
                    CategoriaReceita.query.filter_by(user_id=user.id).delete()
                    MeioPagamento.query.filter_by(user_id=user.id).delete()
                    MeioRecebimento.query.filter_by(user_id=user.id).delete()
                    ApiKey.query.filter_by(user_id=user.id).delete()

                    db.session.delete(user)
                    db.session.commit()
                    flash(f'Usuário {nome_excluido} excluído com sucesso!', 'success')

        return redirect(url_for('config.usuarios'))
    
    usuarios = User.query.order_by(User.username).all()
    return render_template('config/usuarios.html', usuarios=usuarios)


# ─── SMTP / WhatsApp config ───────────────────────────────────────────────────

_SMTP_KEYS = ['smtp_host','smtp_port','smtp_secure','smtp_user','smtp_password','smtp_from',
              'webhook_whatsapp','notificar_email','notificar_whatsapp']

@config_bp.route('/smtp-whatsapp', methods=['GET', 'POST'])
@login_required
@admin_required
def smtp_whatsapp():
    if request.method == 'POST':
        action = request.form.get('action', 'save')

        if action == 'save':
            for key in _SMTP_KEYS:
                val = request.form.get(key, '').strip()
                ConfigSistema.set(key, val if val else None)
            db.session.commit()
            flash('Configurações salvas com sucesso!', 'success')

        elif action == 'test_email':
            dest = request.form.get('test_email_dest', '').strip()
            resultado = _enviar_email_teste(dest)
            flash(resultado[1], resultado[0])

        elif action == 'test_whatsapp':
            numero = request.form.get('test_whatsapp_numero', '').strip()
            resultado = _enviar_whatsapp_teste(numero)
            flash(resultado[1], resultado[0])

        return redirect(url_for('config.smtp_whatsapp'))

    cfg = {k: ConfigSistema.get(k, '') for k in _SMTP_KEYS}
    return render_template('config/smtp_whatsapp.html', cfg=cfg)


def _enviar_email_teste(destinatario):
    import smtplib, ssl
    from email.mime.text import MIMEText
    try:
        host     = ConfigSistema.get('smtp_host', '')
        port     = int(ConfigSistema.get('smtp_port', 465) or 465)
        secure   = (ConfigSistema.get('smtp_secure', 'true') or 'true').lower() == 'true'
        user     = ConfigSistema.get('smtp_user', '')
        password = ConfigSistema.get('smtp_password', '')
        from_    = ConfigSistema.get('smtp_from', user)
        if not host or not user:
            return ('warning', 'Configure o SMTP antes de testar.')
        msg = MIMEText('Teste de e-mail do Sistema Financeiro.')
        msg['Subject'] = 'Teste SMTP — Sistema Financeiro'
        msg['From'] = from_
        msg['To']   = destinatario
        ctx = ssl.create_default_context()
        if secure:
            with smtplib.SMTP_SSL(host, port, context=ctx) as s:
                s.login(user, password); s.sendmail(from_, [destinatario], msg.as_string())
        else:
            with smtplib.SMTP(host, port) as s:
                s.ehlo(); s.starttls(context=ctx); s.login(user, password)
                s.sendmail(from_, [destinatario], msg.as_string())
        return ('success', f'E-mail de teste enviado para {destinatario}.')
    except Exception as e:
        return ('danger', f'Erro ao enviar e-mail: {e}')


def _enviar_whatsapp(mensagem, numero):
    """Envia mensagem WhatsApp via webhook. Formato exato: texto<o>numero"""
    import requests as req
    import re
    webhook = ConfigSistema.get('webhook_whatsapp', '')
    if not webhook:
        raise ValueError('Webhook WhatsApp não configurado.')
    # Manter apenas dígitos no número
    numero_limpo = re.sub(r'\D', '', numero)
    payload = f'{mensagem}<o>{numero_limpo}'
    r = req.post(
        webhook,
        data=payload.encode('utf-8'),
        headers={'Content-Type': 'text/plain; charset=utf-8'},
        timeout=15
    )
    r.raise_for_status()
    return r


def _enviar_whatsapp_teste(numero):
    try:
        _enviar_whatsapp('Teste do Sistema Financeiro', numero)
        return ('success', f'Mensagem de teste enviada para {numero}.')
    except Exception as e:
        return ('danger', f'Erro ao enviar WhatsApp: {e}')


@config_bp.route('/orcamento', methods=['GET', 'POST'])
@login_required
def orcamento():
    """Gerenciar orçamento geral por categoria"""
    if request.method == 'POST':
        # Simplificado: Recebe apenas id da categoria e valor
        categoria_id = int(request.form.get('categoria_id'))
        valor_bruto = request.form.get('valor_orcado', '0').replace(',', '.')
        try:
            valor_orcado = float(valor_bruto)
        except ValueError:
            valor_orcado = 0.0
        
        # Verificar se já existe orçamento para esta categoria
        orcamento_existente = Orcamento.query.filter_by(
            categoria_id=categoria_id,
            user_id=current_user.id
        ).first()
        
        if orcamento_existente:
            orcamento_existente.valor_orcado = valor_orcado
            # Se quiser deletar zeros: 
            # if valor_orcado == 0: db.session.delete(orcamento_existente)
        else:
            if valor_orcado > 0: # Só cria se tiver valor
                novo_orcamento = Orcamento(
                    categoria_id=categoria_id,
                    valor_orcado=valor_orcado,
                    user_id=current_user.id
                )
                db.session.add(novo_orcamento)
        
        db.session.commit()
        flash('Orçamento atualizado!', 'success')
        return redirect(url_for('config.orcamento'))
    
    # GET: Preparar dados para a lista unificada
    categorias = CategoriaDespesa.query.filter_by(ativo=True, user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
    orcamentos = Orcamento.query.filter_by(user_id=current_user.id).all()
    
    # Dicionário de orçamentos para acesso rápido: {categoria_id: objeto_orcamento}
    orcamentos_map = {o.categoria_id: o for o in orcamentos}

    return render_template('config/orcamento.html',
                          categorias=categorias,
                          orcamentos_map=orcamentos_map)


# ─── API Key management ───────────────────────────────────────────────────────

@config_bp.route('/api-key', methods=['GET', 'POST'])
@login_required
@admin_required
def api_key():
    """Página de gerenciamento de API keys — exclusiva para admin."""
    from flask import session as flask_session

    if request.method == 'POST':
        action  = request.form.get('action')
        user_id = int(request.form.get('user_id', current_user.id))

        if action == 'gerar':
            raw, key_hash, prefix = ApiKey.gerar_chave()
            ak = ApiKey.query.filter_by(user_id=user_id).first()
            if ak:
                ak.key_hash      = key_hash
                ak.key_prefix    = prefix
                ak.ativo         = True
                ak.data_criacao  = __import__('datetime').datetime.utcnow()
                ak.total_requests = 0
                ak.data_ultimo_uso = None
            else:
                ak = ApiKey(user_id=user_id, key_hash=key_hash, key_prefix=prefix, ativo=True)
                db.session.add(ak)
            db.session.commit()

            target = User.query.get(user_id)
            flash(f'Chave gerada para {target.username}. Copie agora — não será exibida novamente.', 'success')
            flask_session[f'api_key_raw_{user_id}'] = raw
            return redirect(url_for('config.api_key'))

        elif action == 'revogar':
            ak = ApiKey.query.filter_by(user_id=user_id).first()
            if ak:
                ak.ativo = False
                db.session.commit()
                flash('API key revogada.', 'warning')
            return redirect(url_for('config.api_key'))

        elif action == 'salvar_limite':
            limite = request.form.get('limite_free', '500').strip()
            try:
                limite = max(1, int(limite))
            except ValueError:
                limite = 500
            from models import ConfigSistema
            ConfigSistema.set('limite_registros_free', str(limite))
            db.session.commit()
            flash(f'Limite Free atualizado para {limite} registros/mês.', 'success')
            return redirect(url_for('config.api_key'))

    # Coletar raw keys para exibição única
    usuarios = User.query.order_by(User.username).all()
    keys_map  = {ak.user_id: ak for ak in ApiKey.query.all()}
    raw_map   = {}
    for u in usuarios:
        k = flask_session.pop(f'api_key_raw_{u.id}', None)
        if k:
            raw_map[u.id] = k

    # Catálogos do admin (para a aba de docs)
    cat_despesas = CategoriaDespesa.query.filter_by(user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
    cat_receitas = CategoriaReceita.query.filter_by(user_id=current_user.id).order_by(CategoriaReceita.nome).all()
    meios_pag    = MeioPagamento.query.filter_by(user_id=current_user.id).order_by(MeioPagamento.nome).all()
    meios_rec    = MeioRecebimento.query.filter_by(user_id=current_user.id).order_by(MeioRecebimento.nome).all()

    from models import ConfigSistema
    limite_free = int(ConfigSistema.get('limite_registros_free', '500') or 500)

    return render_template(
        'config/api_keys.html',
        usuarios=usuarios,
        keys_map=keys_map,
        raw_map=raw_map,
        cat_despesas=cat_despesas,
        cat_receitas=cat_receitas,
        meios_pag=meios_pag,
        meios_rec=meios_rec,
        limite_free=limite_free,
    )

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
    cartao_ids = [c.id for c in cartoes]
    configuracoes = FechamentoCartao.query.filter(FechamentoCartao.meio_pagamento_id.in_(cartao_ids)).all()

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
    
    categorias      = CategoriaDespesa.query.filter_by(ativo=True, user_id=current_user.id)\
                                            .order_by(CategoriaDespesa.nome).all()
    meios_pagamento = MeioPagamento.query.filter_by(ativo=True, user_id=current_user.id)\
                                         .order_by(MeioPagamento.nome).all()

    return render_template('config/importar_supabase.html',
                         supabase_url=config_url.valor if config_url else '',
                         supabase_key=config_key.valor if config_key else '',
                         supabase_table=config_table.valor if config_table else '',
                         categorias=categorias,
                         meios_pagamento=meios_pagamento)

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
                raw_valor = item.get('valor', 0)
                if isinstance(raw_valor, (int, float)):
                    # Já é número — usa direto
                    valor = float(raw_valor)
                else:
                    valor_str = str(raw_valor).strip()
                    if ',' in valor_str:
                        # Formato brasileiro: 1.234,56 → remove '.' de milhar, troca ',' por '.'
                        valor_str = valor_str.replace('.', '').replace(',', '.')
                    # Caso contrário é ponto decimal padrão: 4.99 → usa direto
                    valor = float(valor_str) if valor_str else 0.0
                
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
                data_pagamento TEXT,
                user_id INTEGER
            )
        """)

        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS orcamento (
                conta_despesa TEXT PRIMARY KEY,
                valor_orcado REAL NOT NULL
            )
        """)

        # Criar tabelas auxiliares
        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """)

        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS meios_pagamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """)

        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS fechamento_cartoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meio_pagamento TEXT NOT NULL UNIQUE,
                data_fechamento INTEGER NOT NULL,
                data_vencimento INTEGER,
                FOREIGN KEY (meio_pagamento) REFERENCES meios_pagamento(nome)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )
        """)

        # Popular tabelas auxiliares do usuário
        categorias_despesa = CategoriaDespesa.query.filter_by(user_id=current_user.id).all()
        for categoria in categorias_despesa:
            sqlite_cursor.execute("INSERT OR IGNORE INTO categorias (nome) VALUES (?)", (categoria.nome,))

        meios_pagamento = MeioPagamento.query.filter_by(user_id=current_user.id).all()
        for meio in meios_pagamento:
            sqlite_cursor.execute("INSERT OR IGNORE INTO meios_pagamento (nome) VALUES (?)", (meio.nome,))

        # Popular fechamento de cartões
        # Buscar todos os fechamentos cujos meios de pagamento pertencem ao usuário
        meios_ids = [m.id for m in meios_pagamento]
        if meios_ids:
            fechamentos = FechamentoCartao.query.filter(FechamentoCartao.meio_pagamento_id.in_(meios_ids)).all()
            print(f"[DEBUG] Meios de pagamento IDs: {meios_ids}")
            print(f"[DEBUG] Fechamentos encontrados: {len(fechamentos)}")
            for fechamento in fechamentos:
                try:
                    meio_nome = fechamento.meio_pagamento.nome if fechamento.meio_pagamento else 'Desconhecido'
                    print(f"[DEBUG] Inserindo: {meio_nome} - Fechamento: {fechamento.dia_fechamento}, Vencimento: {fechamento.dia_vencimento}")
                    sqlite_cursor.execute("""
                        INSERT INTO fechamento_cartoes (meio_pagamento, data_fechamento, data_vencimento)
                        VALUES (?, ?, ?)
                    """, (
                        meio_nome,
                        fechamento.dia_fechamento,
                        fechamento.dia_vencimento
                    ))
                except Exception as e:
                    print(f"[DEBUG ERRO] Falha ao inserir fechamento: {str(e)}")
                    continue

        # Buscar despesas do usuário logado
        despesas = Despesa.query.filter_by(user_id=current_user.id).all()

        for despesa in despesas:
            sqlite_cursor.execute("""
                INSERT INTO despesas (descricao, meio_pagamento, conta_despesa, valor,
                                    num_parcelas, data_registro, data_pagamento, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                despesa.descricao,
                despesa.meio_pagamento.nome if despesa.meio_pagamento else 'Outros',
                despesa.categoria.nome if despesa.categoria else 'Outros',
                despesa.valor,
                despesa.num_parcelas or 1,
                despesa.data_registro.strftime('%Y-%m-%d') if despesa.data_registro else None,
                despesa.data_pagamento.strftime('%Y-%m-%d') if despesa.data_pagamento else None,
                despesa.user_id
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

        # Criar view de compatibilidade (usada pelos relatórios avançados do desktop)
        sqlite_cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_despesas_compat AS
            SELECT
                id,
                descricao,
                valor,
                num_parcelas,
                data_pagamento,
                data_registro,
                conta_despesa,
                meio_pagamento,
                user_id
            FROM despesas
        """)

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
                conta_receita TEXT NOT NULL,
                valor REAL NOT NULL,
                num_parcelas INTEGER DEFAULT 1,
                data_registro TEXT,
                data_recebimento TEXT
            )
        """)

        # Criar tabelas auxiliares
        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias_receita (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """)

        sqlite_cursor.execute("""
            CREATE TABLE IF NOT EXISTS meios_recebimento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        """)

        # Popular tabelas auxiliares do usuário
        categorias_receita = CategoriaReceita.query.filter_by(user_id=current_user.id).all()
        for categoria in categorias_receita:
            sqlite_cursor.execute("INSERT OR IGNORE INTO categorias_receita (nome) VALUES (?)", (categoria.nome,))

        meios_recebimento = MeioRecebimento.query.filter_by(user_id=current_user.id).all()
        for meio in meios_recebimento:
            sqlite_cursor.execute("INSERT OR IGNORE INTO meios_recebimento (nome) VALUES (?)", (meio.nome,))

        # Buscar receitas do usuário logado
        receitas = Receita.query.filter_by(user_id=current_user.id).all()

        for receita in receitas:
            sqlite_cursor.execute("""
                INSERT INTO receitas (descricao, meio_recebimento, conta_receita, valor,
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
            download_name='financas_receitas.db',
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

@config_bp.route('/openfinance', methods=['GET'])
@login_required
def openfinance():
    """Página principal do OpenFinance"""
    return render_template('config/openfinance.html')

@config_bp.route('/openfinance/import', methods=['POST'])
@login_required
def openfinance_import():
    """Busca dados da Pluggy e mostra tela de revisão"""
    from flask import current_app
    
    item_id = request.form.get('item_id')
    sync_all = request.form.get('sync_all') == 'on'
    
    if not item_id:
        flash('Item ID é obrigatório!', 'warning')
        return redirect(url_for('config.openfinance'))
        
    client_id = current_app.config.get('PLUGGY_CLIENT_ID')
    client_secret = current_app.config.get('PLUGGY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        flash('Credenciais da Pluggy não configuradas no servidor.', 'danger')
        return redirect(url_for('config.openfinance'))
        
    try:
        client = PluggyClient(client_id, client_secret)
        
        # 1. Buscar contas
        accounts = client.get_accounts(item_id)
        if not accounts:
            flash('Nenhuma conta encontrada para este Item ID.', 'warning')
            return redirect(url_for('config.openfinance'))
            
        # Carregar categorias para o template
        cats_despesa = CategoriaDespesa.query.filter_by(user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
        cats_receita = CategoriaReceita.query.filter_by(user_id=current_user.id).order_by(CategoriaReceita.nome).all()
        
        # Carregar cartões para seleção
        cartoes = MeioPagamento.query.filter_by(user_id=current_user.id, tipo='cartao', ativo=True).all()
        
        cat_outros_despesa = next((c for c in cats_despesa if c.nome.lower() == 'outros'), None)
        cat_outros_receita = next((c for c in cats_receita if c.nome.lower() == 'outros'), None)
        
        if not cat_outros_despesa and cats_despesa:
            cat_outros_despesa = cats_despesa[0]
        if not cat_outros_receita and cats_receita:
            cat_outros_receita = cats_receita[0]
            
        transactions_display = []
        
        for account in accounts:
            acc_type = account.get('type') # CREDIT or BANK
            
            # Buscar transações
            transactions = client.get_transactions(account['id'])
            
            for tr in transactions:
                amount = tr.get('amount')
                if amount == 0: continue
                
                description = tr.get('description')
                date_str = tr.get('date').split('T')[0]
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Verificar duplicidade
                exists = False
                suggested_cat_id = None
                
                # LÓGICA DE CLASSIFICAÇÃO PERSONALIZADA
                # Regra 1: Cartão de Crédito
                # "Todos os dados do cartão, via de regra são despesas, somente as relacionadas como estorno seria receitas"
                if acc_type == 'CREDIT':
                    if amount > 0:
                        # Se for positivo (crédito), só é receita se for estorno. 
                        # Caso contrário, invertemos para negativo para tratar como despesa (ex: pagamento de fatura, ajustes)
                        if 'estorno' not in description.lower():
                            amount = -abs(amount)
                
                # Regra 2: Conta Corrente
                # "Registros vindos da conta corrente podem ser receitas ou despesas" -> Mantém lógica do sinal (já é o padrão)

                if amount < 0:
                    # Despesa
                    check = Despesa.query.filter_by(
                        user_id=current_user.id,
                        valor=abs(amount),
                        data_pagamento=date_obj,
                        descricao=description
                    ).first()
                    if check: exists = True
                    
                    # Sugerir Categoria
                    suggested_cat_id = cat_outros_despesa.id if cat_outros_despesa else None
                    for cat in cats_despesa:
                        if cat.nome.lower() in description.lower():
                            suggested_cat_id = cat.id
                            break
                            
                else:
                    # Receita
                    check = Receita.query.filter_by(
                        user_id=current_user.id,
                        valor=amount,
                        data_recebimento=date_obj,
                        descricao=description
                    ).first()
                    if check: exists = True
                    
                    # Sugerir Categoria
                    suggested_cat_id = cat_outros_receita.id if cat_outros_receita else None
                    for cat in cats_receita:
                        if cat.nome.lower() in description.lower():
                            suggested_cat_id = cat.id
                            break
                
                transactions_display.append({
                    'id': tr.get('id'),
                    'date': date_str,
                    'date_formatted': date_obj.strftime('%d/%m/%Y'),
                    'description': description,
                    'amount': amount,
                    'account_type': acc_type,
                    'exists': exists,
                    'suggested_category_id': suggested_cat_id
                })
        
        # Ordenar por data
        transactions_display.sort(key=lambda x: x['date'], reverse=True)
        
        return render_template('config/openfinance_review.html', 
                             transactions=transactions_display,
                             cats_despesa=cats_despesa,
                             cats_receita=cats_receita,
                             item_id=item_id,
                             cartoes=cartoes)
                             
    except Exception as e:
        flash(f'Erro na comunicação com Pluggy: {str(e)}', 'danger')
        return redirect(url_for('config.openfinance'))

@config_bp.route('/openfinance/confirm', methods=['POST'])
@login_required
def openfinance_confirm():
    """Processa a gravação das transações selecionadas"""
    
    selected_indices = request.form.getlist('selected_idx')
    target_card_id = request.form.get('target_card_id')
    
    if not selected_indices:
        flash('Nenhuma transação selecionada.', 'warning')
        return redirect(url_for('config.openfinance'))
        
    try:
        count = 0
        
        # Carregar meios de pagamento
        meio_cartao_padrao = MeioPagamento.query.filter_by(user_id=current_user.id, tipo='cartao').first()
        meio_debito = MeioPagamento.query.filter_by(user_id=current_user.id, tipo='debito').first()
        meio_rec = MeioRecebimento.query.filter_by(user_id=current_user.id).first()
        
        # Se usuário selecionou um cartão específico, usamos ele. Se não, fallback.
        meio_cartao_selecionado = None
        if target_card_id:
             meio_cartao_selecionado = MeioPagamento.query.get(int(target_card_id))
        
        # Fallback final se não selecionou e não achou
        if not meio_cartao_selecionado:
            meio_cartao_selecionado = meio_cartao_padrao
        
        # Fallback para débito
        if not meio_debito: meio_debito = MeioPagamento.query.filter_by(user_id=current_user.id).first()
        
        for idx in selected_indices:
            try:
                description = request.form.get(f'description_{idx}')
                amount = float(request.form.get(f'amount_{idx}'))
                date_str = request.form.get(f'date_{idx}')
                cat_id = int(request.form.get(f'category_{idx}'))
                acc_type = request.form.get(f'account_type_{idx}')
                
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                if amount < 0:
                    # Salvar Despesa
                    # Se for crédito, usa o selecionado. Se for débito, usa o de débito.
                    meio_id = meio_cartao_selecionado.id if acc_type == 'CREDIT' else meio_debito.id
                    
                    nova_despesa = Despesa(
                        descricao=description,
                        valor=abs(amount),
                        data_pagamento=date_obj,
                        data_registro=datetime.now(),
                        user_id=current_user.id,
                        categoria_id=cat_id,
                        meio_pagamento_id=meio_id
                    )
                    db.session.add(nova_despesa)
                else:
                    # Salvar Receita
                    nova_receita = Receita(
                        descricao=description,
                        valor=amount,
                        data_recebimento=date_obj,
                        data_registro=datetime.now(),
                        user_id=current_user.id,
                        categoria_id=cat_id,
                        meio_recebimento_id=meio_rec.id if meio_rec else None
                    )
                    db.session.add(nova_receita)
                    
                count += 1
                
            except Exception as e:
                print(f"Erro ao salvar item {idx}: {e}")
                continue
                
        db.session.commit()
        flash(f'Sucesso! {count} transações importadas.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar dados: {str(e)}', 'danger')
        
    return redirect(url_for('config.openfinance'))

@config_bp.route('/openfinance/token', methods=['GET'])
@login_required
def openfinance_token():
    """Gera um token de conexão para o widget da Pluggy"""
    from flask import current_app, jsonify
    
    client_id = current_app.config.get('PLUGGY_CLIENT_ID')
    client_secret = current_app.config.get('PLUGGY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        return jsonify({'error': 'Credenciais não configuradas'}), 400
        
    try:
        client = PluggyClient(client_id, client_secret)
        token = client.create_connect_token()
        return jsonify({'accessToken': token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@config_bp.route('/importar-fatura-cartao', methods=['GET'])
@login_required
@nao_free_required
def importar_fatura_cartao():
    """PÃ¡gina de importaÃ§Ã£o de fatura de cartÃ£o CSV"""
    cartoes = MeioPagamento.query.filter_by(
        tipo='cartao', ativo=True, user_id=current_user.id
    ).order_by(MeioPagamento.nome).all()
    cartao_ids_imp = [c.id for c in cartoes]
    fechamentos = {fc.meio_pagamento_id: fc for fc in FechamentoCartao.query.filter(FechamentoCartao.meio_pagamento_id.in_(cartao_ids_imp)).all()}
    categorias = CategoriaDespesa.query.filter_by(
        user_id=current_user.id, ativo=True
    ).order_by(CategoriaDespesa.nome).all()
    return render_template('config/importar_fatura_cartao.html',
                           cartoes=cartoes,
                           fechamentos=fechamentos,
                           categorias=categorias)


@config_bp.route('/debug-pdf', methods=['POST'])
@login_required
def debug_pdf():
    """Rota temporÃ¡ria para inspecionar texto extraÃ­do do PDF"""
    arquivo = request.files.get('arquivo')
    if not arquivo:
        return jsonify({'error': 'sem arquivo'})
    try:
        import pdfplumber, io as _io
        raw = arquivo.read()
        resultado = []
        with pdfplumber.open(_io.BytesIO(raw)) as pdf:
            for i, page in enumerate(pdf.pages):
                txt = page.extract_text(layout=True) or ''
                linhas = txt.split('\n')
                resultado.append({
                    'pagina': i + 1,
                    'total_linhas': len(linhas),
                    'linhas': [{'idx': j, 'txt': l} for j, l in enumerate(linhas)]
                })
        return jsonify({'success': True, 'paginas': resultado})
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()})


def _processar_pdf_nubank(arquivo, cartao_id, cartao, fechamento):
    """
    Extrai transaÃ§Ãµes de um PDF de fatura do Nubank.
    Formato: DD MMM [â€¢â€¢â€¢â€¢XXXX] DescriÃ§Ã£o [- Parcela X/Y] R$ valor
    Ignora: pagamentos, IOF, saldo restante, valores negativos.
    """
    import re as _re
    from datetime import datetime as _dt, date as _date

    try:
        import pdfplumber
    except ImportError:
        return jsonify({'success': False,
                        'error': 'Biblioteca pdfplumber nÃ£o instalada no servidor.'})

    MESES_PT = {'jan':1,'fev':2,'mar':3,'abr':4,'mai':5,'jun':6,
                'jul':7,'ago':8,'set':9,'out':10,'nov':11,'dez':12}

    def _val(s):
        s = str(s or '').strip().replace(' ', '').replace('R$','').replace('âˆ’','').replace('âˆ’','')
        if not s or s == '-':
            return 0.0
        s = s.replace('.', '').replace(',', '.')
        try:
            return abs(float(s))
        except Exception:
            return 0.0

    def _parse_data_nu(dia_s, mes_s):
        """DD MMM â†’ date"""
        try:
            dia = int(dia_s)
            mes = MESES_PT.get(mes_s.lower()[:3], 0)
            if not mes:
                return None
            ano = _dt.now().year
            if mes > _dt.now().month:
                ano -= 1
            return _date(ano, mes, dia)
        except Exception:
            return None

    IGNORAR_DESC = {
        'pagamento em', 'saldo restante', 'iof de', 'iof "',
        'pagamentos e financiamentos', 'fatura anterior',
        'pagamento recebido', 'total a pagar',
    }

    linhas_brutas = []
    erros = []

    try:
        raw = arquivo.read()
        import io as _io
        todas_linhas = []
        with pdfplumber.open(_io.BytesIO(raw)) as pdf:
            for page in pdf.pages:
                txt = page.extract_text(layout=False) or ''
                for linha in txt.split('\n'):
                    if linha.strip():
                        todas_linhas.append(linha)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro ao ler PDF Nubank: {e}'})

    em_transacoes = False
    em_pagamentos = False

    # PadrÃ£o Nubank:
    # "02 MAI â€¢â€¢â€¢â€¢ 9523 Dl *Temucom Temu Br Xb - Parcela 2/6 R$ 46,78"
    # "03 MAI â€¢â€¢â€¢â€¢ 9523 Uber_credit R$ 335,00"
    # "02 MAI Raia Drogasil - NuPay - Parcela 2/3 R$ 898,91"
    # "28 MAI â€¢â€¢â€¢â€¢ 9523 Openai R$ 52,29"  (pode ter linha extra com conversÃ£o)
    PAT_NU = _re.compile(
        r'^(\d{1,2})\s+([A-Za-zÃ€-Ãº]{3})\s+'   # DD MMM
        r'(?:[\â€¢\.]{4}\s*\d{4}\s+|nu\s+)?'      # cartÃ£o opcional (â€¢â€¢â€¢â€¢ XXXX ou NU)
        r'(.+?)'                                  # descriÃ§Ã£o
        r'(?:\s+-\s+Parcela\s+(\d+)/(\d+))?'    # parcela opcional
        r'\s+R\$\s+([\d\.]+,\d{2})\s*$'         # R$ valor
    , _re.IGNORECASE)

    # Segunda forma: sem "R$" na mesma linha (Openai tem linha extra)
    PAT_NU2 = _re.compile(
        r'^(\d{1,2})\s+([A-Za-zÃ€-Ãº]{3})\s+'
        r'(?:[\â€¢\.]{4}\s*\d{4}\s+|nu\s+)?'
        r'(.+?)\s*$'
    , _re.IGNORECASE)

    linha_anterior = None

    for idx, linha in enumerate(todas_linhas):
        linha_strip = linha.strip()
        l_lower = linha_strip.lower()

        # Detectar inÃ­cio de transaÃ§Ãµes
        if _re.search(r'transaÃ§Ãµes\s+de\s+\d{2}\s+\w+\s+a\s+\d{2}\s+\w+', l_lower) or \
           _re.search(r'transacoes\s+de', l_lower):
            em_transacoes = True
            em_pagamentos = False
            continue

        # Detectar seÃ§Ã£o de pagamentos (ignorar)
        if 'pagamentos e financiamentos' in l_lower:
            em_pagamentos = True
            continue

        if not em_transacoes or em_pagamentos:
            linha_anterior = linha_strip
            continue

        # Ignorar linhas de metadados
        if any(ign in l_lower for ign in IGNORAR_DESC):
            linha_anterior = linha_strip
            continue

        # Ignorar subtotais de portador (ex: "Orlei O Barbosa R$ 3.504,61")
        if _re.match(r'^[A-Za-zÃ€-Ãº\s]+R\$\s+[\d\.]+,\d{2}$', linha_strip):
            linha_anterior = linha_strip
            continue

        # Ignorar linhas de conversÃ£o cambial
        if 'usd' in l_lower or 'conversÃ£o' in l_lower or 'conversao' in l_lower:
            linha_anterior = linha_strip
            continue

        # Ignorar valores negativos (pagamentos, IOF de volta)
        if _re.search(r'[âˆ’\-]R\$', linha_strip) or _re.match(r'^-R\$', linha_strip):
            linha_anterior = linha_strip
            continue

        m = PAT_NU.match(linha_strip)
        if not m:
            linha_anterior = linha_strip
            continue

        dia_s    = m.group(1)
        mes_s    = m.group(2)
        descricao = m.group(3).strip().rstrip(' -').strip()
        parc_a   = m.group(4)
        parc_t   = m.group(5)
        valor_s  = m.group(6)

        # Ignorar IOF
        if 'iof' in descricao.lower():
            linha_anterior = linha_strip
            continue

        data_compra = _parse_data_nu(dia_s, mes_s)
        if not data_compra:
            erros.append(f'Data invÃ¡lida: "{dia_s} {mes_s}" em "{descricao}"')
            linha_anterior = linha_strip
            continue

        valor_parcela = _val(valor_s)
        if valor_parcela <= 0:
            linha_anterior = linha_strip
            continue

        parcela_atual = int(parc_a) if parc_a else 1
        num_parcelas  = int(parc_t) if parc_t else 1

        linhas_brutas.append({
            'descricao': descricao,
            'valor_parcela': valor_parcela,
            'data_compra': data_compra,
            'parcela_atual': parcela_atual,
            'num_parcelas': num_parcelas,
            'categoria': '',
        })
        linha_anterior = linha_strip

    # Calcular valor total e verificar duplicatas
    linhas = []
    for lb in linhas_brutas:
        descricao     = lb['descricao']
        valor_parcela = lb['valor_parcela']
        data_compra   = lb['data_compra']
        parcela_atual = lb['parcela_atual']
        num_parcelas  = lb['num_parcelas']
        valor_total   = round(valor_parcela * num_parcelas, 2)

        duplicata = Despesa.query.filter_by(
            user_id=current_user.id,
            descricao=descricao,
            meio_pagamento_id=cartao_id,
            data_pagamento=data_compra,
        ).filter(Despesa.valor.between(valor_total - 0.01, valor_total + 0.01)).first()

        linhas.append({
            'descricao': descricao,
            'valor': valor_total,
            'valor_parcela': round(valor_parcela, 2),
            'data_compra': data_compra.strftime('%d/%m/%Y'),
            'data_pagamento': data_compra.strftime('%d/%m/%Y'),
            'parcela_atual': parcela_atual,
            'num_parcelas': num_parcelas,
            'categoria': '',
            'duplicata': bool(duplicata),
        })

    if not linhas and not erros:
        return jsonify({'success': False,
                        'error': 'Nenhuma transaÃ§Ã£o encontrada. Verifique se Ã© uma fatura Nubank.'})

    return jsonify({
        'success': True,
        'linhas': linhas,
        'erros': erros,
        'cartao_nome': cartao.nome,
        'cartao_id': cartao_id,
    })


def _processar_pdf_santander(arquivo, cartao_id, cartao, fechamento):
    """
    Extrai transaÃ§Ãµes de um PDF de fatura do Santander.
    Suporta seÃ§Ãµes: Parcelamentos e Despesas, mÃºltiplos portadores.
    Ignora pagamentos/crÃ©ditos (valores negativos ou seÃ§Ã£o 'Pagamento e Demais CrÃ©ditos').
    """
    import re as _re
    from datetime import datetime as _dt, date as _date
    from dateutil.relativedelta import relativedelta as _rd

    try:
        import pdfplumber
    except ImportError:
        return jsonify({'success': False,
                        'error': 'Biblioteca pdfplumber nÃ£o instalada no servidor.'})

    MESES_PT = {'jan':1,'fev':2,'mar':3,'abr':4,'mai':5,'jun':6,
                'jul':7,'ago':8,'set':9,'out':10,'nov':11,'dez':12}

    def _val(s):
        s = str(s or '').strip().replace(' ', '')
        if not s or s == '-':
            return 0.0
        s = s.replace('.', '').replace(',', '.')
        try:
            return float(s)
        except Exception:
            return 0.0

    def _parse_parc(s):
        s = str(s or '').strip().lower()
        if not s or s in ('', '-'):
            return 1, 1
        m = _re.match(r'^(\d+)/(\d+)$', s)
        if m:
            return int(m.group(1)), int(m.group(2))
        # "07/12" jÃ¡ Ã© numÃ©rico â†’ tratado acima
        # Tentar mÃªs abreviado: "07/dez"
        m2 = _re.match(r'^(\d+)/([a-z]{3})$', s)
        if m2:
            mes = MESES_PT.get(m2.group(2)[:3], 1)
            return int(m2.group(1)), mes
        return 1, 1

    ano_atual = _dt.now().year

    def _parse_data(s):
        """dd/mm â†’ date com ano inferido"""
        s = str(s or '').strip()
        m = _re.match(r'^(\d{1,2})/(\d{2})$', s)
        if m:
            dia, mes = int(m.group(1)), int(m.group(2))
            # Se mÃªs > mÃªs atual, provavelmente ano passado
            ano = ano_atual if mes <= _dt.now().month else ano_atual - 1
            try:
                return _date(ano, mes, dia)
            except Exception:
                pass
        # dd/mm/yyyy
        m2 = _re.match(r'^(\d{1,2})/(\d{2})/(\d{4})$', s)
        if m2:
            try:
                return _dt.strptime(s, '%d/%m/%Y').date()
            except Exception:
                pass
        return None

    linhas_brutas = []
    erros = []

    try:
        raw = arquivo.read()
        import io as _io
        # Extrair palavras com coordenadas para separar as duas colunas do PDF
        todas_linhas = []
        with pdfplumber.open(_io.BytesIO(raw)) as pdf:
            for page in pdf.pages:
                largura = page.width
                meio = largura / 2

                # Extrair coluna esquerda e direita separadamente
                col_esq = page.within_bbox((0, 0, meio, page.height))
                col_dir = page.within_bbox((meio, 0, largura, page.height))

                for col in (col_esq, col_dir):
                    txt = col.extract_text(layout=False) or ''
                    for linha in txt.split('\n'):
                        if linha.strip():
                            todas_linhas.append(linha)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro ao ler PDF: {e}'})

    IGNORAR_DESC = {
        'deb autom de fatura', 'pagamento fatura', 'pagto fatura',
        'anuidade diferenciada', 'saldo anterior', 'pagto. por deb',
        'estorno tarifa', 'pagamento fatura qr', 'deb autom',
        'cotacao dolar', 'cotaÃ§Ã£o dolar', 'valor total',
        'saldo desta fatura', 'total despesas', 'total de pagamentos',
        'total de creditos', 'compras parceladas',
    }

    # PadrÃ£o: [Ã­cone] data descriÃ§Ã£o [parcela] valor [valorUS$]
    PAT_TRANS = _re.compile(
        r'^(?:[\d@]\s{1,3})?'           # prefixo Ã­cone opcional (3, 2, @)
        r'(\d{1,2}/\d{2})\s+'          # data dd/mm
        r'(.+?)\s+'                     # descriÃ§Ã£o
        r'(?:(\d{2}/\d{2})\s+)?'       # parcela xx/xx opcional
        r'(-?[\d\.]+,\d{2})'            # valor R$
        r'(?:\s+[\d\.]+,\d{2})?'       # valor US$ opcional
        r'\s*$'
    )

    em_parcelamentos = False
    em_despesas = False
    em_pagamentos = False

    for linha in todas_linhas:
        linha_strip = linha.strip()
        if not linha_strip:
            continue
        l_lower = linha_strip.lower()

        # â”€â”€ Detectar seÃ§Ãµes â”€â”€
        if any(x in l_lower for x in ('pagamento e demais cr', 'pagamento e demais crÃ©d')):
            em_pagamentos, em_parcelamentos, em_despesas = True, False, False
            continue
        if l_lower.rstrip() == 'parcelamentos' or (
                'parcelamentos' in l_lower and len(linha_strip) < 20):
            em_parcelamentos, em_despesas, em_pagamentos = True, False, False
            continue
        if l_lower.rstrip() == 'despesas' or (
                l_lower.startswith('despesas') and len(linha_strip) < 15):
            em_despesas, em_parcelamentos, em_pagamentos = True, False, False
            continue
        if l_lower.startswith('valor total'):
            em_parcelamentos = em_despesas = em_pagamentos = False
            continue
        if _re.search(r'xxxx\s+xxxx', l_lower):
            em_parcelamentos = em_despesas = em_pagamentos = False
            continue
        if 'compra' in l_lower and 'data' in l_lower and 'descri' in l_lower:
            continue  # cabeÃ§alho

        if not (em_parcelamentos or em_despesas) or em_pagamentos:
            continue

        m = PAT_TRANS.match(linha_strip)
        if not m:
            continue

        data_str  = m.group(1)
        descricao = m.group(2).strip()
        parcela_s = (m.group(3) or '').strip()
        valor_s   = m.group(4)

        desc_low = descricao.lower()
        if any(ign in desc_low for ign in IGNORAR_DESC):
            continue

        valor_parcela = _val(valor_s)
        if valor_parcela <= 0:
            continue

        data_compra = _parse_data(data_str)
        if not data_compra:
            erros.append(f'Data invÃ¡lida: "{data_str}" em "{descricao}"')
            continue

        parcela_atual, num_parcelas = _parse_parc(parcela_s) if parcela_s else (1, 1)

        linhas_brutas.append({
            'descricao': descricao,
            'valor_parcela': valor_parcela,
            'data_compra': data_compra,
            'parcela_atual': parcela_atual,
            'num_parcelas': num_parcelas,
            'categoria': '',
        })

    # â”€â”€ Calcular valor total e verificar duplicatas â”€â”€
    linhas = []
    for lb in linhas_brutas:
        descricao    = lb['descricao']
        valor_parcela = lb['valor_parcela']
        data_compra  = lb['data_compra']
        parcela_atual = lb['parcela_atual']
        num_parcelas  = lb['num_parcelas']
        valor_total  = round(valor_parcela * num_parcelas, 2)

        duplicata = Despesa.query.filter_by(
            user_id=current_user.id,
            descricao=descricao,
            meio_pagamento_id=cartao_id,
            data_pagamento=data_compra,
        ).filter(Despesa.valor.between(valor_total - 0.01, valor_total + 0.01)).first()

        linhas.append({
            'descricao': descricao,
            'valor': valor_total,
            'valor_parcela': round(valor_parcela, 2),
            'data_compra': data_compra.strftime('%d/%m/%Y'),
            'data_pagamento': data_compra.strftime('%d/%m/%Y'),
            'parcela_atual': parcela_atual,
            'num_parcelas': num_parcelas,
            'categoria': '',
            'duplicata': bool(duplicata),
        })

    if not linhas and not erros:
        return jsonify({'success': False,
                        'error': 'Nenhuma transaÃ§Ã£o encontrada no PDF. '
                                 'Verifique se Ã© uma fatura Santander.'})

    return jsonify({
        'success': True,
        'linhas': linhas,
        'erros': erros,
        'cartao_nome': cartao.nome,
        'cartao_id': cartao_id,
    })


@config_bp.route('/importar-fatura-cartao/processar', methods=['POST'])
@login_required
@nao_free_required
def processar_fatura_cartao():
    """Processa o CSV enviado e retorna os dados para revisÃ£o"""
    import io, csv
    from werkzeug.utils import secure_filename

    cartao_id = request.form.get('cartao_id', type=int)
    if not cartao_id:
        return jsonify({'success': False, 'error': 'Selecione um cartÃ£o.'})

    cartao = MeioPagamento.query.filter_by(
        id=cartao_id, user_id=current_user.id, tipo='cartao'
    ).first()
    if not cartao:
        return jsonify({'success': False, 'error': 'CartÃ£o nÃ£o encontrado.'})

    fechamento = FechamentoCartao.query.filter_by(meio_pagamento_id=cartao_id).first()

    arquivo = request.files.get('arquivo')
    if not arquivo:
        return jsonify({'success': False, 'error': 'Envie um arquivo CSV ou PDF.'})

    nome_arquivo = arquivo.filename.lower()

    # â”€â”€ Parsing PDF Santander â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if nome_arquivo.endswith('.pdf'):
        # Detectar banco: 1) pelo nome do arquivo, 2) pelo texto extraÃ­do
        eh_nubank = 'nubank' in nome_arquivo.lower()

        if not eh_nubank:
            try:
                import pdfplumber, io as _io2
                raw_peek = arquivo.read()
                arquivo.seek(0)
                with pdfplumber.open(_io2.BytesIO(raw_peek)) as pdf_peek:
                    txt_p1 = (pdf_peek.pages[0].extract_text() or '').lower() if pdf_peek.pages else ''
                eh_nubank = ('nubank' in txt_p1 or 'nu pagamentos' in txt_p1
                             or 'nupay' in txt_p1 or 'nu.com' in txt_p1
                             or 'transaÃ§Ãµes de' in txt_p1)
            except Exception:
                pass

        if eh_nubank:
            return _processar_pdf_nubank(arquivo, cartao_id, cartao, fechamento)
        else:
            return _processar_pdf_santander(arquivo, cartao_id, cartao, fechamento)

    if not nome_arquivo.endswith('.csv'):
        return jsonify({'success': False, 'error': 'Formato nÃ£o suportado. Envie CSV ou PDF.'})

    # Detectar encoding
    raw = arquivo.read()
    for enc in ('utf-8-sig', 'latin-1', 'cp1252'):
        try:
            texto = raw.decode(enc)
            break
        except Exception:
            continue
    else:
        return jsonify({'success': False, 'error': 'Encoding do arquivo nÃ£o reconhecido.'})

    # Detectar separador
    amostra = texto[:2000]
    sep = ';' if amostra.count(';') > amostra.count(',') else ','

    # â”€â”€ Detectar e converter formato "extrato bancÃ¡rio" â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # CabeÃ§alho esperado: Data;HistÃ³rico;;Valor (US$);Valor(R$)
    import unicodedata, re as _re

    def _norm(s):
        s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()
        return s

    primeira_linha = texto.strip().split('\n')[0]
    colunas_norm = [_norm(c) for c in primeira_linha.split(sep)]

    FORMATO_EXTRATO = (
        'data' in colunas_norm and
        'historico' in colunas_norm and
        any('valor' in c and 'r$' in c.replace('(', '').replace(')', '') for c in colunas_norm)
    )

    if FORMATO_EXTRATO:
        # Converter para o formato padrÃ£o do importador
        # Regra de parcela: extrair "X/Y" do final do histÃ³rico
        def _extrair_parcela(historico):
            """Extrai parcela do histÃ³rico. Ex: 'PETZ DIGITAL 1/2' â†’ ('PETZ DIGITAL', '1/2')"""
            m = _re.search(r'\s+(\d+/\d+)\s*$', historico.strip())
            if m:
                descricao = historico[:m.start()].strip()
                parcela = m.group(1)
                return descricao, parcela
            return historico.strip(), 'Ãºnica'

        # Descobrir ano atual para completar a data (formato dd/mm sem ano)
        from datetime import datetime as _dt_conv, date as _date_conv
        ano_atual = _dt_conv.now().year

        linhas_conv = []
        reader_ext = csv.DictReader(io.StringIO(texto), delimiter=sep)
        for row in reader_ext:
            cols = {_norm(k): v.strip() for k, v in row.items() if k}

            # Data: "24/05" â†’ completar com ano
            data_raw = cols.get('data', '').strip()
            if not data_raw or not _re.match(r'\d{1,2}/\d{1,2}', data_raw):
                continue  # linhas de total/resumo

            partes_data = data_raw.split('/')
            if len(partes_data) == 2:
                try:
                    dia, mes = int(partes_data[0]), int(partes_data[1])
                    # Se mÃªs jÃ¡ passou no ano atual, pode ser ano passado
                    data_str = f'{dia:02d}/{mes:02d}/{ano_atual}'
                    # Validar
                    _dt_conv.strptime(data_str, '%d/%m/%Y')
                except Exception:
                    continue
            elif len(partes_data) == 3:
                data_str = data_raw
            else:
                continue

            # HistÃ³rico e parcela
            historico_raw = cols.get('historico', '').strip()
            if not historico_raw or historico_raw.upper() in ('SALDO ANTERIOR', 'PAGTO. POR DEB EM C/C'):
                continue

            descricao, parcela = _extrair_parcela(historico_raw)

            # Valor R$ â€” busca coluna que contenha "r$" (nÃ£o "us$")
            valor_raw = ''
            for k, v in cols.items():
                if 'valor' in k and 'r$' in k and v:
                    valor_raw = v
                    break
            # fallback: Ãºltima coluna com "valor"
            if not valor_raw:
                for k, v in reversed(list(cols.items())):
                    if 'valor' in k and v:
                        valor_raw = v
                        break
            if not valor_raw:
                continue
            try:
                valor_f = float(valor_raw.replace('.', '').replace(',', '.'))
            except Exception:
                continue
            if valor_f <= 0:
                continue  # ignora estornos/pagamentos

            linhas_conv.append({
                'Data de Compra': data_str,
                'DescriÃ§Ã£o': descricao,
                'Parcela': parcela,
                'Valor (em R$)': str(valor_f),
                'Categoria': '',
            })

        # Reescrever texto como CSV padrÃ£o
        saida = io.StringIO()
        writer_conv = csv.DictWriter(saida,
            fieldnames=['Data de Compra', 'DescriÃ§Ã£o', 'Parcela', 'Valor (em R$)', 'Categoria'],
            delimiter=';')
        writer_conv.writeheader()
        writer_conv.writerows(linhas_conv)
        texto = saida.getvalue()
        sep = ';'
    # â”€â”€ Fim conversÃ£o extrato bancÃ¡rio â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    reader = csv.DictReader(io.StringIO(texto), delimiter=sep)

    from datetime import datetime as _dt, date as _date
    from dateutil.relativedelta import relativedelta as _rd

    # Meses abreviados em PT para converter "07/dez" â†’ parcela_atual=7
    MESES_PT = {'jan':1,'fev':2,'mar':3,'abr':4,'mai':5,'jun':6,
                'jul':7,'ago':8,'set':9,'out':10,'nov':11,'dez':12}

    def _parse_valor(s):
        """Valor no CSV usa ponto como decimal: 60.48 â†’ 60.48, nÃ£o 6048"""
        s = s.strip().replace(' ', '')
        if not s:
            return 0.0
        # Se tem vÃ­rgula â†’ formato BR com ponto milhar: 1.234,56 â†’ 1234.56
        if ',' in s:
            s = s.replace('.', '').replace(',', '.')
        # Caso contrÃ¡rio ponto jÃ¡ Ã© decimal: 60.48 â†’ 60.48
        return float(s)

    def _parse_parcela(s):
        """
        Retorna (parcela_atual, num_parcelas).
        Formatos:
          "07/dez" â†’ (7, 12)  â€” parcela 7 de 12 (dez = dezembro = mÃªs 12 = 12 parcelas)
          "02/ago" â†’ (2, 8)   â€” parcela 2 de 8  (ago = agosto  = mÃªs 8  = 8 parcelas)
          "1/10"   â†’ (1, 10)  â€” parcela 1 de 10 (nÃºmero explÃ­cito)
          "Ãºnica"  â†’ (1, 1)
        """
        s = s.strip().lower()
        if not s or s in ('unica', 'Ãºnica', '-', ''):
            return 1, 1
        if '/' in s:
            partes = s.split('/')
            try:
                atual = int(partes[0])
            except ValueError:
                return 1, 1
            total_str = partes[1].strip()
            if total_str.isdigit():
                return atual, int(total_str)
            # mÃªs abreviado PT: jan=1 â€¦ dez=12 â†’ esse nÃºmero Ã© o total de parcelas
            mes_num = MESES_PT.get(total_str[:3])
            if mes_num:
                return atual, mes_num
            return atual, atual  # fallback: total = atual
        try:
            return int(s), 1
        except ValueError:
            return 1, 1

    # 1Âª passagem: ler todas as linhas brutas
    linhas_brutas = []
    erros = []

    for i, row in enumerate(reader):
        cols = {_norm(k): v for k, v in row.items()}

        data_raw = (cols.get('data de compra') or cols.get('data') or cols.get('date') or '').strip()
        try:
            if '/' in data_raw:
                data_compra = _dt.strptime(data_raw, '%d/%m/%Y').date()
            elif '-' in data_raw:
                data_compra = _dt.strptime(data_raw, '%Y-%m-%d').date()
            else:
                erros.append(f'Linha {i+2}: data invÃ¡lida "{data_raw}"')
                continue
        except Exception:
            erros.append(f'Linha {i+2}: data invÃ¡lida "{data_raw}"')
            continue

        descricao = (cols.get('descricao') or cols.get('description') or
                     cols.get('estabelecimento') or cols.get('nome') or '').strip()

        valor_raw = (cols.get('valor (em r$)') or cols.get('valor') or
                     cols.get('value') or cols.get('amount') or '0').strip()
        try:
            valor_parcela = _parse_valor(valor_raw)
        except Exception:
            erros.append(f'Linha {i+2}: valor invÃ¡lido "{valor_raw}"')
            continue

        if valor_parcela <= 0:
            continue  # ignora estornos/pagamentos

        parcela_raw = (cols.get('parcela') or cols.get('parcelas') or 'Ãºnica').strip()
        parcela_atual, num_parcelas = _parse_parcela(parcela_raw)

        cat_raw = (cols.get('categoria') or cols.get('category') or 'Outros').strip()

        linhas_brutas.append({
            'descricao': descricao,
            'valor_parcela': valor_parcela,
            'data_compra': data_compra,
            'parcela_atual': parcela_atual,
            'num_parcelas': num_parcelas,
            'categoria': cat_raw,
        })

    # 3Âª passagem: calcular valor total e datas de pagamento
    linhas = []
    for lb in linhas_brutas:
        descricao   = lb['descricao']
        valor_parcela = lb['valor_parcela']
        data_compra = lb['data_compra']
        parcela_atual = lb['parcela_atual']
        num_parcelas  = lb['num_parcelas']
        cat_raw       = lb['categoria']

        # Cada linha do CSV mostra o valor de UMA parcela.
        # Valor total da compra = valor_parcela Ã— num_parcelas.
        # Data = data da compra original (nÃ£o a data de vencimento da parcela atual).
        valor_total = round(valor_parcela * num_parcelas, 2)
        data_pagamento = data_compra  # data original da compra

        # Verificar duplicata: mesma descriÃ§Ã£o + cartÃ£o + valor_parcela + data_pagamento
        duplicata = Despesa.query.filter_by(
            user_id=current_user.id,
            descricao=descricao,
            meio_pagamento_id=cartao_id,
            data_pagamento=data_pagamento,
        ).filter(Despesa.valor.between(valor_total - 0.01, valor_total + 0.01)).first()

        linhas.append({
            'descricao': descricao,
            'valor': valor_total,                    # valor total = parcela Ã— num_parcelas
            'valor_parcela': round(valor_parcela, 2),# valor de cada parcela (informativo)
            'data_compra': data_compra.strftime('%d/%m/%Y'),
            'data_pagamento': data_pagamento.strftime('%d/%m/%Y'),
            'parcela_atual': parcela_atual,
            'num_parcelas': num_parcelas,
            'categoria': cat_raw,
            'duplicata': bool(duplicata),
        })

    return jsonify({
        'success': True,
        'linhas': linhas,
        'erros': erros,
        'cartao_nome': cartao.nome,
        'cartao_id': cartao_id,
    })


@config_bp.route('/importar-fatura-cartao/importar', methods=['POST'])
@login_required
@nao_free_required
def importar_fatura_cartao_confirmar():
    """Importa os itens selecionados para o banco"""
    from datetime import datetime as _dt

    data = request.get_json(silent=True, force=True) or {}
    items = data.get('items', [])
    cartao_id = data.get('cartao_id')

    if not cartao_id:
        return jsonify({'success': False, 'error': 'CartÃ£o nÃ£o informado.'})

    cartao = MeioPagamento.query.filter_by(
        id=cartao_id, user_id=current_user.id, tipo='cartao'
    ).first()
    if not cartao:
        return jsonify({'success': False, 'error': 'CartÃ£o nÃ£o encontrado.'})

    importados = 0
    erros = []

    for item in items:
        try:
            # Categoria â€” cria se nÃ£o existir
            cat_nome = (item.get('categoria') or 'Outros').strip()
            categoria = CategoriaDespesa.query.filter_by(
                nome=cat_nome, user_id=current_user.id
            ).first()
            if not categoria:
                categoria = CategoriaDespesa(nome=cat_nome, ativo=True, user_id=current_user.id)
                db.session.add(categoria)
                db.session.flush()

            # Usa data da compra como data de pagamento (data original da transaÃ§Ã£o)
            data_pag = _dt.strptime(item['data_compra'], '%d/%m/%Y').date()

            nova = Despesa(
                descricao=item['descricao'],
                valor=float(item['valor']),
                data_pagamento=data_pag,
                num_parcelas=int(item.get('num_parcelas', 1)),
                categoria_id=categoria.id,
                meio_pagamento_id=cartao_id,
                user_id=current_user.id,
            )
            db.session.add(nova)
            importados += 1
        except Exception as e:
            erros.append(f'{item.get("descricao","?")}: {e}')

    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'{importados} despesa(s) importada(s) com sucesso!',
        'erros': erros,
    })

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from routes.auth import admin_required, gerente_required, gerente_only_required
from models import db, User, CategoriaDespesa, CategoriaReceita, MeioPagamento, MeioRecebimento, Orcamento, FechamentoCartao, Configuracao, Despesa
from utils.supabase_client import SupabaseClient
import json
from datetime import datetime
import os

config_bp = Blueprint('config', __name__)

@config_bp.route('/importar-dados-antigos', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_dados_antigos():
    """Importar dados do sistema antigo (apenas admin)"""
    if request.method == 'POST':
        from utils.importador import importar_dados_antigos, importar_fluxo_caixa
        from flask import current_app
        
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
@gerente_required
def usuarios():
    """Gerenciar usuários (admin e gerente)"""
    # Níveis que o gerente pode atribuir (não pode criar/promover a admin/gerente)
    NIVEIS_GERENTE = ('pro', 'promax', 'free')
    eh_admin = current_user.is_admin()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'ativar_desativar':
            id = int(request.form.get('id'))
            user = User.query.get(id)
            if user and user.id == current_user.id:
                flash('Você não pode desativar sua própria conta!', 'danger')
            elif user and (eh_admin or user.nivel_acesso in NIVEIS_GERENTE):
                user.ativo = not user.ativo
                db.session.commit()
                flash(f'Usuário {"ativado" if user.ativo else "desativado"}!', 'success')
            else:
                flash('Sem permissão para esta ação.', 'danger')

        elif action == 'alterar_nivel':
            id = int(request.form.get('id'))
            nivel = request.form.get('nivel')
            user = User.query.get(id)
            # Gerente só pode atribuir níveis não-admin
            if not eh_admin and nivel not in NIVEIS_GERENTE:
                flash('Você não pode atribuir este nível.', 'danger')
            elif user and user.id != current_user.id:
                user.nivel_acesso = nivel
                db.session.commit()
                flash('Nível de acesso alterado!', 'success')

        elif action == 'alterar_modo_conta':
            id = int(request.form.get('id'))
            modo = request.form.get('modo_conta')
            user = User.query.get(id)
            if user and modo in ('pf', 'pf_pj'):
                user.modo_conta = modo
                db.session.commit()
                flash('Modo de conta alterado!', 'success')

        return redirect(url_for('config.usuarios'))

    # Gerente vê apenas usuários não-admin; admin vê todos
    if eh_admin:
        usuarios = User.query.order_by(User.username).all()
    else:
        usuarios = User.query.filter(
            User.nivel_acesso.in_(NIVEIS_GERENTE)
        ).order_by(User.username).all()

    return render_template('config/usuarios.html', usuarios=usuarios, eh_admin=eh_admin)


@config_bp.route('/usuarios/<int:id>/exportar-dados')
@login_required
@admin_required
def exportar_dados_usuario(id):
    """Exportar todos os dados de um usuário para Excel antes de excluir"""
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    from models import Despesa, Receita, CategoriaDespesa, CategoriaReceita, MeioPagamento, MeioRecebimento, Orcamento

    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Você não pode exportar/excluir sua própria conta!', 'danger')
        return redirect(url_for('config.usuarios'))

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Despesas
        despesas = Despesa.query.filter_by(user_id=id).all()
        dados_d = [{'Data': d.data_pagamento.strftime('%d/%m/%Y'), 'Descrição': d.descricao,
                    'Categoria': d.categoria.nome, 'Meio de Pagamento': d.meio_pagamento.nome,
                    'Valor': d.valor, 'Parcelas': d.num_parcelas,
                    'Entidade': getattr(d, 'entidade', '')} for d in despesas]
        pd.DataFrame(dados_d).to_excel(writer, index=False, sheet_name='Despesas')

        # Receitas
        receitas = Receita.query.filter_by(user_id=id).all()
        dados_r = [{'Data': r.data_recebimento.strftime('%d/%m/%Y'), 'Descrição': r.descricao,
                    'Categoria': r.categoria.nome, 'Meio de Recebimento': r.meio_recebimento.nome,
                    'Valor': r.valor, 'Parcelas': r.num_parcelas,
                    'Entidade': getattr(r, 'entidade', '')} for r in receitas]
        pd.DataFrame(dados_r).to_excel(writer, index=False, sheet_name='Receitas')

        # Categorias despesa
        cats_d = [{'Nome': c.nome, 'Ativo': c.ativo}
                  for c in CategoriaDespesa.query.filter_by(user_id=id).all()]
        pd.DataFrame(cats_d).to_excel(writer, index=False, sheet_name='CategoriasDespesa')

        # Categorias receita
        cats_r = [{'Nome': c.nome, 'Ativo': c.ativo}
                  for c in CategoriaReceita.query.filter_by(user_id=id).all()]
        pd.DataFrame(cats_r).to_excel(writer, index=False, sheet_name='CategoriasReceita')

        # Meios de pagamento
        meios_p = [{'Nome': m.nome, 'Tipo': m.tipo, 'Ativo': m.ativo}
                   for m in MeioPagamento.query.filter_by(user_id=id).all()]
        pd.DataFrame(meios_p).to_excel(writer, index=False, sheet_name='MeiosPagamento')

        # Meios de recebimento
        meios_r = [{'Nome': m.nome, 'Ativo': m.ativo}
                   for m in MeioRecebimento.query.filter_by(user_id=id).all()]
        pd.DataFrame(meios_r).to_excel(writer, index=False, sheet_name='MeiosRecebimento')

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'dados_{user.username}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )


@config_bp.route('/usuarios/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_usuario(id):
    """Excluir usuário e todos os seus dados"""
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Você não pode excluir sua própria conta!', 'danger')
        return redirect(url_for('config.usuarios'))
    if user.nivel_acesso == 'admin':
        flash('Não é possível excluir outro administrador!', 'danger')
        return redirect(url_for('config.usuarios'))

    # Excluir dados sem cascade automático
    from models import (CategoriaDespesa, CategoriaReceita, MeioPagamento,
                        MeioRecebimento, Orcamento, FechamentoCartao,
                        BalancoMensal, EventoCaixaAvulso, ApiKey)
    ApiKey.query.filter_by(user_id=id).delete()
    Orcamento.query.filter_by(user_id=id).delete()
    # FechamentoCartao está ligado a MeioPagamento, não diretamente ao user
    meios_ids = [m.id for m in MeioPagamento.query.filter_by(user_id=id).all()]
    if meios_ids:
        FechamentoCartao.query.filter(FechamentoCartao.meio_pagamento_id.in_(meios_ids)).delete(synchronize_session=False)
    BalancoMensal.query.filter_by(user_id=id).delete()
    EventoCaixaAvulso.query.filter_by(user_id=id).delete()
    # Despesas e receitas têm cascade no relacionamento do User
    # Categorias e meios têm user_id mas não cascade — excluir manualmente
    from models import Despesa, Receita
    Despesa.query.filter_by(user_id=id).delete()
    Receita.query.filter_by(user_id=id).delete()
    MeioPagamento.query.filter_by(user_id=id).delete()
    MeioRecebimento.query.filter_by(user_id=id).delete()
    CategoriaDespesa.query.filter_by(user_id=id).delete()
    CategoriaReceita.query.filter_by(user_id=id).delete()

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuário "{username}" e todos os seus dados foram excluídos!', 'success')
    return redirect(url_for('config.usuarios'))


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
                categoria = CategoriaDespesa.query.filter_by(nome=cat_nome).first()
                if not categoria:
                    categoria = CategoriaDespesa(nome=cat_nome, ativo=True)
                    db.session.add(categoria)
                    db.session.commit()
                
                # Verificar/Criar Meio de Pagamento
                mp_nome = item.get('meio_pagamento', 'Outros')
                meio_pagamento = MeioPagamento.query.filter_by(nome=mp_nome).first()
                if not meio_pagamento:
                    meio_pagamento = MeioPagamento(nome=mp_nome, tipo='outros', ativo=True)
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


@config_bp.route('/api-key', methods=['GET', 'POST'])
@login_required
@admin_required
def api_key():
    """Página de gerenciamento de API keys — exclusiva para admin."""
    from flask import session as flask_session
    from models import ApiKey, CategoriaReceita, ConfigSistema

    if request.method == 'POST':
        action  = request.form.get('action')
        user_id = int(request.form.get('user_id', current_user.id))

        if action == 'gerar':
            raw, key_hash, prefix = ApiKey.gerar_chave()
            ak = ApiKey.query.filter_by(user_id=user_id).first()
            if ak:
                ak.key_hash       = key_hash
                ak.key_prefix     = prefix
                ak.ativo          = True
                ak.data_criacao   = datetime.utcnow()
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
            ConfigSistema.set('limite_registros_free', str(limite))
            db.session.commit()
            flash(f'Limite Free atualizado para {limite} registros/mês.', 'success')
            return redirect(url_for('config.api_key'))

    from models import ApiKey, CategoriaReceita, ConfigSistema
    usuarios  = User.query.order_by(User.username).all()
    keys_map  = {ak.user_id: ak for ak in ApiKey.query.all()}
    raw_map   = {}
    for u in usuarios:
        k = flask_session.pop(f'api_key_raw_{u.id}', None)
        if k:
            raw_map[u.id] = k

    cat_despesas = CategoriaDespesa.query.filter_by(user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
    cat_receitas = CategoriaReceita.query.filter_by(user_id=current_user.id).order_by(CategoriaReceita.nome).all()
    meios_pag    = MeioPagamento.query.filter_by(user_id=current_user.id).order_by(MeioPagamento.nome).all()
    meios_rec    = MeioRecebimento.query.filter_by(user_id=current_user.id).order_by(MeioRecebimento.nome).all()
    limite_free  = int(ConfigSistema.get('limite_registros_free', '500') or 500)

    return render_template('config/api_key.html',
        usuarios=usuarios,
        keys_map=keys_map,
        raw_map=raw_map,
        cat_despesas=cat_despesas,
        cat_receitas=cat_receitas,
        meios_pag=meios_pag,
        meios_rec=meios_rec,
        limite_free=limite_free,
    )


@config_bp.route('/smtp-whatsapp', methods=['GET', 'POST'])
@login_required
@admin_required
def smtp_whatsapp():
    """Configurações de SMTP e WhatsApp"""
    from models import ConfigSistema
    if request.method == 'POST':
        for chave in ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password',
                      'smtp_from', 'whatsapp_token', 'whatsapp_phone_id']:
            valor = request.form.get(chave, '').strip()
            ConfigSistema.set(chave, valor)
        db.session.commit()
        flash('Configurações salvas!', 'success')
        return redirect(url_for('config.smtp_whatsapp'))
    _SMTP_KEYS = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password',
                  'smtp_from', 'smtp_secure', 'whatsapp_token', 'whatsapp_phone_id', 'webhook_whatsapp']
    cfg = {k: ConfigSistema.get(k, '') for k in _SMTP_KEYS}
    return render_template('config/smtp_whatsapp.html', cfg=cfg)


@config_bp.route('/openfinance')
@login_required
def openfinance():
    """OpenFinance / Pluggy"""
    return render_template('config/openfinance.html')


@config_bp.route('/openfinance/importar', methods=['POST'])
@login_required
def openfinance_import():
    flash('Funcionalidade OpenFinance não disponível nesta versão.', 'warning')
    return redirect(url_for('config.openfinance'))


@config_bp.route('/openfinance/confirmar', methods=['POST'])
@login_required
def openfinance_confirm():
    flash('Funcionalidade OpenFinance não disponível nesta versão.', 'warning')
    return redirect(url_for('config.openfinance'))


@config_bp.route('/openfinance/token')
@login_required
def openfinance_token():
    return jsonify({'token': None, 'error': 'não configurado'})

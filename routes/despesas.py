from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Despesa, Receita, CategoriaDespesa, MeioPagamento
from datetime import datetime, date
from sqlalchemy import extract, func
import re

def _verificar_limite_free(usuario):
    """Retorna (True, None) se pode registrar, (False, msg) se limite atingido."""
    if not usuario.is_free():
        return True, None
    limite = usuario.limite_registros_mensais()
    hoje   = datetime.now()
    total  = (
        Despesa.query.filter_by(user_id=usuario.id)
        .filter(extract('month', Despesa.data_registro) == hoje.month,
                extract('year',  Despesa.data_registro) == hoje.year).count()
        +
        Receita.query.filter_by(user_id=usuario.id)
        .filter(extract('month', Receita.data_registro) == hoje.month,
                extract('year',  Receita.data_registro) == hoje.year).count()
    )
    if total >= limite:
        return False, (f'Limite de {limite} registros mensais do plano Free atingido. '
                       f'Entre em contato com o administrador para fazer upgrade.')
    return True, None

def _parse_operador(valor_str):
    """Parse '>100', '<500', '>=200', '<=300', '=150' → (op, num) ou None"""
    if not valor_str:
        return None
    m = re.match(r'^(>=|<=|>|<|=)(\d+(?:[.,]\d+)?)$', valor_str.strip())
    if not m:
        return None
    op  = m.group(1)
    num = float(m.group(2).replace(',', '.'))
    return op, num

def _apply_op(query, col, valor_str):
    parsed = _parse_operador(valor_str)
    if not parsed:
        return query
    op, num = parsed
    if op == '>':  return query.filter(col > num)
    if op == '<':  return query.filter(col < num)
    if op == '>=': return query.filter(col >= num)
    if op == '<=': return query.filter(col <= num)
    if op == '=':  return query.filter(col == num)
    return query

despesas_bp = Blueprint('despesas', __name__)

@despesas_bp.route('/')
@login_required
def lista():
    """Listar despesas com filtros"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtros básicos
    busca             = request.args.get('busca', '').strip()
    categoria_busca   = request.args.get('categoria_busca', '').strip()
    meio_busca        = request.args.get('meio_busca', '').strip()
    valor_filtro      = request.args.get('valor_filtro', '').strip()
    parcelas_filtro   = request.args.get('parcelas_filtro', '').strip()
    # Compatibilidade legada
    categoria_id      = request.args.get('categoria_id', type=int)
    meio_pagamento_id = request.args.get('meio_pagamento_id', type=int)

    # Período (padrão: mes_atual)
    periodo     = request.args.get('periodo', 'mes_atual')
    data_inicio = request.args.get('data_inicio')
    data_fim    = request.args.get('data_fim')

    if periodo == 'mes_atual':
        hoje = datetime.now()
        import calendar
        ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
        data_inicio = date(hoje.year, hoje.month, 1).strftime('%Y-%m-%d')
        data_fim    = date(hoje.year, hoje.month, ultimo_dia).strftime('%Y-%m-%d')
    elif periodo == 'todos':
        data_inicio = None
        data_fim    = None

    # Query base
    query = Despesa.query.filter_by(user_id=current_user.id)

    # Busca na descrição
    if busca:
        query = query.filter(Despesa.descricao.ilike(f'%{busca}%'))

    # Categoria — busca por texto (novo) ou por ID (legado)
    if categoria_busca:
        query = query.join(CategoriaDespesa, Despesa.categoria_id == CategoriaDespesa.id)\
                     .filter(CategoriaDespesa.nome.ilike(f'%{categoria_busca}%'))
    elif categoria_id:
        query = query.filter_by(categoria_id=categoria_id)

    # Meio de pagamento — busca por texto (novo) ou por ID (legado)
    if meio_busca:
        query = query.join(MeioPagamento, Despesa.meio_pagamento_id == MeioPagamento.id)\
                     .filter(MeioPagamento.nome.ilike(f'%{meio_busca}%'))
    elif meio_pagamento_id:
        query = query.filter_by(meio_pagamento_id=meio_pagamento_id)

    # Filtro de datas
    if data_inicio:
        query = query.filter(Despesa.data_pagamento >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(Despesa.data_pagamento <= datetime.strptime(data_fim, '%Y-%m-%d').date())

    # Filtro de valor com operador
    query = _apply_op(query, Despesa.valor, valor_filtro)

    # Filtro de parcelas com operador
    query = _apply_op(query, Despesa.num_parcelas, parcelas_filtro)

    # Ordenar e paginar
    despesas = query.order_by(Despesa.data_pagamento.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Carregar opções (para compatibilidade com dropdowns legacy)
    categorias      = CategoriaDespesa.query.filter_by(ativo=True, user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
    meios_pagamento = MeioPagamento.query.filter_by(ativo=True, user_id=current_user.id).order_by(MeioPagamento.nome).all()

    filtros_url = {k: v for k, v in request.args.items() if k != 'page'}

    return render_template('despesas/lista.html',
                         despesas=despesas,
                         categorias=categorias,
                         meios_pagamento=meios_pagamento,
                         periodo=periodo,
                         data_inicio_filtro=data_inicio,
                         data_fim_filtro=data_fim,
                         filtros_url=filtros_url)

@despesas_bp.route('/criar', methods=['GET', 'POST'])
@login_required
def criar():
    """Criar nova despesa"""
    if request.method == 'POST':
        # Verificar limite Free
        ok, msg = _verificar_limite_free(current_user)
        if not ok:
            flash(msg, 'warning')
            return redirect(url_for('despesas.lista'))

        descricao = request.form.get('descricao')
        valor = float(request.form.get('valor').replace(',', '.'))
        categoria_id = int(request.form.get('categoria_id'))
        meio_pagamento_id = int(request.form.get('meio_pagamento_id'))
        num_parcelas = int(request.form.get('num_parcelas', 1))
        data_pagamento = datetime.strptime(request.form.get('data_pagamento'), '%Y-%m-%d').date()

        nova_despesa = Despesa(
            descricao=descricao,
            valor=valor,
            categoria_id=categoria_id,
            meio_pagamento_id=meio_pagamento_id,
            num_parcelas=num_parcelas,
            data_pagamento=data_pagamento,
            user_id=current_user.id
        )

        db.session.add(nova_despesa)
        db.session.commit()

        flash('Despesa cadastrada com sucesso!', 'success')
        return redirect(url_for('despesas.lista'))
    
    categorias = CategoriaDespesa.query.filter_by(ativo=True, user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
    meios_pagamento = MeioPagamento.query.filter_by(ativo=True, user_id=current_user.id).order_by(MeioPagamento.nome).all()

    return render_template('despesas/form.html',
                         categorias=categorias,
                         meios_pagamento=meios_pagamento,
                         hoje=datetime.now().date())

@despesas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar despesa existente"""
    despesa = Despesa.query.get_or_404(id)
    
    # Capturar filtros da URL para persistência
    filtros = {k: v for k, v in request.args.items()}
    
    # Verificar permissão - usuário só pode editar suas próprias despesas
    if despesa.user_id != current_user.id:
        flash('Você não tem permissão para editar esta despesa.', 'danger')
        return redirect(url_for('despesas.lista', **filtros))
    
    next_url = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        despesa.descricao = request.form.get('descricao')
        despesa.valor = float(request.form.get('valor').replace(',', '.'))
        despesa.categoria_id = int(request.form.get('categoria_id'))
        despesa.meio_pagamento_id = int(request.form.get('meio_pagamento_id'))
        despesa.num_parcelas = int(request.form.get('num_parcelas', 1))
        despesa.data_pagamento = datetime.strptime(request.form.get('data_pagamento'), '%Y-%m-%d').date()

        db.session.commit()
        flash('Despesa atualizada com sucesso!', 'success')

        if next_url:
            return redirect(next_url)

        filtros_redirect = {}
        _all_keys = ['periodo','data_inicio','data_fim','categoria_id','meio_pagamento_id',
                     'busca','categoria_busca','meio_busca','valor_filtro','parcelas_filtro','page']
        for key in _all_keys:
            val = request.form.get(f'filtro_{key}')
            if val:
                filtros_redirect[key] = val
        return redirect(url_for('despesas.lista', **filtros_redirect))

    categorias = CategoriaDespesa.query.filter_by(ativo=True, user_id=current_user.id).order_by(CategoriaDespesa.nome).all()
    meios_pagamento = MeioPagamento.query.filter_by(ativo=True, user_id=current_user.id).order_by(MeioPagamento.nome).all()

    return render_template('despesas/form.html',
                         despesa=despesa,
                         categorias=categorias,
                         meios_pagamento=meios_pagamento,
                         filtros=filtros,
                         next_url=next_url)

@despesas_bp.route('/nova-despesa-fatura', methods=['POST'])
@login_required
def nova_despesa_fatura():
    """Cria despesa a partir do modal de detalhes da fatura do cartão (via AJAX)"""
    try:
        data = request.get_json()

        cartao_id    = int(data['cartao_id'])
        categoria_id = int(data['categoria_id'])
        descricao    = (data.get('descricao') or '').strip()
        num_parcelas = max(1, int(data.get('num_parcelas', 1)))
        valor_parcela = float(str(data.get('valor_parcela', 0)).replace(',', '.'))
        valor_total  = round(valor_parcela * num_parcelas, 2)

        data_pagamento = datetime.strptime(data['data_pagamento'], '%Y-%m-%d').date()

        # Verificar se o cartão pertence ao usuário
        from models import MeioPagamento
        cartao = MeioPagamento.query.filter_by(id=cartao_id, user_id=current_user.id).first()
        if not cartao:
            return jsonify({'success': False, 'message': 'Cartão não encontrado.'})

        nova = Despesa(
            descricao=descricao or cartao.nome,
            valor=valor_total,
            categoria_id=categoria_id,
            meio_pagamento_id=cartao_id,
            num_parcelas=num_parcelas,
            data_pagamento=data_pagamento,
            user_id=current_user.id
        )
        db.session.add(nova)
        db.session.commit()

        return jsonify({'success': True, 'id': nova.id,
                        'message': f'Despesa cadastrada! Valor total: R$ {valor_total:.2f}'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@despesas_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    """Excluir despesa"""
    despesa = Despesa.query.get_or_404(id)
    
    # Verificar permissão - usuário só pode excluir suas próprias despesas
    if despesa.user_id != current_user.id:
        flash('Você não tem permissão para excluir esta despesa.', 'danger')
        return redirect(url_for('despesas.lista'))
    
    next_url = request.form.get('next')
    db.session.delete(despesa)
    db.session.commit()

    flash('Despesa excluída com sucesso!', 'success')
    return redirect(next_url if next_url else url_for('despesas.lista'))

@despesas_bp.route('/exportar')
@login_required
def exportar():
    """Exportar despesas para Excel"""
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    
    # Query base - todos os usuários veem apenas seus dados
    despesas = Despesa.query.filter_by(user_id=current_user.id).all()
    
    # Preparar dados
    dados = []
    for d in despesas:
        dados.append({
            'Data': d.data_pagamento.strftime('%d/%m/%Y'),
            'Descrição': d.descricao,
            'Categoria': d.categoria.nome,
            'Meio de Pagamento': d.meio_pagamento.nome,
            'Valor': d.valor,
            'Parcelas': d.num_parcelas,
            'Usuário': d.usuario.username
        })
    
    df = pd.DataFrame(dados)
    
    # Criar arquivo Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Despesas')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'despesas_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

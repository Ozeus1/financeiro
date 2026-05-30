from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from models import db, Despesa, Receita, CategoriaDespesa
from sqlalchemy import func, extract, or_
from datetime import datetime, timedelta
import calendar

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página inicial"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal do sistema"""
    hoje = datetime.now()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # Filtro de entidade (apenas para promax pf_pj)
    entidade_filtro = None
    if current_user.usa_separacao_pf_pj():
        entidade_filtro = request.args.get('entidade', '')  # '' = todas, 'pf', 'pj'

    # Query base
    if current_user.is_gerente():
        despesas_query = Despesa.query
        receitas_query = Receita.query
    else:
        despesas_query = Despesa.query.filter_by(user_id=current_user.id)
        receitas_query = Receita.query.filter_by(user_id=current_user.id)

    # Filtro de entidade: entidade == valor OU entidade IS NULL (cartão, sem separação)
    if entidade_filtro:
        despesas_query = despesas_query.filter(
            or_(Despesa.entidade == entidade_filtro, Despesa.entidade == None)
        )
        receitas_query = receitas_query.filter(
            or_(Receita.entidade == entidade_filtro, Receita.entidade == None)
        )

    # Total de despesas do mês
    total_despesas_mes = db.session.query(func.sum(Despesa.valor)).join(CategoriaDespesa).filter(
        extract('month', Despesa.data_pagamento) == mes_atual,
        extract('year', Despesa.data_pagamento) == ano_atual,
        func.lower(CategoriaDespesa.nome) != 'pagamentos'
    )
    if not current_user.is_gerente():
        total_despesas_mes = total_despesas_mes.filter(Despesa.user_id == current_user.id)
    if entidade_filtro:
        total_despesas_mes = total_despesas_mes.filter(
            or_(Despesa.entidade == entidade_filtro, Despesa.entidade == None)
        )
    total_despesas_mes = total_despesas_mes.scalar() or 0

    # Total de receitas do mês
    total_receitas_mes = db.session.query(func.sum(Receita.valor)).filter(
        extract('month', Receita.data_recebimento) == mes_atual,
        extract('year', Receita.data_recebimento) == ano_atual
    )
    if not current_user.is_gerente():
        total_receitas_mes = total_receitas_mes.filter(Receita.user_id == current_user.id)
    if entidade_filtro:
        total_receitas_mes = total_receitas_mes.filter(
            or_(Receita.entidade == entidade_filtro, Receita.entidade == None)
        )
    total_receitas_mes = total_receitas_mes.scalar() or 0

    saldo_mes = total_receitas_mes - total_despesas_mes

    # --- FLUXO DE CAIXA ---
    from models import MeioPagamento, EventoCaixaAvulso

    MEIOS_PAGAMENTO_CAIXA = ['Boleto', 'Dinheiro', 'PIX', 'Transferência', 'Débito em Conta']

    saidas_caixa_query = db.session.query(func.sum(Despesa.valor)).join(
        Despesa.meio_pagamento
    ).join(
        Despesa.categoria
    ).filter(
        extract('month', Despesa.data_pagamento) == mes_atual,
        extract('year', Despesa.data_pagamento) == ano_atual,
        or_(
            func.lower(MeioPagamento.nome).in_([m.lower() for m in MEIOS_PAGAMENTO_CAIXA]),
            func.lower(CategoriaDespesa.nome) == 'pagamentos'
        )
    )
    if not current_user.is_gerente():
        saidas_caixa_query = saidas_caixa_query.filter(Despesa.user_id == current_user.id)
    if entidade_filtro:
        saidas_caixa_query = saidas_caixa_query.filter(
            or_(Despesa.entidade == entidade_filtro, Despesa.entidade == None)
        )
    saidas_caixa = saidas_caixa_query.scalar() or 0.0

    eventos_caixa_query = db.session.query(func.sum(EventoCaixaAvulso.valor)).filter(
        extract('month', EventoCaixaAvulso.data) == mes_atual,
        extract('year', EventoCaixaAvulso.data) == ano_atual
    )
    if not current_user.is_gerente():
        eventos_caixa_query = eventos_caixa_query.filter(EventoCaixaAvulso.user_id == current_user.id)
    eventos_caixa = eventos_caixa_query.scalar() or 0.0

    fluxo_saidas = saidas_caixa + eventos_caixa
    fluxo_entradas = total_receitas_mes
    fluxo_saldo = fluxo_entradas - fluxo_saidas

    # Totais separados PF/PJ para promax pf_pj (exibidos quando "Todas")
    totais_pf_pj = None
    if current_user.usa_separacao_pf_pj() and not entidade_filtro:
        def _total_desp(ent):
            q = db.session.query(func.sum(Despesa.valor)).join(CategoriaDespesa).filter(
                extract('month', Despesa.data_pagamento) == mes_atual,
                extract('year', Despesa.data_pagamento) == ano_atual,
                func.lower(CategoriaDespesa.nome) != 'pagamentos',
                Despesa.user_id == current_user.id,
                Despesa.entidade == ent
            )
            return q.scalar() or 0

        def _total_rec(ent):
            q = db.session.query(func.sum(Receita.valor)).filter(
                extract('month', Receita.data_recebimento) == mes_atual,
                extract('year', Receita.data_recebimento) == ano_atual,
                Receita.user_id == current_user.id,
                Receita.entidade == ent
            )
            return q.scalar() or 0

        totais_pf_pj = {
            'desp_pf': _total_desp('pf'), 'desp_pj': _total_desp('pj'),
            'rec_pf': _total_rec('pf'),   'rec_pj': _total_rec('pj'),
        }

    # Últimas transações
    ultimas_despesas = despesas_query.order_by(Despesa.data_registro.desc()).limit(5).all()
    ultimas_receitas = receitas_query.order_by(Receita.data_registro.desc()).limit(5).all()

    nome_mes = calendar.month_name[mes_atual]

    return render_template('dashboard.html',
                         total_despesas=total_despesas_mes,
                         total_receitas=total_receitas_mes,
                         saldo=saldo_mes,
                         fluxo_entradas=fluxo_entradas,
                         fluxo_saidas=fluxo_saidas,
                         fluxo_saldo=fluxo_saldo,
                         ultimas_despesas=ultimas_despesas,
                         ultimas_receitas=ultimas_receitas,
                         mes_atual=nome_mes,
                         ano_atual=ano_atual,
                         entidade_filtro=entidade_filtro,
                         totais_pf_pj=totais_pf_pj)

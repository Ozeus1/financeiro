from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, Despesa, Receita, CategoriaDespesa
from sqlalchemy import func, extract
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
    
    # Todos os usuários (incluindo admin) veem apenas seus próprios dados
    despesas_query = Despesa.query.filter_by(user_id=current_user.id)
    receitas_query = Receita.query.filter_by(user_id=current_user.id)
    
    # Total de despesas do mês (Excluindo 'Pagamentos')
    total_despesas_mes = db.session.query(func.sum(Despesa.valor)).join(CategoriaDespesa).filter(
        extract('month', Despesa.data_pagamento) == mes_atual,
        extract('year', Despesa.data_pagamento) == ano_atual,
        func.lower(CategoriaDespesa.nome) != 'pagamentos',
        Despesa.user_id == current_user.id
    ).scalar() or 0
    
    # Total de receitas do mês
    total_receitas_mes = db.session.query(func.sum(Receita.valor)).filter(
        extract('month', Receita.data_recebimento) == mes_atual,
        extract('year', Receita.data_recebimento) == ano_atual,
        Receita.user_id == current_user.id
    ).scalar() or 0
    
    # Saldo do mês (Geral)
    saldo_mes = total_receitas_mes - total_despesas_mes
    
    # --- CÁLCULO DO FLUXO DE CAIXA ---
    from models import MeioPagamento, EventoCaixaAvulso
    from sqlalchemy import or_
    
    MEIOS_PAGAMENTO_CAIXA = ['Boleto', 'Dinheiro', 'PIX', 'Transferência', 'Débito em Conta']
    
    # Saídas de Caixa (Despesas em dinheiro/pix/etc OU Categoria 'Pagamentos')
    saidas_caixa = db.session.query(func.sum(Despesa.valor)).join(
        Despesa.meio_pagamento
    ).join(
        Despesa.categoria
    ).filter(
        extract('month', Despesa.data_pagamento) == mes_atual,
        extract('year', Despesa.data_pagamento) == ano_atual,
        or_(
            func.lower(MeioPagamento.nome).in_([m.lower() for m in MEIOS_PAGAMENTO_CAIXA]),
            func.lower(CategoriaDespesa.nome) == 'pagamentos'
        ),
        Despesa.user_id == current_user.id
    ).scalar() or 0.0
    
    # Eventos Avulsos (Saídas)
    eventos_caixa = db.session.query(func.sum(EventoCaixaAvulso.valor)).filter(
        extract('month', EventoCaixaAvulso.data) == mes_atual,
        extract('year', EventoCaixaAvulso.data) == ano_atual,
        EventoCaixaAvulso.user_id == current_user.id
    ).scalar() or 0.0
    
    fluxo_saidas = saidas_caixa + eventos_caixa
    fluxo_entradas = total_receitas_mes # Receitas são entradas de caixa
    fluxo_saldo = fluxo_entradas - fluxo_saidas
    
    # Últimas despesas (Por Registro)
    ultimas_despesas_registro = despesas_query.order_by(Despesa.data_registro.desc()).limit(5).all()
    
    # Últimas despesas (Por Data - Mês Atual)
    ultimas_despesas_data = despesas_query.filter(
        extract('month', Despesa.data_pagamento) == mes_atual,
        extract('year', Despesa.data_pagamento) == ano_atual
    ).order_by(Despesa.data_pagamento.desc()).limit(5).all()
    
    # Últimas receitas (Por Registro)
    ultimas_receitas_registro = receitas_query.order_by(Receita.data_registro.desc()).limit(5).all()
    
    # Últimas receitas (Por Data - Mês Atual)
    ultimas_receitas_data = receitas_query.filter(
        extract('month', Receita.data_recebimento) == mes_atual,
        extract('year', Receita.data_recebimento) == ano_atual
    ).order_by(Receita.data_recebimento.desc()).limit(5).all()
    
    # Nome do mês em português
    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    nome_mes = meses_pt[mes_atual]

    return render_template('dashboard.html',
                         total_despesas=total_despesas_mes,
                         total_receitas=total_receitas_mes,
                         saldo=saldo_mes,
                         fluxo_entradas=fluxo_entradas,
                         fluxo_saidas=fluxo_saidas,
                         fluxo_saldo=fluxo_saldo,
                         ultimas_despesas_registro=ultimas_despesas_registro,
                         ultimas_despesas_data=ultimas_despesas_data,
                         ultimas_receitas_registro=ultimas_receitas_registro,
                         ultimas_receitas_data=ultimas_receitas_data,
                         mes_atual=nome_mes,
                         ano_atual=ano_atual)

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import (db, InvestRendaFixa, InvestFundo, InvestCripto, InvestPrevidencia,
                     InvestInternacional, InvestAtivo)
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

investimentos_bp = Blueprint('investimentos', __name__)


def _check_acesso():
    if not (current_user.is_pro() or current_user.is_promax()):
        abort(403)


def get_maturity_class(date_obj):
    if not date_obj:
        return 'Indefinido'
    days = (date_obj - date.today()).days
    if days <= 365:
        return 'Curto Prazo'
    elif days <= 1095:
        return 'Médio Prazo'
    else:
        return 'Longo Prazo'


def process_assets(assets):
    if not assets:
        return []
    total_value_list = sum((a.quantity or 0) * (a.current_price or 0.0) for a in assets)
    final_data = []
    for a in assets:
        current_price = a.current_price if a.current_price else 0.0
        total_invested = (a.quantity or 0) * (a.avg_price or 0)
        current_total = (a.quantity or 0) * current_price
        profit = current_total - total_invested
        profit_pct = (profit / total_invested * 100) if total_invested > 0 else 0
        weight = (current_total / total_value_list * 100) if total_value_list > 0 else 0
        if a.daily_change and current_price > 0:
            prev_close = current_price / (1 + (a.daily_change / 100))
            day_gain = (a.quantity or 0) * (current_price - prev_close)
        else:
            day_gain = 0.0
        final_data.append({
            'asset': a, 'current_price': current_price,
            'change_percent': a.daily_change if a.daily_change is not None else 0.0,
            'total_invested': total_invested, 'current_total': current_total,
            'profit': profit, 'profit_pct': profit_pct, 'day_gain': day_gain, 'weight': weight,
            'last_update': a.last_update.strftime('%d/%m %H:%M') if a.last_update else '-'
        })
    return final_data


@investimentos_bp.route('/')
@login_required
def index():
    _check_acesso()

    try:
        rfs = InvestRendaFixa.query.filter_by(user_id=current_user.id).all()
        rf_pos = [r for r in rfs if r.category == 'POS']
        rf_pre = [r for r in rfs if r.category == 'PRE']
        rf_ipca = [r for r in rfs if r.category == 'IPCA']
        funds = InvestFundo.query.filter_by(user_id=current_user.id).all()
        pensions = InvestPrevidencia.query.filter_by(user_id=current_user.id).all()
        cryptos = InvestCripto.query.filter_by(user_id=current_user.id).all()

        acoes_assets = InvestAtivo.query.filter(InvestAtivo.type == 'ACAO', InvestAtivo.user_id == current_user.id, InvestAtivo.quantity > 0).all()
        fiis_assets = InvestAtivo.query.filter(InvestAtivo.type == 'FII', InvestAtivo.user_id == current_user.id, InvestAtivo.quantity > 0).all()
        etfs_assets = InvestAtivo.query.filter(InvestAtivo.type == 'ETF', InvestAtivo.user_id == current_user.id, InvestAtivo.quantity > 0).all()

        intls_rv = InvestInternacional.query.filter_by(user_id=current_user.id, category='RV').all()
        intls_rf = InvestInternacional.query.filter_by(user_id=current_user.id, category='RF').all()

        val_acoes = sum((a.quantity * ((a.current_price or 0) if (a.current_price or 0) > 0 else (a.avg_price or 0))) for a in acoes_assets)
        val_fiis = sum((a.quantity * ((a.current_price or 0) if (a.current_price or 0) > 0 else (a.avg_price or 0))) for a in fiis_assets)
        val_etfs = sum((a.quantity * ((a.current_price or 0) if (a.current_price or 0) > 0 else (a.avg_price or 0))) for a in etfs_assets)

        summary = {
            'Curto Prazo': 0, 'Médio Prazo': 0, 'Longo Prazo': 0, 'Indefinido': 0,
            'Renda Fixa': 0, 'Renda Variável': 0
        }

        types_total = {
            'Renda Fixa Pós': 0, 'Renda Fixa Pré': 0, 'Renda Fixa IPCA': 0,
            'Fundos': 0, 'Cripto': 0, 'Previdência': 0,
            'Internacional RV': 0, 'Internacional RF': 0,
            'Ações': val_acoes, 'FIIs': val_fiis
        }

        maturity_breakdown = {
            'Renda Fixa Pós': {'Curto Prazo': 0, 'Médio Prazo': 0, 'Longo Prazo': 0, 'Indefinido': 0},
            'Renda Fixa Pré': {'Curto Prazo': 0, 'Médio Prazo': 0, 'Longo Prazo': 0, 'Indefinido': 0},
            'Renda Fixa IPCA': {'Curto Prazo': 0, 'Médio Prazo': 0, 'Longo Prazo': 0, 'Indefinido': 0},
            'Fundos': {'Curto Prazo': 0, 'Médio Prazo': 0, 'Longo Prazo': 0, 'Indefinido': 0}
        }

        # Subtipos de Renda Fixa
        rf_subtypes = {}
        for r in rfs:
            p_type = r.product_type
            if not p_type:
                name_upper = r.name.upper()
                if 'CDB' in name_upper: p_type = 'CDB'
                elif 'LCI' in name_upper: p_type = 'LCI'
                elif 'LCA' in name_upper: p_type = 'LCA'
                elif 'CRI' in name_upper: p_type = 'CRI'
                elif 'CRA' in name_upper: p_type = 'CRA'
                elif 'RDB' in name_upper: p_type = 'RDB'
                elif 'TESOURO' in name_upper: p_type = 'Tesouro Direto'
                elif 'DEBENTURE' in name_upper: p_type = 'Debênture'
                else: p_type = 'Outros'
            p_type = p_type.upper().strip()
            rf_subtypes[p_type] = rf_subtypes.get(p_type, 0) + (r.value or 0)
        rf_subtypes_sorted = dict(sorted(rf_subtypes.items(), key=lambda item: item[1], reverse=True))

        def process_list(items, type_key, is_variable=False):
            total = 0
            for i in items:
                val = i.value or 0
                total += val
                cls = get_maturity_class(i.maturity_date)
                summary[cls] += val
                if type_key in maturity_breakdown:
                    maturity_breakdown[type_key][cls] += val
            types_total[type_key] = total
            if is_variable:
                summary['Renda Variável'] += total
            else:
                summary['Renda Fixa'] += total
            return total

        process_list(rf_pos, 'Renda Fixa Pós')
        process_list(rf_pre, 'Renda Fixa Pré')
        process_list(rf_ipca, 'Renda Fixa IPCA')

        # Fundos
        total_funds = 0
        val_funds_pos = 0
        val_funds_ipca = 0
        for f in funds:
            val = f.value or 0
            total_funds += val
            cls = get_maturity_class(f.maturity_date)
            if f.maturity_date:
                summary[cls] += val
            else:
                summary['Indefinido'] += val

            idx = (f.indexer or '').upper()
            if 'IPCA' in idx:
                chart_cat = 'Renda Fixa IPCA'
                val_funds_ipca += val
            elif 'SELIC' in idx or 'CDI' in idx:
                chart_cat = 'Renda Fixa Pós'
                val_funds_pos += val
            else:
                chart_cat = 'Fundos'
                val_funds_pos += val

            if chart_cat in maturity_breakdown:
                maturity_breakdown[chart_cat][cls] += val

        types_total['Fundos'] = total_funds
        summary['Renda Fixa'] += total_funds

        # Cripto
        t_crypto = sum((c.current_value or 0) for c in cryptos)
        types_total['Cripto'] = t_crypto
        summary['Renda Variável'] += t_crypto
        summary['Indefinido'] += t_crypto

        # Previdência
        val_pension_rf = 0
        val_pension_acao = 0
        for p in pensions:
            types_total['Previdência'] += p.value
            summary['Longo Prazo'] += p.value
            if p.type == 'Acao':
                summary['Renda Variável'] += p.value
                val_pension_acao += p.value
            else:
                summary['Renda Fixa'] += p.value
                val_pension_rf += p.value

        # Internacional RV
        t_intl_rv = sum(((i.value_usd or 0) * (i.rate_usd or 5.5)) for i in intls_rv)
        types_total['Internacional RV'] = t_intl_rv
        summary['Renda Variável'] += t_intl_rv
        summary['Indefinido'] += t_intl_rv

        # Internacional RF
        t_intl_rf = sum(((i.value_usd or 0) * (i.rate_usd or 5.5)) for i in intls_rf)
        types_total['Internacional RF'] = t_intl_rf
        summary['Renda Fixa'] += t_intl_rf
        summary['Longo Prazo'] += t_intl_rf

        # Ações / FIIs / ETF
        summary['Renda Variável'] += (val_acoes + val_fiis + val_etfs)
        summary['Indefinido'] += (val_acoes + val_fiis + val_etfs)
        types_total['ETF'] = val_etfs

        total_portfolio = sum(types_total.values())

        # Limpa breakdown de vencimento (remove zeros)
        clean_breakdown = {}
        for cat, terms in maturity_breakdown.items():
            clean_terms = {k: v for k, v in terms.items() if v > 0.01}
            if clean_terms:
                clean_breakdown[cat] = clean_terms

        # RF por prazo (agregado)
        rf_chart_term = {'Curto Prazo': 0, 'Médio Prazo': 0, 'Longo Prazo': 0, 'Indefinido': 0}
        for cat, terms in clean_breakdown.items():
            for term, val in terms.items():
                if term in rf_chart_term:
                    rf_chart_term[term] += val

        # RF por tipo (agregado)
        rf_chart_type = {cat: sum(terms.values()) for cat, terms in clean_breakdown.items()}
        total_rf_detailed = sum(rf_chart_type.values())

        # Pizza por classe
        target_keys = [
            'Renda Fixa Pós', 'Renda Fixa Pré', 'Renda Fixa IPCA',
            'Fundos', 'Cripto', 'Previdência',
            'Ações', 'FIIs',
            'Internacional RV', 'Internacional RF', 'ETF'
        ]
        pie_chart_data = {k: types_total.get(k, 0) for k in target_keys if types_total.get(k, 0) > 0.01}

        # Totais Internacional RV
        intl_rv_invested = sum(((i.quantity or 0) * (i.avg_price or 0)) for i in intls_rv)
        intl_rv_current = sum(((i.quantity or 0) * (i.quote or 0)) for i in intls_rv)
        intl_rv_profit = intl_rv_current - intl_rv_invested

        # Totais Cripto
        crypto_invested = sum((c.quantity or 0) * (c.avg_price or 0) for c in cryptos)
        crypto_current = sum((c.current_value or 0) for c in cryptos)
        crypto_profit = crypto_current - crypto_invested

        # Localização (Brasil x Internacional)
        total_intl = t_intl_rv + t_intl_rf + t_crypto + val_etfs
        total_br = total_portfolio - total_intl
        location_chart = {'Brasil': total_br, 'Internacional': total_intl}

        # Hierarquia de resumo
        val_rf_pos_strict = types_total.get('Renda Fixa Pós', 0)
        total_pos = val_rf_pos_strict + val_funds_pos + val_pension_rf
        total_pre = types_total.get('Renda Fixa Pré', 0)
        total_ipca = types_total.get('Renda Fixa IPCA', 0) + val_funds_ipca
        total_rf_general = total_pos + total_pre + total_ipca

        total_acoes_consol = val_acoes + val_pension_acao
        total_fii = val_fiis
        total_rv_br = total_acoes_consol + total_fii

        total_cripto = types_total.get('Cripto', 0)
        total_intl_rv = types_total.get('Internacional RV', 0)
        total_intl_rf = types_total.get('Internacional RF', 0)
        total_etf_intl = val_etfs
        total_rv_intl_general = total_cripto + total_intl_rv + total_intl_rf + total_etf_intl

        def calc_pct(v):
            return (v / total_portfolio * 100) if total_portfolio > 0 else 0

        summary_hierarchy = [
            {
                'group': 'Renda Fixa',
                'lines': [
                    {'label': 'Pós', 'value': total_pos, 'pct': calc_pct(total_pos)},
                    {'label': 'Pré', 'value': total_pre, 'pct': calc_pct(total_pre)},
                    {'label': 'Ipca', 'value': total_ipca, 'pct': calc_pct(total_ipca)},
                ],
                'total': total_rf_general,
                'total_pct': calc_pct(total_rf_general)
            },
            {
                'group': 'RV Brasil',
                'lines': [
                    {'label': 'Ações', 'value': total_acoes_consol, 'pct': calc_pct(total_acoes_consol)},
                    {'label': 'FII', 'value': total_fii, 'pct': calc_pct(total_fii)},
                ],
                'total': total_rv_br,
                'total_pct': calc_pct(total_rv_br)
            },
            {
                'group': 'RV Internacional',
                'lines': [
                    {'label': 'Criptomoedas', 'value': total_cripto, 'pct': calc_pct(total_cripto)},
                    {'label': 'ETF', 'value': total_etf_intl, 'pct': calc_pct(total_etf_intl)},
                    {'label': 'Renda Variável Internacional', 'value': total_intl_rv, 'pct': calc_pct(total_intl_rv)},
                    {'label': 'Renda Fixa Internacional', 'value': total_intl_rf, 'pct': calc_pct(total_intl_rf)},
                ],
                'total': total_rv_intl_general,
                'total_pct': calc_pct(total_rv_intl_general)
            }
        ]

        summary_exploded = {}
        for group in summary_hierarchy:
            for line in group['lines']:
                if line['value'] > 0:
                    label = line['label']
                    if label == 'Renda Variável Internacional': label = 'RV Internacional'
                    if label == 'Renda Fixa Internacional': label = 'RF Internacional'
                    summary_exploded[label] = line['value']

        summary_general = {
            'Pós': total_pos,
            'Pré': total_pre,
            'Ipca': total_ipca,
            'RV Brasil': total_rv_br,
            'RV Internacional': total_rv_intl_general
        }

        processed_acoes = process_assets(acoes_assets)
        processed_etfs = process_assets(etfs_assets)
        total_acoes_invested = sum(a['total_invested'] for a in processed_acoes)
        total_acoes_current = sum(a['current_total'] for a in processed_acoes)
        total_etfs_invested = sum(a['total_invested'] for a in processed_etfs)
        total_etfs_current = sum(a['current_total'] for a in processed_etfs)

        return render_template('investimentos/index.html',
                               rf_pos=rf_pos, rf_pre=rf_pre, rf_ipca=rf_ipca,
                               funds=funds, cryptos=cryptos, pensions=pensions,
                               intls_rv=intls_rv, intls_rf=intls_rf,
                               summary=summary, types_total=types_total, total_portfolio=total_portfolio,
                               maturity_breakdown=clean_breakdown,
                               rf_chart_term=rf_chart_term, rf_chart_type=rf_chart_type,
                               pie_chart_data=pie_chart_data,
                               total_rf_detailed=total_rf_detailed,
                               intl_rv_invested=intl_rv_invested,
                               intl_rv_current=intl_rv_current,
                               intl_rv_profit=intl_rv_profit,
                               crypto_invested=crypto_invested,
                               crypto_current=crypto_current,
                               crypto_profit=crypto_profit,
                               location_chart=location_chart,
                               summary_hierarchy=summary_hierarchy,
                               summary_exploded=summary_exploded,
                               summary_general=summary_general,
                               rf_subtypes=rf_subtypes_sorted,
                               acoes=processed_acoes, total_acoes_invested=total_acoes_invested, total_acoes_current=total_acoes_current,
                               etfs=processed_etfs, total_etfs_invested=total_etfs_invested, total_etfs_current=total_etfs_current)
    except Exception:
        import traceback
        return f"<h3>Erro ao carregar Investimentos:</h3><pre>{traceback.format_exc()}</pre>"


# ---------------------------------------------------------------------------
# Atualização de cotações via Yahoo Finance
# ---------------------------------------------------------------------------

def _yf_fast_info(yf_ticker):
    import yfinance as yf
    try:
        fi = yf.Ticker(yf_ticker).fast_info
        price = fi.last_price
        prev = fi.previous_close
        if price and price > 0:
            change = ((price - prev) / prev * 100) if prev and prev > 0 else 0.0
            return float(price), float(change)
    except Exception as e:
        print(f"yf fast_info falhou para {yf_ticker}: {e}")
    return None


@investimentos_bp.route('/update_quotes', methods=['POST'])
@login_required
def update_quotes():
    _check_acesso()

    updated = 0
    total = 0

    # 1. Ações / FIIs / ETFs (B3)
    ativos = InvestAtivo.query.filter_by(user_id=current_user.id).all()
    if ativos:
        def _fetch_b3(ativo):
            yf_t = f"{ativo.ticker.upper()}.SA"
            return ativo, _yf_fast_info(yf_t)

        total += len(ativos)
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(_fetch_b3, a) for a in ativos]
            for fut in as_completed(futures):
                ativo, result = fut.result()
                if result:
                    price, change = result
                    ativo.current_price = price
                    ativo.daily_change = change
                    ativo.last_update = datetime.now()
                    updated += 1

    # 2. Internacional (RV/RF) + Cripto + cotação USD/BRL
    intls = InvestInternacional.query.filter_by(user_id=current_user.id).all()
    cryptos = InvestCripto.query.filter_by(user_id=current_user.id).all()

    tasks = {'__USD__': 'USDBRL=X'}
    for item in intls:
        if item.name and item.name.upper() != 'RENDA FIXA':
            t = item.name.strip().upper()
            if t == 'BRKB':
                t = 'BRK-B'
            tasks[f'intl_{item.id}'] = t
    for c in cryptos:
        if c.name:
            tasks[f'crypto_{c.id}'] = f"{c.name.strip().upper()}-USD"

    prices = {}
    if tasks:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = {ex.submit(_yf_fast_info, yf_t): key for key, yf_t in tasks.items()}
            for fut in as_completed(futures):
                key = futures[fut]
                prices[key] = fut.result()

    usd_result = prices.get('__USD__')
    usd_rate = usd_result[0] if usd_result else 0.0

    if usd_rate > 0:
        for item in intls:
            item.rate_usd = usd_rate
            result = prices.get(f'intl_{item.id}')
            if result:
                price, change = result
                if price > 0:
                    item.quote = price
                    item.daily_change = change
                    item.current_price = price
                    if item.quantity:
                        item.value_usd = item.quantity * price
                    total += 1
                    updated += 1

        for c in cryptos:
            result = prices.get(f'crypto_{c.id}')
            if result:
                price_usd, _ = result
                if price_usd > 0:
                    price_brl = price_usd * usd_rate
                    c.quote = price_brl
                    if c.quantity:
                        c.current_value = c.quantity * price_brl
                    total += 1
                    updated += 1

    db.session.commit()

    if total == 0:
        flash('Nenhum ativo cadastrado para atualizar.', 'warning')
    else:
        flash(f'Cotações atualizadas: {updated}/{total} ativo(s).', 'success')

    return redirect(url_for('investimentos.index'))


# ---------------------------------------------------------------------------
# CRUD simplificado
# ---------------------------------------------------------------------------

def _parse_float(value, default=0.0):
    if value is None:
        return default
    value = str(value).strip().replace('.', '').replace(',', '.') if ',' in str(value) else str(value).strip()
    try:
        return float(value)
    except ValueError:
        return default


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


@investimentos_bp.route('/add/rf', methods=['POST'])
@login_required
def add_rf():
    _check_acesso()
    item = InvestRendaFixa(
        user_id=current_user.id,
        category=request.form.get('category'),
        product_type=request.form.get('product_type'),
        institution=request.form.get('institution'),
        name=request.form.get('name'),
        value=_parse_float(request.form.get('value')),
        rate=request.form.get('rate'),
        maturity_date=_parse_date(request.form.get('maturity_date'))
    )
    db.session.add(item)
    db.session.commit()
    flash('Renda Fixa adicionada!', 'success')
    return redirect(url_for('investimentos.index'))


@investimentos_bp.route('/add/fund', methods=['POST'])
@login_required
def add_fund():
    _check_acesso()
    item = InvestFundo(
        user_id=current_user.id,
        institution=request.form.get('institution'),
        name=request.form.get('name'),
        value=_parse_float(request.form.get('value')),
        indexer=request.form.get('indexer'),
        maturity_date=_parse_date(request.form.get('maturity_date'))
    )
    db.session.add(item)
    db.session.commit()
    flash('Fundo adicionado!', 'success')
    return redirect(url_for('investimentos.index'))


@investimentos_bp.route('/add/crypto', methods=['POST'])
@login_required
def add_crypto():
    _check_acesso()
    qty = _parse_float(request.form.get('quantity'))
    avg_price = _parse_float(request.form.get('avg_price'))
    current_value = _parse_float(request.form.get('current_value'))
    item = InvestCripto(
        user_id=current_user.id,
        institution=request.form.get('institution'),
        name=request.form.get('name'),
        quantity=qty,
        avg_price=avg_price,
        invested_value=qty * avg_price,
        current_value=current_value
    )
    db.session.add(item)
    db.session.commit()
    flash('Cripto adicionada!', 'success')
    return redirect(url_for('investimentos.index'))


@investimentos_bp.route('/add/pension', methods=['POST'])
@login_required
def add_pension():
    _check_acesso()
    item = InvestPrevidencia(
        user_id=current_user.id,
        institution=request.form.get('institution'),
        name=request.form.get('name'),
        value=_parse_float(request.form.get('value')),
        type=request.form.get('type'),
        certificate=request.form.get('certificate')
    )
    db.session.add(item)
    db.session.commit()
    flash('Previdência adicionada!', 'success')
    return redirect(url_for('investimentos.index'))


@investimentos_bp.route('/add/intl', methods=['POST'])
@login_required
def add_intl():
    _check_acesso()
    qty = _parse_float(request.form.get('quantity'))
    avg_price = _parse_float(request.form.get('avg_price'))
    invested = qty * avg_price
    item = InvestInternacional(
        user_id=current_user.id,
        institution=request.form.get('institution'),
        name=(request.form.get('name') or '').upper(),
        quantity=qty,
        avg_price=avg_price,
        category=request.form.get('category', 'RV'),
        description=request.form.get('description'),
        value_usd=invested,
        invested_value=invested,
        quote=avg_price
    )
    db.session.add(item)
    db.session.commit()
    flash('Investimento Internacional adicionado!', 'success')
    return redirect(url_for('investimentos.index'))


@investimentos_bp.route('/add/ativo', methods=['POST'])
@login_required
def add_ativo():
    _check_acesso()
    item = InvestAtivo(
        user_id=current_user.id,
        ticker=(request.form.get('ticker') or '').upper(),
        type=request.form.get('type', 'ACAO'),
        quantity=int(_parse_float(request.form.get('quantity'))),
        avg_price=_parse_float(request.form.get('avg_price')),
        entry_date=_parse_date(request.form.get('entry_date'))
    )
    db.session.add(item)
    db.session.commit()
    flash('Ativo adicionado!', 'success')
    return redirect(url_for('investimentos.index'))


_MODEL_MAP = {
    'rf': InvestRendaFixa,
    'fund': InvestFundo,
    'crypto': InvestCripto,
    'pension': InvestPrevidencia,
    'intl': InvestInternacional,
    'ativo': InvestAtivo,
}


@investimentos_bp.route('/edit/<tipo>/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(tipo, id):
    _check_acesso()
    model = _MODEL_MAP.get(tipo)
    if not model:
        abort(404)
    item = model.query.filter_by(id=id, user_id=current_user.id).first()
    if not item:
        flash('Item não encontrado ou acesso negado.', 'warning')
        return redirect(url_for('investimentos.index'))

    if request.method == 'POST':
        if tipo == 'rf':
            item.institution = request.form.get('institution')
            item.name = request.form.get('name')
            item.value = _parse_float(request.form.get('value'))
            item.rate = request.form.get('rate')
            item.maturity_date = _parse_date(request.form.get('maturity_date'))
            if request.form.get('product_type'):
                item.product_type = request.form.get('product_type')

        elif tipo == 'fund':
            item.institution = request.form.get('institution')
            item.name = request.form.get('name')
            item.value = _parse_float(request.form.get('value'))
            item.indexer = request.form.get('indexer')
            item.maturity_date = _parse_date(request.form.get('maturity_date'))

        elif tipo == 'crypto':
            item.institution = request.form.get('institution')
            item.name = request.form.get('name')
            item.quantity = _parse_float(request.form.get('quantity'))
            item.avg_price = _parse_float(request.form.get('avg_price'))
            item.invested_value = item.quantity * item.avg_price
            item.current_value = _parse_float(request.form.get('current_value'))

        elif tipo == 'pension':
            item.institution = request.form.get('institution')
            item.name = request.form.get('name')
            item.value = _parse_float(request.form.get('value'))
            item.type = request.form.get('type')
            item.certificate = request.form.get('certificate')

        elif tipo == 'intl':
            item.institution = request.form.get('institution')
            item.name = (request.form.get('name') or '').upper()
            item.description = request.form.get('description')
            item.quantity = _parse_float(request.form.get('quantity'))
            item.avg_price = _parse_float(request.form.get('avg_price'))
            quote = _parse_float(request.form.get('quote'))
            if quote:
                item.quote = quote
                item.value_usd = (item.quantity or 0) * quote

        elif tipo == 'ativo':
            item.ticker = (request.form.get('ticker') or '').upper()
            item.type = request.form.get('type')
            item.quantity = int(_parse_float(request.form.get('quantity')))
            item.avg_price = _parse_float(request.form.get('avg_price'))
            item.entry_date = _parse_date(request.form.get('entry_date'))

        db.session.commit()
        flash('Item atualizado com sucesso!', 'success')
        return redirect(url_for('investimentos.index'))

    return render_template('investimentos/edit_item.html', item=item, tipo=tipo)


@investimentos_bp.route('/delete/<tipo>/<int:id>')
@login_required
def delete_item(tipo, id):
    _check_acesso()
    model = _MODEL_MAP.get(tipo)
    if not model:
        abort(404)
    item = model.query.filter_by(id=id, user_id=current_user.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Item removido!', 'success')
    else:
        flash('Item não encontrado ou acesso negado.', 'warning')
    return redirect(url_for('investimentos.index'))

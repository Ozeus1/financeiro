"""
REST API v1 — FiNan
Autenticação: header  X-API-Key: <sua_chave>
Todos os endpoints exigem a chave e retornam apenas dados do usuário dono da chave.
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import date, datetime
from sqlalchemy import extract

import calendar
from datetime import date as _date, timedelta

from models import (
    db, ApiKey,
    Despesa, Receita,
    CategoriaDespesa, CategoriaReceita,
    MeioPagamento, MeioRecebimento,
    Orcamento,
)

api_bp = Blueprint('api_v1', __name__)

# ── Auth decorator ─────────────────────────────────────────────────────────────

def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        raw = (
            request.headers.get('X-API-Key')
            or request.args.get('api_key')
        )
        if not raw:
            return jsonify({'erro': 'API key não fornecida', 'codigo': 'MISSING_KEY'}), 401

        usuario, _ = ApiKey.verificar(raw)
        if not usuario:
            return jsonify({'erro': 'API key inválida ou inativa', 'codigo': 'INVALID_KEY'}), 401
        if not usuario.ativo:
            return jsonify({'erro': 'Usuário inativo', 'codigo': 'USER_INACTIVE'}), 403

        return f(usuario, *args, **kwargs)
    return decorated


def _parse_date(s):
    """Converte string YYYY-MM-DD para date. Aceita datetime ISO e remove hora se vier junto."""
    from datetime import datetime as _dt
    s = str(s).strip()[:10]
    return _dt.strptime(s, '%Y-%m-%d').date()


def _despesa_dict(d):
    return {
        'id': d.id,
        'descricao': d.descricao,
        'valor': round(d.valor, 2),
        'num_parcelas': d.num_parcelas,
        'data_pagamento': d.data_pagamento.isoformat(),
        'data_registro': d.data_registro.isoformat() if d.data_registro else None,
        'categoria_codigo': d.categoria_id,
        'categoria_nome': d.categoria.nome if d.categoria else None,
        'meio_pagamento_codigo': d.meio_pagamento_id,
        'meio_pagamento_nome': d.meio_pagamento.nome if d.meio_pagamento else None,
    }


def _receita_dict(r):
    return {
        'id': r.id,
        'descricao': r.descricao,
        'valor': round(r.valor, 2),
        'num_parcelas': r.num_parcelas,
        'data_recebimento': r.data_recebimento.isoformat(),
        'data_registro': r.data_registro.isoformat() if r.data_registro else None,
        'categoria_codigo': r.categoria_id,
        'categoria_nome': r.categoria.nome if r.categoria else None,
        'meio_recebimento_codigo': r.meio_recebimento_id,
        'meio_recebimento_nome': r.meio_recebimento.nome if r.meio_recebimento else None,
    }


# ── Referências (catálogos) ────────────────────────────────────────────────────

@api_bp.route('/categorias/despesas', methods=['GET'])
@api_key_required
def listar_cat_despesas(usuario):
    """Lista categorias de despesa com seus códigos."""
    so_ativas = request.args.get('ativo', 'false').lower() == 'true'
    q = CategoriaDespesa.query.filter_by(user_id=usuario.id)
    if so_ativas:
        q = q.filter_by(ativo=True)
    cats = q.order_by(CategoriaDespesa.nome).all()
    return jsonify([{'codigo': c.id, 'nome': c.nome, 'ativo': c.ativo} for c in cats])


@api_bp.route('/categorias/receitas', methods=['GET'])
@api_key_required
def listar_cat_receitas(usuario):
    """Lista categorias de receita com seus códigos."""
    so_ativas = request.args.get('ativo', 'false').lower() == 'true'
    q = CategoriaReceita.query.filter_by(user_id=usuario.id)
    if so_ativas:
        q = q.filter_by(ativo=True)
    cats = q.order_by(CategoriaReceita.nome).all()
    return jsonify([{'codigo': c.id, 'nome': c.nome, 'ativo': c.ativo} for c in cats])


@api_bp.route('/meios-pagamento', methods=['GET'])
@api_key_required
def listar_meios_pag(usuario):
    """Lista meios de pagamento com seus códigos."""
    so_ativos = request.args.get('ativo', 'false').lower() == 'true'
    q = MeioPagamento.query.filter_by(user_id=usuario.id)
    if so_ativos:
        q = q.filter_by(ativo=True)
    meios = q.order_by(MeioPagamento.nome).all()
    return jsonify([{'codigo': m.id, 'nome': m.nome, 'tipo': m.tipo, 'ativo': m.ativo} for m in meios])


@api_bp.route('/meios-recebimento', methods=['GET'])
@api_key_required
def listar_meios_rec(usuario):
    """Lista meios de recebimento com seus códigos."""
    so_ativos = request.args.get('ativo', 'false').lower() == 'true'
    q = MeioRecebimento.query.filter_by(user_id=usuario.id)
    if so_ativos:
        q = q.filter_by(ativo=True)
    meios = q.order_by(MeioRecebimento.nome).all()
    return jsonify([{'codigo': m.id, 'nome': m.nome, 'ativo': m.ativo} for m in meios])


# ── Despesas ───────────────────────────────────────────────────────────────────

@api_bp.route('/despesas', methods=['GET'])
@api_key_required
def listar_despesas(usuario):
    """
    Lista despesas com filtros opcionais.
    Query params:
      mes, ano                       — filtra por mês/ano
      data_inicio, data_fim          — filtra por intervalo YYYY-MM-DD (substitui mes/ano)
      categoria_codigo               — filtra por categoria
      meio_pagamento_codigo          — filtra por meio de pagamento
      pagina, por_pagina             — paginação (máx 200)
    Retorna também total_registros e total_valor (soma dos valores filtrados).
    """
    q = Despesa.query.filter_by(user_id=usuario.id)

    # Filtro por intervalo de datas (tem precedência sobre mes/ano)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    if data_inicio or data_fim:
        if data_inicio:
            try:
                q = q.filter(Despesa.data_pagamento >= _parse_date(data_inicio))
            except (ValueError, TypeError):
                return jsonify({'erro': 'data_inicio inválida. Use YYYY-MM-DD'}), 422
        if data_fim:
            try:
                q = q.filter(Despesa.data_pagamento <= _parse_date(data_fim))
            except (ValueError, TypeError):
                return jsonify({'erro': 'data_fim inválida. Use YYYY-MM-DD'}), 422
    else:
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        if ano:
            q = q.filter(extract('year', Despesa.data_pagamento) == ano)
        if mes:
            q = q.filter(extract('month', Despesa.data_pagamento) == mes)

    cat_cod = request.args.get('categoria_codigo', type=int)
    meio_cod = request.args.get('meio_pagamento_codigo', type=int)
    if cat_cod:
        q = q.filter_by(categoria_id=cat_cod)
    if meio_cod:
        q = q.filter_by(meio_pagamento_id=meio_cod)

    total_registros = q.count()
    total_valor = round(db.session.query(db.func.sum(Despesa.valor))
                        .filter(Despesa.id.in_([d.id for d in q.with_entities(Despesa.id)])).scalar() or 0, 2)

    pagina = max(1, request.args.get('pagina', 1, type=int))
    por_pagina = min(request.args.get('por_pagina', 50, type=int), 200)
    despesas = (q.order_by(Despesa.data_pagamento.desc())
                 .offset((pagina - 1) * por_pagina)
                 .limit(por_pagina).all())

    return jsonify({
        'total_registros': total_registros,
        'total_valor': total_valor,
        'pagina': pagina,
        'por_pagina': por_pagina,
        'paginas': max(1, (total_registros + por_pagina - 1) // por_pagina),
        'dados': [_despesa_dict(d) for d in despesas],
    })


@api_bp.route('/despesas/<int:despesa_id>', methods=['GET'])
@api_key_required
def obter_despesa(usuario, despesa_id):
    d = Despesa.query.filter_by(id=despesa_id, user_id=usuario.id).first()
    if not d:
        return jsonify({'erro': 'Despesa não encontrada'}), 404
    return jsonify(_despesa_dict(d))


@api_bp.route('/despesas', methods=['POST'])
@api_key_required
def criar_despesa(usuario):
    """
    Corpo JSON obrigatório:
      descricao, valor, data_pagamento (YYYY-MM-DD),
      categoria_codigo, meio_pagamento_codigo
    Opcional: num_parcelas (padrão 1)
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'erro': 'JSON inválido ou ausente'}), 400

    erros = []
    for campo in ('descricao', 'valor', 'data_pagamento', 'categoria_codigo', 'meio_pagamento_codigo'):
        if not data.get(campo) and data.get(campo) != 0:
            erros.append(f'Campo "{campo}" é obrigatório')
    if erros:
        return jsonify({'erro': 'Dados inválidos', 'detalhes': erros}), 422

    try:
        cat_id = int(data['categoria_codigo'])
        meio_id = int(data['meio_pagamento_codigo'])
    except (ValueError, TypeError):
        return jsonify({'erro': 'categoria_codigo e meio_pagamento_codigo devem ser números inteiros'}), 422

    categoria = CategoriaDespesa.query.filter_by(id=cat_id, user_id=usuario.id).first()
    if not categoria:
        return jsonify({'erro': 'categoria_codigo inválido ou não pertence ao usuário'}), 422

    meio = MeioPagamento.query.filter_by(id=meio_id, user_id=usuario.id).first()
    if not meio:
        return jsonify({'erro': 'meio_pagamento_codigo inválido ou não pertence ao usuário'}), 422

    try:
        dt_pag = _parse_date(data['data_pagamento'])
    except (ValueError, TypeError):
        return jsonify({'erro': 'data_pagamento inválida. Use YYYY-MM-DD'}), 422

    try:
        valor = float(str(data['valor']).replace(',', '.'))
        if valor <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'erro': 'valor deve ser um número positivo'}), 422

    despesa = Despesa(
        descricao=str(data['descricao']).strip(),
        valor=valor,
        num_parcelas=max(1, int(data.get('num_parcelas', 1))),
        data_pagamento=dt_pag,
        user_id=usuario.id,
        categoria_id=categoria.id,
        meio_pagamento_id=meio.id,
    )
    db.session.add(despesa)
    db.session.commit()
    return jsonify({'mensagem': 'Despesa criada com sucesso', **_despesa_dict(despesa)}), 201


@api_bp.route('/despesas/<int:despesa_id>', methods=['PUT'])
@api_key_required
def atualizar_despesa(usuario, despesa_id):
    """Atualiza campos fornecidos da despesa (PATCH semântico)."""
    d = Despesa.query.filter_by(id=despesa_id, user_id=usuario.id).first()
    if not d:
        return jsonify({'erro': 'Despesa não encontrada'}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'erro': 'JSON inválido ou ausente'}), 400

    if 'descricao' in data:
        d.descricao = str(data['descricao']).strip()
    if 'valor' in data:
        try:
            v = float(data['valor'])
            if v <= 0:
                raise ValueError
            d.valor = v
        except (ValueError, TypeError):
            return jsonify({'erro': 'valor deve ser um número positivo'}), 422
    if 'num_parcelas' in data:
        d.num_parcelas = max(1, int(data['num_parcelas']))
    if 'data_pagamento' in data:
        try:
            d.data_pagamento = _parse_date(data['data_pagamento'])
        except (ValueError, TypeError):
            return jsonify({'erro': 'data_pagamento inválida. Use YYYY-MM-DD'}), 422
    if 'categoria_codigo' in data:
        cat = CategoriaDespesa.query.filter_by(id=data['categoria_codigo'], user_id=usuario.id).first()
        if not cat:
            return jsonify({'erro': 'categoria_codigo inválido'}), 422
        d.categoria_id = cat.id
    if 'meio_pagamento_codigo' in data:
        meio = MeioPagamento.query.filter_by(id=data['meio_pagamento_codigo'], user_id=usuario.id).first()
        if not meio:
            return jsonify({'erro': 'meio_pagamento_codigo inválido'}), 422
        d.meio_pagamento_id = meio.id

    db.session.commit()
    return jsonify({'mensagem': 'Despesa atualizada', **_despesa_dict(d)})


@api_bp.route('/despesas/<int:despesa_id>', methods=['DELETE'])
@api_key_required
def excluir_despesa(usuario, despesa_id):
    d = Despesa.query.filter_by(id=despesa_id, user_id=usuario.id).first()
    if not d:
        return jsonify({'erro': 'Despesa não encontrada'}), 404
    db.session.delete(d)
    db.session.commit()
    return jsonify({'mensagem': 'Despesa excluída com sucesso', 'id': despesa_id})


# ── Receitas ───────────────────────────────────────────────────────────────────

@api_bp.route('/receitas', methods=['GET'])
@api_key_required
def listar_receitas(usuario):
    """
    Lista receitas com filtros opcionais.
    Query params:
      mes, ano                       — filtra por mês/ano
      data_inicio, data_fim          — filtra por intervalo YYYY-MM-DD
      categoria_codigo               — filtra por categoria
      meio_recebimento_codigo        — filtra por meio de recebimento
      pagina, por_pagina             — paginação (máx 200)
    Retorna também total_registros e total_valor.
    """
    q = Receita.query.filter_by(user_id=usuario.id)

    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    if data_inicio or data_fim:
        if data_inicio:
            try:
                q = q.filter(Receita.data_recebimento >= _parse_date(data_inicio))
            except (ValueError, TypeError):
                return jsonify({'erro': 'data_inicio inválida. Use YYYY-MM-DD'}), 422
        if data_fim:
            try:
                q = q.filter(Receita.data_recebimento <= _parse_date(data_fim))
            except (ValueError, TypeError):
                return jsonify({'erro': 'data_fim inválida. Use YYYY-MM-DD'}), 422
    else:
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        if ano:
            q = q.filter(extract('year', Receita.data_recebimento) == ano)
        if mes:
            q = q.filter(extract('month', Receita.data_recebimento) == mes)

    cat_cod = request.args.get('categoria_codigo', type=int)
    meio_cod = request.args.get('meio_recebimento_codigo', type=int)
    if cat_cod:
        q = q.filter_by(categoria_id=cat_cod)
    if meio_cod:
        q = q.filter_by(meio_recebimento_id=meio_cod)

    total_registros = q.count()
    total_valor = round(db.session.query(db.func.sum(Receita.valor))
                        .filter(Receita.id.in_([r.id for r in q.with_entities(Receita.id)])).scalar() or 0, 2)

    pagina = max(1, request.args.get('pagina', 1, type=int))
    por_pagina = min(request.args.get('por_pagina', 50, type=int), 200)
    receitas = (q.order_by(Receita.data_recebimento.desc())
                  .offset((pagina - 1) * por_pagina)
                  .limit(por_pagina).all())

    return jsonify({
        'total_registros': total_registros,
        'total_valor': total_valor,
        'pagina': pagina,
        'por_pagina': por_pagina,
        'paginas': max(1, (total_registros + por_pagina - 1) // por_pagina),
        'dados': [_receita_dict(r) for r in receitas],
    })


@api_bp.route('/receitas/<int:receita_id>', methods=['GET'])
@api_key_required
def obter_receita(usuario, receita_id):
    r = Receita.query.filter_by(id=receita_id, user_id=usuario.id).first()
    if not r:
        return jsonify({'erro': 'Receita não encontrada'}), 404
    return jsonify(_receita_dict(r))


@api_bp.route('/receitas', methods=['POST'])
@api_key_required
def criar_receita(usuario):
    """
    Corpo JSON obrigatório:
      descricao, valor, data_recebimento (YYYY-MM-DD),
      categoria_codigo, meio_recebimento_codigo
    Opcional: num_parcelas (padrão 1)
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'erro': 'JSON inválido ou ausente'}), 400

    erros = []
    for campo in ('descricao', 'valor', 'data_recebimento', 'categoria_codigo', 'meio_recebimento_codigo'):
        if not data.get(campo) and data.get(campo) != 0:
            erros.append(f'Campo "{campo}" é obrigatório')
    if erros:
        return jsonify({'erro': 'Dados inválidos', 'detalhes': erros}), 422

    try:
        cat_id = int(data['categoria_codigo'])
        meio_id = int(data['meio_recebimento_codigo'])
    except (ValueError, TypeError):
        return jsonify({'erro': 'categoria_codigo e meio_recebimento_codigo devem ser números inteiros'}), 422

    categoria = CategoriaReceita.query.filter_by(id=cat_id, user_id=usuario.id).first()
    if not categoria:
        return jsonify({'erro': 'categoria_codigo inválido ou não pertence ao usuário'}), 422

    meio = MeioRecebimento.query.filter_by(id=meio_id, user_id=usuario.id).first()
    if not meio:
        return jsonify({'erro': 'meio_recebimento_codigo inválido ou não pertence ao usuário'}), 422

    try:
        dt_rec = _parse_date(data['data_recebimento'])
    except (ValueError, TypeError):
        return jsonify({'erro': 'data_recebimento inválida. Use YYYY-MM-DD'}), 422

    try:
        valor = float(str(data['valor']).replace(',', '.'))
        if valor <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'erro': 'valor deve ser um número positivo'}), 422

    receita = Receita(
        descricao=str(data['descricao']).strip(),
        valor=valor,
        num_parcelas=max(1, int(data.get('num_parcelas', 1))),
        data_recebimento=dt_rec,
        user_id=usuario.id,
        categoria_id=categoria.id,
        meio_recebimento_id=meio.id,
    )
    db.session.add(receita)
    db.session.commit()
    return jsonify({'mensagem': 'Receita criada com sucesso', **_receita_dict(receita)}), 201


@api_bp.route('/receitas/<int:receita_id>', methods=['PUT'])
@api_key_required
def atualizar_receita(usuario, receita_id):
    """Atualiza campos fornecidos da receita (PATCH semântico)."""
    r = Receita.query.filter_by(id=receita_id, user_id=usuario.id).first()
    if not r:
        return jsonify({'erro': 'Receita não encontrada'}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'erro': 'JSON inválido ou ausente'}), 400

    if 'descricao' in data:
        r.descricao = str(data['descricao']).strip()
    if 'valor' in data:
        try:
            v = float(data['valor'])
            if v <= 0:
                raise ValueError
            r.valor = v
        except (ValueError, TypeError):
            return jsonify({'erro': 'valor deve ser um número positivo'}), 422
    if 'num_parcelas' in data:
        r.num_parcelas = max(1, int(data['num_parcelas']))
    if 'data_recebimento' in data:
        try:
            r.data_recebimento = _parse_date(data['data_recebimento'])
        except (ValueError, TypeError):
            return jsonify({'erro': 'data_recebimento inválida. Use YYYY-MM-DD'}), 422
    if 'categoria_codigo' in data:
        cat = CategoriaReceita.query.filter_by(id=data['categoria_codigo'], user_id=usuario.id).first()
        if not cat:
            return jsonify({'erro': 'categoria_codigo inválido'}), 422
        r.categoria_id = cat.id
    if 'meio_recebimento_codigo' in data:
        meio = MeioRecebimento.query.filter_by(id=data['meio_recebimento_codigo'], user_id=usuario.id).first()
        if not meio:
            return jsonify({'erro': 'meio_recebimento_codigo inválido'}), 422
        r.meio_recebimento_id = meio.id

    db.session.commit()
    return jsonify({'mensagem': 'Receita atualizada', **_receita_dict(r)})


@api_bp.route('/receitas/<int:receita_id>', methods=['DELETE'])
@api_key_required
def excluir_receita(usuario, receita_id):
    r = Receita.query.filter_by(id=receita_id, user_id=usuario.id).first()
    if not r:
        return jsonify({'erro': 'Receita não encontrada'}), 404
    db.session.delete(r)
    db.session.commit()
    return jsonify({'mensagem': 'Receita excluída com sucesso', 'id': receita_id})


# ── Helpers de período ─────────────────────────────────────────────────────────

def _periodo_from_args():
    """Resolve (dt_ini, dt_fim) a partir dos query params da request atual."""
    hoje = _date.today()
    ini_str = request.args.get('data_inicio')
    fim_str = request.args.get('data_fim')
    mes = request.args.get('mes', type=int) or hoje.month
    ano = request.args.get('ano', type=int) or hoje.year

    if ini_str or fim_str:
        dt_ini = _parse_date(ini_str) if ini_str else _date(ano, mes, 1)
        dt_fim = _parse_date(fim_str) if fim_str else hoje
    else:
        dt_ini = _date(ano, mes, 1)
        dt_fim = _date(ano, mes, calendar.monthrange(ano, mes)[1])
    return dt_ini, dt_fim


# ── 1. Ranking de gastos por categoria ────────────────────────────────────────

@api_bp.route('/resumo/categorias', methods=['GET'])
@api_key_required
def resumo_categorias(usuario):
    """
    Ranking de gastos por categoria no período informado.
    Query params: mes, ano  OU  data_inicio, data_fim
    Retorna lista ordenada por valor, % do total e variação vs período anterior.
    """
    try:
        dt_ini, dt_fim = _periodo_from_args()
    except (ValueError, TypeError):
        return jsonify({'erro': 'Data inválida. Use YYYY-MM-DD'}), 422

    rows = (
        db.session.query(
            Despesa.categoria_id,
            db.func.sum(Despesa.valor).label('total'),
            db.func.count(Despesa.id).label('qtd'),
        )
        .filter(
            Despesa.user_id == usuario.id,
            Despesa.data_pagamento >= dt_ini,
            Despesa.data_pagamento <= dt_fim,
        )
        .group_by(Despesa.categoria_id)
        .order_by(db.desc('total'))
        .all()
    )

    total_geral = sum(r.total for r in rows) or 0

    # Período anterior de mesmo tamanho
    delta = (dt_fim - dt_ini).days + 1
    dt_ini_ant = dt_ini - timedelta(days=delta)
    dt_fim_ant = dt_ini - timedelta(days=1)
    ant_rows = (
        db.session.query(Despesa.categoria_id, db.func.sum(Despesa.valor).label('total'))
        .filter(
            Despesa.user_id == usuario.id,
            Despesa.data_pagamento >= dt_ini_ant,
            Despesa.data_pagamento <= dt_fim_ant,
        )
        .group_by(Despesa.categoria_id)
        .all()
    )
    ant_map = {r.categoria_id: round(r.total, 2) for r in ant_rows}

    cat_ids = [r.categoria_id for r in rows]
    cats = {c.id: c.nome for c in CategoriaDespesa.query.filter(CategoriaDespesa.id.in_(cat_ids)).all()}

    dados = []
    for r in rows:
        total = round(r.total, 2)
        ant_val = ant_map.get(r.categoria_id, 0)
        variacao = round((total - ant_val) / ant_val * 100, 1) if ant_val else None
        dados.append({
            'categoria_codigo': r.categoria_id,
            'categoria_nome': cats.get(r.categoria_id, '?'),
            'total': total,
            'qtd_transacoes': r.qtd,
            'percentual_do_total': round(total / total_geral * 100, 1) if total_geral else 0,
            'periodo_anterior': ant_val,
            'variacao_percentual': variacao,
        })

    return jsonify({
        'periodo': {'inicio': dt_ini.isoformat(), 'fim': dt_fim.isoformat()},
        'total_geral': round(total_geral, 2),
        'categorias': dados,
    })


# ── 2. Status do orçamento ────────────────────────────────────────────────────

@api_bp.route('/orcamento/status', methods=['GET'])
@api_key_required
def orcamento_status(usuario):
    """
    Status do orçamento por categoria no mês informado.
    Query params: mes, ano (padrão: mês atual)
    Alertas: EXCEDIDO (>=100%), ATENCAO (>=80%), PROJECAO_EXCEDE (projeção > orçado)
    """
    hoje = _date.today()
    mes = request.args.get('mes', type=int) or hoje.month
    ano = request.args.get('ano', type=int) or hoje.year

    dt_ini = _date(ano, mes, 1)
    dias_mes = calendar.monthrange(ano, mes)[1]
    dt_fim = _date(ano, mes, dias_mes)

    orcamentos = Orcamento.query.filter_by(user_id=usuario.id).all()
    if not orcamentos:
        return jsonify({'mensagem': 'Nenhum orçamento cadastrado', 'categorias': []}), 200

    gastos_rows = (
        db.session.query(Despesa.categoria_id, db.func.sum(Despesa.valor).label('total'))
        .filter(
            Despesa.user_id == usuario.id,
            Despesa.data_pagamento >= dt_ini,
            Despesa.data_pagamento <= dt_fim,
        )
        .group_by(Despesa.categoria_id)
        .all()
    )
    gastos_map = {g.categoria_id: round(g.total, 2) for g in gastos_rows}

    dias_passados = hoje.day if (mes == hoje.month and ano == hoje.year) else dias_mes
    dias_restantes = max(0, dias_mes - dias_passados)

    resultado = []
    for orc in sorted(orcamentos, key=lambda o: o.categoria.nome if o.categoria else ''):
        gasto = gastos_map.get(orc.categoria_id, 0)
        saldo = round(orc.valor_orcado - gasto, 2)
        pct = round(gasto / orc.valor_orcado * 100, 1) if orc.valor_orcado else 0
        projecao = round(gasto / dias_passados * dias_mes, 2) if dias_passados else gasto

        if pct >= 100:
            alerta = 'EXCEDIDO'
        elif pct >= 80:
            alerta = 'ATENCAO'
        elif projecao > orc.valor_orcado:
            alerta = 'PROJECAO_EXCEDE'
        else:
            alerta = None

        resultado.append({
            'categoria_codigo': orc.categoria_id,
            'categoria_nome': orc.categoria.nome if orc.categoria else '?',
            'orcado': round(orc.valor_orcado, 2),
            'gasto': gasto,
            'saldo': saldo,
            'percentual_utilizado': pct,
            'projecao_mensal': projecao,
            'alerta': alerta,
        })

    return jsonify({
        'periodo': {'mes': mes, 'ano': ano, 'dias_passados': dias_passados, 'dias_restantes': dias_restantes},
        'total_orcado': round(sum(o.valor_orcado for o in orcamentos), 2),
        'total_gasto': round(sum(gastos_map.values()), 2),
        'categorias': resultado,
    })


# ── 3. Comparativo mensal ─────────────────────────────────────────────────────

@api_bp.route('/resumo/mensal', methods=['GET'])
@api_key_required
def resumo_mensal(usuario):
    """
    Comparativo de despesas e receitas mês a mês.
    Query params: meses (int, padrão 6, máx 24)
    Retorna: por mês: total_despesas, total_receitas, saldo, variacao_despesas_pct
    """
    hoje = _date.today()
    n_meses = min(request.args.get('meses', 6, type=int), 24)

    meses = []
    for i in range(n_meses - 1, -1, -1):
        m = hoje.month - i
        a = hoje.year
        while m <= 0:
            m += 12
            a -= 1
        dt_ini = _date(a, m, 1)
        dt_fim = _date(a, m, calendar.monthrange(a, m)[1])

        desp = db.session.query(db.func.sum(Despesa.valor)).filter(
            Despesa.user_id == usuario.id,
            Despesa.data_pagamento >= dt_ini,
            Despesa.data_pagamento <= dt_fim,
        ).scalar() or 0

        rec = db.session.query(db.func.sum(Receita.valor)).filter(
            Receita.user_id == usuario.id,
            Receita.data_recebimento >= dt_ini,
            Receita.data_recebimento <= dt_fim,
        ).scalar() or 0

        meses.append({
            'mes': m,
            'ano': a,
            'mes_ano': f"{m:02d}/{a}",
            'total_despesas': round(desp, 2),
            'total_receitas': round(rec, 2),
            'saldo': round(rec - desp, 2),
            'variacao_despesas_pct': None,
        })

    for i in range(1, len(meses)):
        ant = meses[i - 1]['total_despesas']
        atual = meses[i]['total_despesas']
        meses[i]['variacao_despesas_pct'] = round((atual - ant) / ant * 100, 1) if ant else None

    media_desp = round(sum(m['total_despesas'] for m in meses) / len(meses), 2) if meses else 0
    media_rec = round(sum(m['total_receitas'] for m in meses) / len(meses), 2) if meses else 0

    return jsonify({
        'meses': meses,
        'media_mensal_despesas': media_desp,
        'media_mensal_receitas': media_rec,
    })


# ── 4. Gastos por meio de pagamento (cartões) ─────────────────────────────────

@api_bp.route('/resumo/cartoes', methods=['GET'])
@api_key_required
def resumo_cartoes(usuario):
    """
    Gastos agrupados por meio de pagamento no período informado.
    Query params: mes, ano  OU  data_inicio, data_fim
    """
    try:
        dt_ini, dt_fim = _periodo_from_args()
    except (ValueError, TypeError):
        return jsonify({'erro': 'Data inválida. Use YYYY-MM-DD'}), 422

    rows = (
        db.session.query(
            Despesa.meio_pagamento_id,
            db.func.sum(Despesa.valor).label('total'),
            db.func.count(Despesa.id).label('qtd'),
        )
        .filter(
            Despesa.user_id == usuario.id,
            Despesa.data_pagamento >= dt_ini,
            Despesa.data_pagamento <= dt_fim,
        )
        .group_by(Despesa.meio_pagamento_id)
        .order_by(db.desc('total'))
        .all()
    )

    total_geral = sum(r.total for r in rows) or 0
    meio_ids = [r.meio_pagamento_id for r in rows]
    meios = {
        m.id: {'nome': m.nome, 'tipo': m.tipo}
        for m in MeioPagamento.query.filter(MeioPagamento.id.in_(meio_ids)).all()
    }

    dados = []
    for r in rows:
        total = round(r.total, 2)
        info = meios.get(r.meio_pagamento_id, {'nome': '?', 'tipo': '?'})
        dados.append({
            'meio_pagamento_codigo': r.meio_pagamento_id,
            'meio_pagamento_nome': info['nome'],
            'tipo': info['tipo'],
            'total': total,
            'qtd_transacoes': r.qtd,
            'percentual_do_total': round(total / total_geral * 100, 1) if total_geral else 0,
        })

    return jsonify({
        'periodo': {'inicio': dt_ini.isoformat(), 'fim': dt_fim.isoformat()},
        'total_geral': round(total_geral, 2),
        'meios_pagamento': dados,
    })

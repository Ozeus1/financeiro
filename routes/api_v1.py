"""
REST API v1 — FiNan
Autenticação: header  X-API-Key: <sua_chave>
Todos os endpoints exigem a chave e retornam apenas dados do usuário dono da chave.
"""
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import date, datetime
from sqlalchemy import extract

from models import (
    db, ApiKey,
    Despesa, Receita,
    CategoriaDespesa, CategoriaReceita,
    MeioPagamento, MeioRecebimento,
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
    """Converte string YYYY-MM-DD para date, levanta ValueError se inválido."""
    return date.fromisoformat(s)


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
    Query params: mes, ano, categoria_codigo, meio_pagamento_codigo, pagina, por_pagina
    """
    q = Despesa.query.filter_by(user_id=usuario.id)

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

    total = q.count()
    pagina = max(1, request.args.get('pagina', 1, type=int))
    por_pagina = min(request.args.get('por_pagina', 50, type=int), 200)
    despesas = (q.order_by(Despesa.data_pagamento.desc())
                 .offset((pagina - 1) * por_pagina)
                 .limit(por_pagina).all())

    return jsonify({
        'total': total,
        'pagina': pagina,
        'por_pagina': por_pagina,
        'paginas': max(1, (total + por_pagina - 1) // por_pagina),
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

    categoria = CategoriaDespesa.query.filter_by(id=data['categoria_codigo'], user_id=usuario.id).first()
    if not categoria:
        return jsonify({'erro': 'categoria_codigo inválido ou não pertence ao usuário'}), 422

    meio = MeioPagamento.query.filter_by(id=data['meio_pagamento_codigo'], user_id=usuario.id).first()
    if not meio:
        return jsonify({'erro': 'meio_pagamento_codigo inválido ou não pertence ao usuário'}), 422

    try:
        dt_pag = _parse_date(data['data_pagamento'])
    except (ValueError, TypeError):
        return jsonify({'erro': 'data_pagamento inválida. Use YYYY-MM-DD'}), 422

    try:
        valor = float(data['valor'])
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
    Query params: mes, ano, categoria_codigo, meio_recebimento_codigo, pagina, por_pagina
    """
    q = Receita.query.filter_by(user_id=usuario.id)

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

    total = q.count()
    pagina = max(1, request.args.get('pagina', 1, type=int))
    por_pagina = min(request.args.get('por_pagina', 50, type=int), 200)
    receitas = (q.order_by(Receita.data_recebimento.desc())
                  .offset((pagina - 1) * por_pagina)
                  .limit(por_pagina).all())

    return jsonify({
        'total': total,
        'pagina': pagina,
        'por_pagina': por_pagina,
        'paginas': max(1, (total + por_pagina - 1) // por_pagina),
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

    categoria = CategoriaReceita.query.filter_by(id=data['categoria_codigo'], user_id=usuario.id).first()
    if not categoria:
        return jsonify({'erro': 'categoria_codigo inválido ou não pertence ao usuário'}), 422

    meio = MeioRecebimento.query.filter_by(id=data['meio_recebimento_codigo'], user_id=usuario.id).first()
    if not meio:
        return jsonify({'erro': 'meio_recebimento_codigo inválido ou não pertence ao usuário'}), 422

    try:
        dt_rec = _parse_date(data['data_recebimento'])
    except (ValueError, TypeError):
        return jsonify({'erro': 'data_recebimento inválida. Use YYYY-MM-DD'}), 422

    try:
        valor = float(data['valor'])
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

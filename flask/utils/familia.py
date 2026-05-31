"""Helpers para o plano família — acesso compartilhado ao banco de dados"""
from flask_login import current_user
from models import db, Despesa, Receita, CategoriaDespesa, CategoriaReceita, MeioPagamento, MeioRecebimento, User


def get_user_ids_grupo():
    """Retorna lista de user_ids do grupo família (ou só o próprio user se não for família)"""
    if current_user.is_familia() and current_user.grupo_familia_id:
        membros = User.query.filter_by(grupo_familia_id=current_user.grupo_familia_id).all()
        return [m.id for m in membros]
    return [current_user.id]


def filtrar_despesas(query=None):
    """Filtra despesas pelo grupo ou pelo usuário"""
    if query is None:
        query = Despesa.query
    if current_user.is_familia() and current_user.grupo_familia_id:
        ids = get_user_ids_grupo()
        return query.filter(Despesa.user_id.in_(ids))
    return query.filter_by(user_id=current_user.id)


def filtrar_receitas(query=None):
    """Filtra receitas pelo grupo ou pelo usuário"""
    if query is None:
        query = Receita.query
    if current_user.is_familia() and current_user.grupo_familia_id:
        ids = get_user_ids_grupo()
        return query.filter(Receita.user_id.in_(ids))
    return query.filter_by(user_id=current_user.id)


def get_categorias_despesa():
    """Retorna categorias de despesa do grupo ou do usuário"""
    if current_user.is_familia() and current_user.grupo_familia_id:
        ids = get_user_ids_grupo()
        return CategoriaDespesa.query.filter(
            CategoriaDespesa.user_id.in_(ids), CategoriaDespesa.ativo == True
        ).order_by(CategoriaDespesa.nome).all()
    return CategoriaDespesa.query.filter_by(
        user_id=current_user.id, ativo=True
    ).order_by(CategoriaDespesa.nome).all()


def get_categorias_receita():
    if current_user.is_familia() and current_user.grupo_familia_id:
        ids = get_user_ids_grupo()
        return CategoriaReceita.query.filter(
            CategoriaReceita.user_id.in_(ids), CategoriaReceita.ativo == True
        ).order_by(CategoriaReceita.nome).all()
    return CategoriaReceita.query.filter_by(
        user_id=current_user.id, ativo=True
    ).order_by(CategoriaReceita.nome).all()


def get_meios_pagamento():
    if current_user.is_familia() and current_user.grupo_familia_id:
        ids = get_user_ids_grupo()
        return MeioPagamento.query.filter(
            MeioPagamento.user_id.in_(ids), MeioPagamento.ativo == True
        ).order_by(MeioPagamento.nome).all()
    return MeioPagamento.query.filter_by(
        user_id=current_user.id, ativo=True
    ).order_by(MeioPagamento.nome).all()


def get_meios_recebimento():
    if current_user.is_familia() and current_user.grupo_familia_id:
        ids = get_user_ids_grupo()
        return MeioRecebimento.query.filter(
            MeioRecebimento.user_id.in_(ids), MeioRecebimento.ativo == True
        ).order_by(MeioRecebimento.nome).all()
    return MeioRecebimento.query.filter_by(
        user_id=current_user.id, ativo=True
    ).order_by(MeioRecebimento.nome).all()


def owner_id_para_novo_registro():
    """Para registros novos no plano família, usa o user_id do assinante (dono do grupo)"""
    if current_user.is_familia() and current_user.grupo_familia_id:
        from models import GrupoFamilia
        grupo = GrupoFamilia.query.get(current_user.grupo_familia_id)
        if grupo:
            return grupo.assinante_id
    return current_user.id

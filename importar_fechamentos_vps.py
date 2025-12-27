# Script para importar fechamentos de cartoes no Flask/PostgreSQL
# Execute na VPS dentro da pasta /var/www/financeiro

from models import db, FechamentoCartao, MeioPagamento
from app import app

# Execute dentro do contexto da aplicacao
with app.app_context():
    # Cartão Azul
    meio = MeioPagamento.query.filter_by(nome='Cartão Azul').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=1,
                dia_vencimento=11
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão Azul - Fecha: 1, Vence: 11')
        else:
            print(f'[SKIP] Ja existe: Cartão Azul')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão Azul')

    # Cartão BB
    meio = MeioPagamento.query.filter_by(nome='Cartão BB').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=30,
                dia_vencimento=9
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão BB - Fecha: 30, Vence: 9')
        else:
            print(f'[SKIP] Ja existe: Cartão BB')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão BB')

    # Cartão C6
    meio = MeioPagamento.query.filter_by(nome='Cartão C6').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=4,
                dia_vencimento=14
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão C6 - Fecha: 4, Vence: 14')
        else:
            print(f'[SKIP] Ja existe: Cartão C6')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão C6')

    # Cartão Gol
    meio = MeioPagamento.query.filter_by(nome='Cartão Gol').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=1,
                dia_vencimento=11
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão Gol - Fecha: 1, Vence: 11')
        else:
            print(f'[SKIP] Ja existe: Cartão Gol')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão Gol')

    # Cartão Latam
    meio = MeioPagamento.query.filter_by(nome='Cartão Latam').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=1,
                dia_vencimento=11
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão Latam - Fecha: 1, Vence: 11')
        else:
            print(f'[SKIP] Ja existe: Cartão Latam')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão Latam')

    # Cartão Mercado Pago
    meio = MeioPagamento.query.filter_by(nome='Cartão Mercado Pago').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=8,
                dia_vencimento=18
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão Mercado Pago - Fecha: 8, Vence: 18')
        else:
            print(f'[SKIP] Ja existe: Cartão Mercado Pago')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão Mercado Pago')

    # Cartão Nubank
    meio = MeioPagamento.query.filter_by(nome='Cartão Nubank').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=30,
                dia_vencimento=9
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão Nubank - Fecha: 30, Vence: 9')
        else:
            print(f'[SKIP] Ja existe: Cartão Nubank')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão Nubank')

    # Cartão Pão de Açúcar
    meio = MeioPagamento.query.filter_by(nome='Cartão Pão de Açúcar').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=30,
                dia_vencimento=9
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão Pão de Açúcar - Fecha: 30, Vence: 9')
        else:
            print(f'[SKIP] Ja existe: Cartão Pão de Açúcar')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão Pão de Açúcar')

    # Cartão Unlimited Master
    meio = MeioPagamento.query.filter_by(nome='Cartão Unlimited Master').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=3,
                dia_vencimento=13
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão Unlimited Master - Fecha: 3, Vence: 13')
        else:
            print(f'[SKIP] Ja existe: Cartão Unlimited Master')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão Unlimited Master')

    # Cartão Unlimited Visa
    meio = MeioPagamento.query.filter_by(nome='Cartão Unlimited Visa').first()
    if meio:
        existe = FechamentoCartao.query.filter_by(meio_pagamento_id=meio.id).first()
        if not existe:
            fechamento = FechamentoCartao(
                meio_pagamento_id=meio.id,
                dia_fechamento=1,
                dia_vencimento=11
            )
            db.session.add(fechamento)
            print(f'[OK] Adicionado: Cartão Unlimited Visa - Fecha: 1, Vence: 11')
        else:
            print(f'[SKIP] Ja existe: Cartão Unlimited Visa')
    else:
        print(f'[AVISO] Meio de pagamento nao encontrado: Cartão Unlimited Visa')

    # Salvar no banco
    try:
        db.session.commit()
        print('[OK] Fechamentos salvos com sucesso!')
    except Exception as e:
        db.session.rollback()
        print(f'[ERRO] Falha ao salvar: {e}')

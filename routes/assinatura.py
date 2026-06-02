from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, User, Assinatura, ConfigSistema
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import json

assinatura_bp = Blueprint('assinatura', __name__, url_prefix='/assinatura')

PLANOS = {
    'basic': {
        'nome': 'Basic',
        'preco': 6.90,
        'cor': '#20c997',
        'icone': 'bi-rocket-takeoff-fill',
        'descricao': 'Tudo do Free, sem nenhum limite — ideal para quem quer crescer',
        'recursos': [
            ('check-circle-fill text-success', 'Registros mensais ilimitados'),
            ('check-circle-fill text-success', 'Categorias ilimitadas'),
            ('check-circle-fill text-success', 'Cartões ilimitados'),
            ('check-circle-fill text-success', 'Todos os relatórios'),
            ('check-circle-fill text-success', 'Fluxo de caixa'),
            ('x-circle-fill text-danger', 'Sem Robô de IA via WhatsApp'),
            ('x-circle-fill text-danger', 'Sem separação PF/PJ'),
        ],
    },
    'familia': {
        'nome': 'Família',
        'preco': 34.90,
        'cor': '#e67e22',
        'icone': 'bi-house-heart-fill',
        'descricao': 'Para famílias que querem gerenciar finanças juntas — até 5 usuários',
        'recursos': [
            ('check-circle-fill text-success', 'Até 5 usuários no mesmo banco'),
            ('check-circle-fill text-success', 'Banco de dados compartilhado'),
            ('check-circle-fill text-success', 'Despesas e receitas ilimitadas'),
            ('check-circle-fill text-success', 'Categorias e meios compartilhados'),
            ('check-circle-fill text-success', 'Relatório por membro do grupo'),
            ('check-circle-fill text-success', 'Acesso ao Robô de IA via WhatsApp'),
            ('check-circle-fill text-success', 'Convite por e-mail ou link'),
            ('x-circle-fill text-danger', 'Separação PF/PJ — apenas ProMax'),
        ],
    },
    'pro': {
        'nome': 'Pro',
        'preco': 19.90,
        'cor': '#4361ee',
        'icone': 'bi-star-fill',
        'descricao': 'Ideal para quem quer controle financeiro pessoal completo',
        'recursos': [
            ('check-circle-fill text-success', 'Despesas e receitas ilimitadas'),
            ('check-circle-fill text-success', 'Categorias ilimitadas'),
            ('check-circle-fill text-success', 'Cartões ilimitados'),
            ('check-circle-fill text-success', 'Registros mensais ilimitados'),
            ('check-circle-fill text-success', 'Todos os relatórios'),
            ('check-circle-fill text-success', 'Acesso ao Robô de IA via WhatsApp'),
            ('check-circle-fill text-success', 'Gerente Financeiro IA'),
            ('check-circle-fill text-success', 'Exportação para Excel'),
            ('x-circle-fill text-danger', 'Separação PF/PJ — apenas ProMax'),
        ],
    },
    'promax': {
        'nome': 'ProMax',
        'preco': 27.90,
        'cor': '#6f42c1',
        'icone': 'bi-stars',
        'descricao': 'Para quem gerencia finanças pessoais e empresariais separadas',
        'recursos': [
            ('check-circle-fill text-success', 'Tudo do plano Pro'),
            ('check-circle-fill text-success', 'Separação de contas PF e PJ'),
            ('check-circle-fill text-success', 'Relatórios PF vs PJ com gráficos'),
            ('check-circle-fill text-success', 'Dashboard separado por entidade'),
            ('check-circle-fill text-success', 'Filtros PF/PJ em todas as telas'),
            ('check-circle-fill text-success', 'Acesso ao Robô de IA via WhatsApp'),
            ('check-circle-fill text-success', 'Gerente Financeiro IA'),
        ],
    },
}

PLANO_FREE = {
    'nome': 'Free',
    'preco': 0,
    'cor': '#6c757d',
    'icone': 'bi-gift',
    'descricao': 'Para começar a organizar suas finanças',
    'recursos': [
        ('check-circle-fill text-success', 'Até 300 registros por mês'),
        ('check-circle-fill text-success', 'Até 10 categorias de despesa'),
        ('check-circle-fill text-success', 'Até 2 cartões'),
        ('check-circle-fill text-success', 'Relatórios básicos'),
        ('x-circle-fill text-danger', 'Sem acesso ao Robô de IA'),
        ('x-circle-fill text-danger', 'Sem Gerente Financeiro IA'),
        ('x-circle-fill text-danger', 'Sem separação PF/PJ'),
    ],
}


@assinatura_bp.route('/planos')
def planos():
    """Página pública de planos"""
    return render_template('assinatura/planos.html',
                           planos=PLANOS,
                           plano_free=PLANO_FREE)


@assinatura_bp.route('/minha-assinatura')
@login_required
def minha_assinatura():
    """Tela do usuário com seu plano atual e opção de assinar"""
    historico = Assinatura.query.filter_by(user_id=current_user.id)\
        .order_by(Assinatura.data_criacao.desc()).limit(10).all()

    # Lista de dicts com todos os planos na ordem de exibição
    def _r(icone, texto):
        return {'icone': icone, 'texto': texto}

    todos_planos = [
        {'pid': 'free', 'nome': 'Free', 'cor': '#6c757d', 'icone': 'bi-gift', 'preco': 0,
         'recursos': [
             _r('dash-circle text-warning',       '300 registros/mês'),
             _r('dash-circle text-warning',       '10 categorias de despesa'),
             _r('dash-circle text-warning',       '2 cartões'),
             _r('check-circle-fill text-success', 'Todos os relatórios'),
             _r('x-circle text-danger',           'Sem Robô de IA'),
             _r('x-circle text-danger',           'Sem separação PF/PJ'),
         ]},
        {'pid': 'basic', 'nome': 'Basic', 'cor': '#20c997', 'icone': 'bi-rocket-takeoff-fill', 'preco': 6.90,
         'recursos': [
             _r('check-circle-fill text-success', 'Registros ilimitados'),
             _r('check-circle-fill text-success', 'Categorias ilimitadas'),
             _r('check-circle-fill text-success', 'Cartões ilimitados'),
             _r('check-circle-fill text-success', 'Todos os relatórios'),
             _r('x-circle text-danger',           'Sem Robô de IA'),
             _r('x-circle text-danger',           'Sem separação PF/PJ'),
         ]},
        {'pid': 'pro', 'nome': 'Pro', 'cor': '#4361ee', 'icone': 'bi-star-fill', 'preco': 19.90,
         'recursos': [
             _r('check-circle-fill text-success', 'Registros ilimitados'),
             _r('check-circle-fill text-success', 'Categorias ilimitadas'),
             _r('check-circle-fill text-success', 'Cartões ilimitados'),
             _r('check-circle-fill text-success', 'Todos os relatórios'),
             _r('check-circle-fill text-success', 'Robô de IA via WhatsApp'),
             _r('x-circle text-danger',           'Sem separação PF/PJ'),
         ]},
        {'pid': 'promax', 'nome': 'ProMax', 'cor': '#6f42c1', 'icone': 'bi-stars', 'preco': 27.90,
         'recursos': [
             _r('check-circle-fill text-success', 'Tudo do plano Pro'),
             _r('check-circle-fill text-success', 'Separação PF/PJ'),
             _r('check-circle-fill text-success', 'Relatórios PF vs PJ'),
             _r('check-circle-fill text-success', 'Dashboard por entidade'),
             _r('check-circle-fill text-success', 'Robô de IA via WhatsApp'),
             _r('check-circle-fill text-success', 'Filtros PF/PJ em todas as telas'),
         ]},
        {'pid': 'familia', 'nome': 'Família', 'cor': '#e67e22', 'icone': 'bi-house-heart-fill', 'preco': 34.90,
         'recursos': [
             _r('check-circle-fill text-success', 'Até 5 usuários compartilhados'),
             _r('check-circle-fill text-success', 'Banco de dados compartilhado'),
             _r('check-circle-fill text-success', 'Registros ilimitados'),
             _r('check-circle-fill text-success', 'Relatório por membro'),
             _r('check-circle-fill text-success', 'Robô de IA via WhatsApp'),
             _r('x-circle text-danger',           'Sem separação PF/PJ'),
         ]},
    ]

    return render_template('assinatura/minha_assinatura.html',
                           todos_planos=todos_planos,
                           historico=historico)


@assinatura_bp.route('/iniciar/<plano>', methods=['GET', 'POST'])
@login_required
def iniciar(plano):
    """Cria preferência de pagamento no Mercado Pago e redireciona"""
    plano = plano.strip().lower() if plano else ''
    if plano not in PLANOS:
        return redirect(url_for('assinatura.minha_assinatura'))

    ciclo = request.form.get('ciclo', 'mensal').strip().lower()
    if ciclo not in ('mensal', 'anual'):
        ciclo = 'mensal'

    mp_access_token = ConfigSistema.get('mp_access_token', '')
    if not mp_access_token:
        flash('Sistema de pagamento não configurado. Entre em contato com o administrador.', 'danger')
        return redirect(url_for('assinatura.minha_assinatura'))

    try:
        import mercadopago
        sdk = mercadopago.SDK(mp_access_token)

        info = PLANOS[plano]
        preco_mensal = info['preco']
        if ciclo == 'anual':
            # 20% de desconto no anual, cobrado de uma vez
            valor = round(preco_mensal * 12 * 0.80, 2)
            titulo = f'FiNan {info["nome"]} — Assinatura Anual (20% off)'
        else:
            valor = preco_mensal
            titulo = f'FiNan {info["nome"]} — Assinatura Mensal'

        base_url = request.host_url.rstrip('/')

        preference_data = {
            'items': [{
                'title': titulo,
                'quantity': 1,
                'unit_price': valor,
                'currency_id': 'BRL',
            }],
            'payer': {
                'name': current_user.nome or current_user.username,
                'email': current_user.email,
            },
            'back_urls': {
                'success': f'{base_url}/assinatura/sucesso',
                'failure': f'{base_url}/assinatura/falha',
                'pending': f'{base_url}/assinatura/pendente',
            },
            'auto_return': 'approved',
            'notification_url': f'{base_url}/assinatura/webhook',
            'external_reference': f'{current_user.id}|{plano}|{ciclo}',
            'statement_descriptor': 'FINAN ASSINATURA',
        }

        result = sdk.preference().create(preference_data)
        preference = result['response']

        # Registra assinatura pendente
        ass = Assinatura(
            user_id=current_user.id,
            plano=plano,
            status='pendente',
            valor=valor,
            mp_preference_id=preference.get('id'),
        )
        db.session.add(ass)
        db.session.commit()

        # Redireciona para checkout do MP
        init_point = preference.get('init_point')
        return redirect(init_point)

    except ImportError:
        flash('Biblioteca mercadopago não instalada no servidor.', 'danger')
        return redirect(url_for('assinatura.minha_assinatura'))
    except Exception as e:
        flash(f'Erro ao iniciar pagamento: {e}', 'danger')
        return redirect(url_for('assinatura.minha_assinatura'))


@assinatura_bp.route('/sucesso')
@login_required
def sucesso():
    payment_id = request.args.get('payment_id')
    status = request.args.get('status')
    external_ref = request.args.get('external_reference', '')

    if status == 'approved' and external_ref:
        _aprovar_assinatura(payment_id, external_ref)

    flash('Pagamento aprovado! Seu plano foi ativado.', 'success')
    return redirect(url_for('assinatura.minha_assinatura'))


@assinatura_bp.route('/falha')
@login_required
def falha():
    flash('Pagamento não aprovado. Tente novamente ou escolha outro método.', 'danger')
    return redirect(url_for('assinatura.minha_assinatura'))


@assinatura_bp.route('/pendente')
@login_required
def pendente():
    flash('Pagamento pendente. Você receberá um e-mail quando for confirmado.', 'info')
    return redirect(url_for('assinatura.minha_assinatura'))


@assinatura_bp.route('/webhook', methods=['POST'])
def webhook():
    """Webhook do Mercado Pago para confirmação automática"""
    try:
        data = request.get_json(silent=True) or {}
        topic = data.get('type') or request.args.get('topic', '')
        resource_id = data.get('data', {}).get('id') or request.args.get('id')

        if topic in ('payment', 'merchant_order') and resource_id:
            mp_access_token = ConfigSistema.get('mp_access_token', '')
            import mercadopago
            sdk = mercadopago.SDK(mp_access_token)

            if topic == 'payment':
                result = sdk.payment().get(resource_id)
                payment = result['response']
                if payment.get('status') == 'approved':
                    ext_ref = payment.get('external_reference', '')
                    _aprovar_assinatura(str(resource_id), ext_ref)

    except Exception as e:
        print(f'Webhook error: {e}')

    return jsonify({'status': 'ok'}), 200


def _aprovar_assinatura(payment_id, external_ref):
    """Ativa o plano do usuário após pagamento aprovado"""
    try:
        partes = external_ref.split('|')
        if len(partes) < 2:
            return
        user_id = int(partes[0])
        plano   = partes[1]
        ciclo   = partes[2] if len(partes) >= 3 else 'mensal'
        if plano not in PLANOS:
            return

        user = User.query.get(user_id)
        if not user:
            return

        meses = 12 if ciclo == 'anual' else 1

        # Atualiza assinatura pendente
        ass = Assinatura.query.filter_by(
            user_id=user_id, status='pendente'
        ).order_by(Assinatura.data_criacao.desc()).first()
        if ass:
            ass.status = 'aprovado'
            ass.mp_payment_id = payment_id
            ass.data_aprovacao = datetime.utcnow()
            ass.data_expiracao = (date.today() + relativedelta(months=meses))

        # Ativa plano do usuário
        user.nivel_acesso = plano
        user.data_validade = date.today() + relativedelta(months=meses)

        # Plano família: criar grupo se ainda não tem
        if plano == 'familia':
            from models import GrupoFamilia
            if not user.grupo_familia_id:
                grupo = GrupoFamilia(
                    nome=f'Família de {user.nome or user.username}',
                    assinante_id=user.id,
                    ativo=True
                )
                db.session.add(grupo)
                db.session.flush()  # gera o id
                user.grupo_familia_id = grupo.id
                user.eh_assinante_familia = True
            else:
                # Reativação — garante que é assinante
                user.eh_assinante_familia = True

        db.session.commit()

    except Exception as e:
        print(f'Erro ao aprovar assinatura: {e}')


@assinatura_bp.route('/admin/config', methods=['GET', 'POST'])
@login_required
def admin_config():
    """Admin: configurar credenciais Mercado Pago"""
    from routes.auth import admin_required
    if not current_user.is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        ConfigSistema.set('mp_access_token', request.form.get('mp_access_token', '').strip())
        ConfigSistema.set('mp_public_key', request.form.get('mp_public_key', '').strip())
        db.session.commit()
        flash('Credenciais do Mercado Pago salvas!', 'success')
        return redirect(url_for('assinatura.admin_config'))

    mp_access_token = ConfigSistema.get('mp_access_token', '')
    mp_public_key = ConfigSistema.get('mp_public_key', '')
    return render_template('assinatura/admin_config.html',
                           mp_access_token=mp_access_token,
                           mp_public_key=mp_public_key)

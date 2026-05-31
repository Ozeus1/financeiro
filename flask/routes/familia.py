from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, GrupoFamilia, ConviteFamilia, Despesa, Receita, CategoriaDespesa
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, extract
import secrets

familia_bp = Blueprint('familia', __name__, url_prefix='/familia')


def _exige_assinante(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_familia() or not current_user.eh_assinante_familia:
            flash('Apenas o assinante do plano família pode acessar esta área.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


@familia_bp.route('/painel')
@login_required
def painel():
    """Painel de gestão do grupo família"""
    if not current_user.is_familia():
        flash('Você não tem o plano família.', 'warning')
        return redirect(url_for('assinatura.minha_assinatura'))

    grupo = GrupoFamilia.query.get(current_user.grupo_familia_id)
    if not grupo:
        flash('Grupo não encontrado.', 'danger')
        return redirect(url_for('main.dashboard'))

    membros = User.query.filter_by(grupo_familia_id=grupo.id).all()
    convites_ativos = ConviteFamilia.query.filter_by(
        grupo_id=grupo.id, usado=False
    ).all()
    convites_ativos = [c for c in convites_ativos if c.esta_valido()]

    return render_template('familia/painel.html',
                           grupo=grupo,
                           membros=membros,
                           convites_ativos=convites_ativos,
                           eh_assinante=current_user.eh_assinante_familia)


@familia_bp.route('/convidar', methods=['POST'])
@login_required
@_exige_assinante
def convidar():
    """Gera convite para novo membro"""
    grupo = GrupoFamilia.query.get(current_user.grupo_familia_id)
    if not grupo.pode_adicionar():
        flash(f'Limite de {grupo.max_membros} membros atingido.', 'warning')
        return redirect(url_for('familia.painel'))

    email = request.form.get('email', '').strip() or None
    token = secrets.token_urlsafe(24)
    expiracao = datetime.utcnow() + relativedelta(days=7)

    convite = ConviteFamilia(
        grupo_id=grupo.id,
        email_convidado=email,
        token=token,
        data_expiracao=expiracao
    )
    db.session.add(convite)
    db.session.commit()

    link = url_for('familia.aceitar_convite', token=token, _external=True)

    # Enviar email se informado
    if email:
        _enviar_email_convite(email, link, current_user, grupo)
        flash(f'Convite enviado para {email}. Link válido por 7 dias.', 'success')
    else:
        flash(f'Link de convite gerado! Compartilhe: {link}', 'success')

    return redirect(url_for('familia.painel'))


@familia_bp.route('/remover/<int:membro_id>', methods=['POST'])
@login_required
@_exige_assinante
def remover_membro(membro_id):
    """Remove membro do grupo família"""
    if membro_id == current_user.id:
        flash('Você não pode se remover do grupo.', 'danger')
        return redirect(url_for('familia.painel'))

    membro = User.query.get_or_404(membro_id)
    if membro.grupo_familia_id != current_user.grupo_familia_id:
        flash('Este usuário não pertence ao seu grupo.', 'danger')
        return redirect(url_for('familia.painel'))

    membro.grupo_familia_id = None
    membro.eh_assinante_familia = False
    membro.nivel_acesso = 'free'
    db.session.commit()
    flash(f'{membro.nome or membro.username} removido do grupo.', 'success')
    return redirect(url_for('familia.painel'))


@familia_bp.route('/aceitar/<token>')
@login_required
def aceitar_convite(token):
    """Aceita convite e entra no grupo família"""
    convite = ConviteFamilia.query.filter_by(token=token).first()
    if not convite or not convite.esta_valido():
        flash('Convite inválido ou expirado.', 'danger')
        return redirect(url_for('main.dashboard'))

    grupo = GrupoFamilia.query.get(convite.grupo_id)
    if not grupo or not grupo.ativo:
        flash('Este grupo não está mais ativo.', 'danger')
        return redirect(url_for('main.dashboard'))

    if not grupo.pode_adicionar():
        flash('O grupo já atingiu o limite de membros.', 'warning')
        return redirect(url_for('main.dashboard'))

    if current_user.grupo_familia_id:
        flash('Você já pertence a um grupo família. Saia do grupo atual primeiro.', 'warning')
        return redirect(url_for('familia.painel'))

    # Verifica se usuário já tem dados (não é o primeiro)
    tem_dados = (Despesa.query.filter_by(user_id=current_user.id).first() is not None or
                 Receita.query.filter_by(user_id=current_user.id).first() is not None)

    return render_template('familia/aceitar_convite.html',
                           convite=convite,
                           grupo=grupo,
                           tem_dados=tem_dados,
                           token=token)


@familia_bp.route('/confirmar-entrada/<token>', methods=['POST'])
@login_required
def confirmar_entrada(token):
    """Confirma entrada no grupo após visualizar aviso"""
    convite = ConviteFamilia.query.filter_by(token=token).first()
    if not convite or not convite.esta_valido():
        flash('Convite inválido ou expirado.', 'danger')
        return redirect(url_for('main.dashboard'))

    grupo = GrupoFamilia.query.get(convite.grupo_id)

    current_user.grupo_familia_id = grupo.id
    current_user.nivel_acesso = 'familia'
    current_user.eh_assinante_familia = False
    current_user.data_validade = User.query.get(grupo.assinante_id).data_validade

    convite.usado = True
    db.session.commit()

    flash(f'Bem-vindo ao grupo família! Agora você compartilha o banco com os membros.', 'success')
    return redirect(url_for('familia.painel'))


@familia_bp.route('/relatorio')
@login_required
def relatorio():
    """Relatório: despesas e receitas por membro do grupo por mês"""
    if not current_user.is_familia():
        flash('Apenas membros do plano família acessam este relatório.', 'warning')
        return redirect(url_for('main.dashboard'))

    grupo = GrupoFamilia.query.get(current_user.grupo_familia_id)
    membros = User.query.filter_by(grupo_familia_id=grupo.id).all()
    membros_ids = [m.id for m in membros]

    mes = request.args.get('mes', datetime.now().month, type=int)
    ano = request.args.get('ano', datetime.now().year, type=int)

    MESES_PT = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
                'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

    # Despesas por membro
    despesas_por_membro = []
    receitas_por_membro = []
    for membro in membros:
        desp = db.session.query(func.sum(Despesa.valor)).join(CategoriaDespesa).filter(
            Despesa.registrado_por == membro.id,
            extract('month', Despesa.data_pagamento) == mes,
            extract('year', Despesa.data_pagamento) == ano,
            func.lower(CategoriaDespesa.nome) != 'pagamentos',
            Despesa.user_id.in_(membros_ids)
        ).scalar() or 0

        rec = db.session.query(func.sum(Receita.valor)).filter(
            Receita.registrado_por == membro.id,
            extract('month', Receita.data_recebimento) == mes,
            extract('year', Receita.data_recebimento) == ano,
            Receita.user_id.in_(membros_ids)
        ).scalar() or 0

        despesas_por_membro.append({'membro': membro, 'total': desp})
        receitas_por_membro.append({'membro': membro, 'total': rec})

    total_despesas = sum(d['total'] for d in despesas_por_membro)
    total_receitas = sum(r['total'] for r in receitas_por_membro)

    return render_template('familia/relatorio.html',
                           grupo=grupo,
                           membros=membros,
                           despesas_por_membro=despesas_por_membro,
                           receitas_por_membro=receitas_por_membro,
                           total_despesas=total_despesas,
                           total_receitas=total_receitas,
                           mes=mes,
                           ano=ano,
                           nome_mes=MESES_PT[mes-1])


def _enviar_email_convite(email_dest, link, remetente, grupo):
    try:
        from models import ConfigSistema
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        host = ConfigSistema.get('smtp_host', '')
        port = int(ConfigSistema.get('smtp_port', 465) or 465)
        secure = (ConfigSistema.get('smtp_secure', 'true') or 'true').lower() == 'true'
        smtp_user = ConfigSistema.get('smtp_user', '')
        password = ConfigSistema.get('smtp_password', '')
        from_ = ConfigSistema.get('smtp_from', smtp_user)
        if not host or not smtp_user:
            return
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Convite para o Plano Família FiNan — {remetente.nome or remetente.username}'
        msg['From'] = from_
        msg['To'] = email_dest
        html = f"""
        <div style="font-family:sans-serif;max-width:500px;margin:0 auto;padding:24px;border:1px solid #e2e8f0;border-radius:12px;">
            <h2 style="color:#4361ee;">FiNan — Convite Plano Família</h2>
            <p><strong>{remetente.nome or remetente.username}</strong> convidou você para compartilhar o plano família no FiNan.</p>
            <p>Com o plano família você terá acesso compartilhado a todas as despesas e receitas do grupo, com relatórios e funcionalidades completas.</p>
            <div style="text-align:center;margin:24px 0;">
                <a href="{link}" style="background:#4361ee;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;">
                    ✅ Aceitar Convite
                </a>
            </div>
            <p style="color:#64748b;font-size:.85rem;">Link válido por 7 dias. Se você não conhece {remetente.nome or remetente.username}, ignore este e-mail.</p>
        </div>"""
        msg.attach(MIMEText(html, 'html'))
        ctx = ssl.create_default_context()
        if secure:
            with smtplib.SMTP_SSL(host, port, context=ctx) as s:
                s.login(smtp_user, password)
                s.sendmail(from_, [email_dest], msg.as_string())
        else:
            with smtplib.SMTP(host, port) as s:
                s.ehlo(); s.starttls(context=ctx); s.login(smtp_user, password)
                s.sendmail(from_, [email_dest], msg.as_string())
    except Exception as e:
        print(f'Erro ao enviar convite: {e}')

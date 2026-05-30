from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def admin_required(f):
    """Decorator para requerer nível admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def gerente_required(f):
    """Decorator para requerer nível gerente ou superior (admin ou gerente)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_gerente():
            flash('Acesso negado. Permissão de gerente necessária.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def gerente_only_required(f):
    """Decorator exclusivo para gerente (não inclui admin — use admin_required para isso)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.nivel_acesso != 'gerente':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.email_confirmado:
                flash('Confirme seu e-mail antes de fazer login. Verifique sua caixa de entrada.', 'warning')
                return redirect(url_for('auth.login'))
            if not user.ativo:
                flash('Sua conta está inativa. Entre em contato com o administrador.', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=remember)
            flash(f'Bem-vindo, {user.username}!', 'success')
            
            # Redirecionar para a página solicitada ou dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Usuário ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
@gerente_required
def register():
    """Registrar novo usuário (apenas admin)"""
    if request.method == 'POST':
        from datetime import datetime as dt
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        nivel_acesso = request.form.get('nivel_acesso', 'pro')
        # Gerente não pode criar admin ou outro gerente
        if not current_user.is_admin() and nivel_acesso in ('admin', 'gerente'):
            nivel_acesso = 'pro'
        nome = request.form.get('nome', '').strip() or None
        whatsapp = request.form.get('whatsapp', '').strip() or None
        cpf_raw = request.form.get('cpf', '').strip()
        cpf = ''.join(filter(str.isdigit, cpf_raw)) or None
        modo_conta = request.form.get('modo_conta', 'pf') if nivel_acesso == 'promax' else 'pf'
        data_validade_str = request.form.get('data_validade', '').strip()
        data_validade = dt.strptime(data_validade_str, '%Y-%m-%d').date() if data_validade_str else None

        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(
            username=username,
            email=email,
            nivel_acesso=nivel_acesso,
            modo_conta=modo_conta,
            nome=nome,
            whatsapp=whatsapp,
            cpf=cpf,
            data_validade=data_validade,
            ativo=True,
            email_confirmado=True
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        from models import criar_dados_padrao_usuario
        criar_dados_padrao_usuario(new_user)
        db.session.commit()

        flash(f'Usuário {username} criado com sucesso!', 'success')
        return redirect(url_for('config.usuarios'))

    return render_template('auth/register.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
@login_required
@admin_required
def registro():
    """Alias de register para compatibilidade"""
    return register()


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Recuperação de senha (stub)"""
    from flask import render_template, flash, redirect, url_for
    flash('Entre em contato com o administrador para redefinir sua senha.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from flask import flash, redirect, url_for
    flash('Link inválido ou expirado. Entre em contato com o administrador.', 'danger')
    return redirect(url_for('auth.login'))


@auth_bp.route('/solicitar-acesso', methods=['GET', 'POST'])
def solicitar_acesso():
    """Auto-cadastro para plano Free — requer confirmação de e-mail"""
    from flask import render_template, request, flash, redirect, url_for
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        nome = request.form.get('nome', '').strip() or None

        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'danger')
            return redirect(url_for('auth.solicitar_acesso'))
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'danger')
            return redirect(url_for('auth.solicitar_acesso'))

        import secrets as _sec
        token = _sec.token_urlsafe(32)

        new_user = User(
            username=username,
            email=email,
            nome=nome,
            nivel_acesso='free',
            ativo=False,          # inativo até confirmar e-mail
            email_confirmado=False,
            token_confirmacao=token
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        from models import criar_dados_padrao_usuario
        criar_dados_padrao_usuario(new_user)
        db.session.commit()

        # Enviar e-mail de confirmação
        _enviar_email_confirmacao(new_user, token, request.host_url)

        flash('Conta criada! Verifique seu e-mail e clique no link de confirmação para ativar o acesso.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/solicitar_acesso.html')


def _enviar_email_confirmacao(user, token, host_url):
    """Envia e-mail de confirmação de cadastro"""
    try:
        from models import ConfigSistema
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        host     = ConfigSistema.get('smtp_host', '')
        port     = int(ConfigSistema.get('smtp_port', 465) or 465)
        secure   = (ConfigSistema.get('smtp_secure', 'true') or 'true').lower() == 'true'
        smtp_user = ConfigSistema.get('smtp_user', '')
        password = ConfigSistema.get('smtp_password', '')
        from_    = ConfigSistema.get('smtp_from', smtp_user)
        if not host or not smtp_user:
            print('SMTP não configurado — confirmação não enviada')
            return False
        link = f"{host_url.rstrip('/')}/confirmar-email/{token}"
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Confirme seu cadastro — FiNan'
        msg['From'] = from_
        msg['To'] = user.email
        html = f"""
        <div style="font-family:sans-serif;max-width:500px;margin:0 auto;padding:24px;border:1px solid #e2e8f0;border-radius:12px;">
            <h2 style="color:#4361ee;">FiNan — Confirme seu cadastro</h2>
            <p>Olá, <strong>{user.nome or user.username}</strong>!</p>
            <p>Obrigado por se cadastrar. Clique no botão abaixo para confirmar seu e-mail e ativar sua conta:</p>
            <div style="text-align:center;margin:24px 0;">
                <a href="{link}" style="background:#4361ee;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:1rem;">
                    ✅ Confirmar E-mail
                </a>
            </div>
            <p style="color:#64748b;font-size:.85rem;">Se você não solicitou este cadastro, ignore este e-mail.</p>
            <p style="color:#64748b;font-size:.8rem;">Link: <a href="{link}">{link}</a></p>
        </div>"""
        msg.attach(MIMEText(html, 'html'))
        ctx = ssl.create_default_context()
        if secure:
            with smtplib.SMTP_SSL(host, port, context=ctx) as s:
                s.login(smtp_user, password)
                s.sendmail(from_, [user.email], msg.as_string())
        else:
            with smtplib.SMTP(host, port) as s:
                s.ehlo(); s.starttls(context=ctx); s.login(smtp_user, password)
                s.sendmail(from_, [user.email], msg.as_string())
        return True
    except Exception as e:
        print(f'Erro ao enviar e-mail de confirmação: {e}')
        return False


@auth_bp.route('/confirmar-email/<token>')
def confirmar_email(token):
    """Confirma o e-mail e ativa a conta"""
    user = User.query.filter_by(token_confirmacao=token).first()
    if not user:
        flash('Link de confirmação inválido ou já utilizado.', 'danger')
        return redirect(url_for('auth.login'))
    if user.email_confirmado:
        flash('E-mail já confirmado. Faça login.', 'info')
        return redirect(url_for('auth.login'))

    user.email_confirmado = True
    user.ativo = True
    user.token_confirmacao = None
    db.session.commit()
    flash('E-mail confirmado! Sua conta está ativa. Faça login para acessar.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Perfil do usuário"""
    from models import db
    from flask import request, flash, redirect, url_for

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'modo_conta' and current_user.is_promax():
            modo = request.form.get('modo_conta')
            if modo in ('pf', 'pf_pj'):
                current_user.modo_conta = modo
                db.session.commit()
                flash('Configuração de conta atualizada!', 'success')

        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')

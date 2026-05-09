from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from functools import wraps
import os


def _generate_reset_token(email):
    from itsdangerous import URLSafeTimedSerializer
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset')


def _verify_reset_token(token, max_age=3600):
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset', max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None
    return email


def _send_reset_email(to_email, reset_url):
    from models import ConfigSistema
    import smtplib, ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    host     = ConfigSistema.get('smtp_host', '')
    port     = int(ConfigSistema.get('smtp_port', 465) or 465)
    secure   = (ConfigSistema.get('smtp_secure', 'true') or 'true').lower() == 'true'
    user     = ConfigSistema.get('smtp_user', '')
    password = ConfigSistema.get('smtp_password', '')
    from_    = ConfigSistema.get('smtp_from', user)

    if not host or not user:
        raise ValueError('Servidor SMTP não configurado. Solicite ao administrador.')

    html_body = f"""
    <div style="font-family:sans-serif;max-width:500px;margin:auto">
      <h2 style="color:#4361ee">Redefinir Senha</h2>
      <p>Recebemos uma solicitação para redefinir a senha do seu acesso ao
         <strong>Sistema Financeiro</strong>.</p>
      <p style="margin:1.5rem 0">
        <a href="{reset_url}"
           style="background:#4361ee;color:#fff;padding:.75rem 1.5rem;border-radius:8px;
                  text-decoration:none;font-weight:600">
          Redefinir minha senha
        </a>
      </p>
      <p style="color:#64748b;font-size:.85rem">
        Este link expira em 1 hora. Se você não solicitou a redefinição,
        ignore este e-mail.
      </p>
    </div>
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Redefinir Senha — Sistema Financeiro'
    msg['From']    = from_
    msg['To']      = to_email
    msg.attach(MIMEText(html_body, 'html'))

    ctx = ssl.create_default_context()
    if secure:
        with smtplib.SMTP_SSL(host, port, context=ctx) as s:
            s.login(user, password)
            s.sendmail(from_, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(host, port) as s:
            s.ehlo(); s.starttls(context=ctx); s.login(user, password)
            s.sendmail(from_, [to_email], msg.as_string())

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
    """Decorator para requerer nível gerente ou superior"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_gerente():
            flash('Acesso negado. Permissão de gerente necessária.', 'danger')
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
            if not user.ativo:
                flash('Sua conta está inativa. Entre em contato com o administrador.', 'warning')
                return redirect(url_for('auth.login'))

            # Verificar se o acesso está válido
            if not user.esta_valido():
                flash('Seu acesso expirou. Entre em contato com o administrador.', 'danger')
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
@admin_required
def register():
    """Registrar novo usuário (apenas admin)"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        nivel_acesso = request.form.get('nivel_acesso', 'usuario')
        
        # Validações
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Criar novo usuário
        new_user = User(
            username=username,
            email=email,
            nivel_acesso=nivel_acesso,
            ativo=True
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Criar dados padrão para o novo usuário
        from models import criar_dados_padrao_usuario
        criar_dados_padrao_usuario(new_user)

        flash(f'Usuário {username} criado com sucesso com dados padrão!', 'success')
        return redirect(url_for('config.usuarios'))
    
    return render_template('auth/register.html')

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Perfil do usuário"""
    if request.method == 'POST':
        action = request.form.get('action', 'change_password')

        if action == 'update_profile':
            current_user.nome     = request.form.get('nome', '').strip() or None
            current_user.whatsapp = request.form.get('whatsapp', '').strip() or None

            foto_file = request.files.get('foto_perfil')
            if foto_file and foto_file.filename:
                ext = foto_file.filename.rsplit('.', 1)[-1].lower()
                if ext in current_app.config.get('ALLOWED_PHOTO_EXTENSIONS', {'jpg','jpeg','png','webp'}):
                    foto_nome = f"user_{current_user.id}.{ext}"
                    foto_file.save(os.path.join(current_app.config['UPLOAD_PERFIL_FOLDER'], foto_nome))
                    current_user.foto_perfil = foto_nome

            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')

        else:  # change_password
            current_password  = request.form.get('current_password')
            new_password      = request.form.get('new_password')
            confirm_password  = request.form.get('confirm_password')

            if not current_user.check_password(current_password):
                flash('Senha atual incorreta.', 'danger')
            elif new_password != confirm_password:
                flash('As novas senhas não conferem.', 'warning')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Senha alterada com sucesso!', 'success')

    return render_template('auth/profile.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Solicitar redefinição de senha por e-mail"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user  = User.query.filter_by(email=email).first()

        # Sempre exibe a mesma mensagem para não revelar quais e-mails existem
        msg_ok = 'Se este e-mail estiver cadastrado, você receberá as instruções em breve.'

        if user and user.ativo:
            try:
                token     = _generate_reset_token(email)
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                _send_reset_email(email, reset_url)
            except Exception as e:
                flash(f'Erro ao enviar e-mail: {e}', 'danger')
                return render_template('auth/forgot_password.html')

        flash(msg_ok, 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Redefinir senha via token do e-mail"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    email = _verify_reset_token(token)
    if not email:
        flash('Link inválido ou expirado. Solicite um novo.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password     = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(new_password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'warning')
        elif new_password != confirm_password:
            flash('As senhas não conferem.', 'warning')
        else:
            user.set_password(new_password)
            db.session.commit()
            flash('Senha redefinida com sucesso! Faça login.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)

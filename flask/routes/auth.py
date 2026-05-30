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
    """Auto-cadastro para plano Free"""
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

        new_user = User(
            username=username,
            email=email,
            nome=nome,
            nivel_acesso='free',
            ativo=True,
            email_confirmado=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        from models import criar_dados_padrao_usuario
        criar_dados_padrao_usuario(new_user)
        db.session.commit()

        flash('Conta criada com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/solicitar_acesso.html')

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

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from functools import wraps
import os
import re as _re


def _limpar_cpf(cpf):
    """Remove máscara e retorna 11 dígitos ou None."""
    return _re.sub(r'\D', '', cpf or '')[:11] or None


def _validar_cpf(cpf):
    """Valida CPF (11 dígitos limpos). Retorna True se válido."""
    cpf = _re.sub(r'\D', '', cpf or '')
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(2):
        soma = sum(int(cpf[j]) * (10 + i - j) for j in range(9 + i))
        d = 11 - (soma % 11)
        if d >= 10:
            d = 0
        if int(cpf[9 + i]) != d:
            return False
    return True


def _importar_planilha_dados_usuario(usuario, arquivo):
    """
    Importa dados de um usuário a partir da planilha Excel gerada por
    config.exportar_dados_usuario (uma aba por tipo de dado).
    Cria categorias/meios citados que ainda não existirem e recria os
    lançamentos (despesas, receitas, orçamentos, balanços, eventos de caixa).
    Retorna (sucesso: bool, mensagem: str).
    """
    import pandas as pd
    from datetime import datetime as _dt
    from models import (CategoriaDespesa, CategoriaReceita, MeioPagamento,
                        MeioRecebimento, Despesa, Receita, Orcamento,
                        BalancoMensal, EventoCaixaAvulso)

    try:
        planilhas = pd.read_excel(arquivo, sheet_name=None, engine='openpyxl')
    except Exception as e:
        return False, f'Não foi possível ler o arquivo: {e}'

    def _obter_categoria_despesa(nome):
        if not nome or (isinstance(nome, float) and pd.isna(nome)):
            return None
        cat = CategoriaDespesa.query.filter_by(user_id=usuario.id, nome=nome).first()
        if not cat:
            cat = CategoriaDespesa(nome=nome, ativo=True, user_id=usuario.id)
            db.session.add(cat)
            db.session.flush()
        return cat

    def _obter_categoria_receita(nome):
        if not nome or (isinstance(nome, float) and pd.isna(nome)):
            return None
        cat = CategoriaReceita.query.filter_by(user_id=usuario.id, nome=nome).first()
        if not cat:
            cat = CategoriaReceita(nome=nome, ativo=True, user_id=usuario.id)
            db.session.add(cat)
            db.session.flush()
        return cat

    def _obter_meio_pagamento(nome, tipo=None):
        if not nome or (isinstance(nome, float) and pd.isna(nome)):
            return None
        meio = MeioPagamento.query.filter_by(user_id=usuario.id, nome=nome).first()
        if not meio:
            meio = MeioPagamento(nome=nome, tipo=tipo or 'outro', ativo=True, user_id=usuario.id)
            db.session.add(meio)
            db.session.flush()
        return meio

    def _obter_meio_recebimento(nome):
        if not nome or (isinstance(nome, float) and pd.isna(nome)):
            return None
        meio = MeioRecebimento.query.filter_by(user_id=usuario.id, nome=nome).first()
        if not meio:
            meio = MeioRecebimento(nome=nome, ativo=True, user_id=usuario.id)
            db.session.add(meio)
            db.session.flush()
        return meio

    def _data(valor):
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return None
        if isinstance(valor, str):
            try:
                return _dt.strptime(valor, '%d/%m/%Y').date()
            except ValueError:
                return None
        if hasattr(valor, 'date'):
            return valor.date()
        return None

    contadores = {'despesas': 0, 'receitas': 0, 'orcamentos': 0, 'balancos': 0, 'eventos': 0}

    df_desp = planilhas.get('Despesas')
    if df_desp is not None:
        for _, row in df_desp.iterrows():
            categoria = _obter_categoria_despesa(row.get('Categoria'))
            meio = _obter_meio_pagamento(row.get('Meio de Pagamento'), tipo='cartao')
            data_pag = _data(row.get('Data'))
            if not (categoria and meio and data_pag):
                continue
            db.session.add(Despesa(
                descricao=str(row.get('Descrição') or ''),
                valor=float(row.get('Valor') or 0),
                num_parcelas=int(row.get('Parcelas') or 1),
                data_pagamento=data_pag,
                user_id=usuario.id,
                categoria_id=categoria.id,
                meio_pagamento_id=meio.id,
            ))
            contadores['despesas'] += 1

    df_rec = planilhas.get('Receitas')
    if df_rec is not None:
        for _, row in df_rec.iterrows():
            categoria = _obter_categoria_receita(row.get('Categoria'))
            meio = _obter_meio_recebimento(row.get('Meio de Recebimento'))
            data_rec = _data(row.get('Data'))
            if not (categoria and meio and data_rec):
                continue
            db.session.add(Receita(
                descricao=str(row.get('Descrição') or ''),
                valor=float(row.get('Valor') or 0),
                num_parcelas=int(row.get('Parcelas') or 1),
                data_recebimento=data_rec,
                user_id=usuario.id,
                categoria_id=categoria.id,
                meio_recebimento_id=meio.id,
            ))
            contadores['receitas'] += 1

    df_orc = planilhas.get('Orçamentos')
    if df_orc is not None:
        for _, row in df_orc.iterrows():
            categoria = _obter_categoria_despesa(row.get('Categoria'))
            if not categoria:
                continue
            if Orcamento.query.filter_by(user_id=usuario.id, categoria_id=categoria.id).first():
                continue
            db.session.add(Orcamento(
                valor_orcado=float(row.get('Valor Orçado') or 0),
                categoria_id=categoria.id,
                user_id=usuario.id,
            ))
            contadores['orcamentos'] += 1

    df_bal = planilhas.get('Balanço Mensal')
    if df_bal is not None:
        for _, row in df_bal.iterrows():
            mes = row.get('Mês')
            ano = row.get('Ano')
            if pd.isna(mes) or pd.isna(ano):
                continue
            mes, ano = int(mes), int(ano)
            if BalancoMensal.query.filter_by(user_id=usuario.id, mes=mes, ano=ano).first():
                continue
            db.session.add(BalancoMensal(
                mes=mes, ano=ano,
                total_entradas=float(row.get('Total Entradas') or 0),
                total_saidas=float(row.get('Total Saídas') or 0),
                saldo_mes=float(row.get('Saldo') or 0),
                user_id=usuario.id,
            ))
            contadores['balancos'] += 1

    df_evt = planilhas.get('Eventos de Caixa')
    if df_evt is not None:
        for _, row in df_evt.iterrows():
            data_evt = _data(row.get('Data'))
            if not data_evt:
                continue
            db.session.add(EventoCaixaAvulso(
                data=data_evt,
                descricao=str(row.get('Descrição') or ''),
                valor=float(row.get('Valor') or 0),
                user_id=usuario.id,
            ))
            contadores['eventos'] += 1

    db.session.commit()

    resumo = ', '.join(f'{v} {k}' for k, v in contadores.items() if v > 0)
    return True, (f'Dados importados com sucesso! ({resumo})' if resumo
                  else 'Arquivo lido, mas nenhum registro pôde ser importado.')


def _gerar_token_confirmacao(email):
    from itsdangerous import URLSafeTimedSerializer
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='email-confirm')


def _verificar_token_confirmacao(token, max_age=86400):  # 24h
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return s.loads(token, salt='email-confirm', max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None


def _enviar_email_confirmacao(to_email, confirm_url):
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
        raise ValueError('Servidor SMTP não configurado.')

    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:auto">
      <h2 style="color:#4361ee">Confirme seu e-mail — FiNan</h2>
      <p>Recebemos uma solicitação de acesso <strong>Free</strong> ao sistema FiNan.</p>
      <p>Clique no botão abaixo para confirmar seu e-mail e ativar sua conta:</p>
      <p style="margin:1.5rem 0">
        <a href="{confirm_url}"
           style="background:#4361ee;color:#fff;padding:.75rem 1.5rem;border-radius:8px;
                  text-decoration:none;font-weight:600">
          Confirmar e-mail e ativar conta
        </a>
      </p>
      <p style="color:#64748b;font-size:.85rem">
        Este link expira em 24 horas. Se você não solicitou acesso, ignore este e-mail.
      </p>
    </div>
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Confirme seu e-mail — FiNan'
    msg['From']    = from_
    msg['To']      = to_email
    msg.attach(MIMEText(html, 'html'))

    ctx = ssl.create_default_context()
    if secure:
        with smtplib.SMTP_SSL(host, port, context=ctx) as s:
            s.login(user, password)
            s.sendmail(from_, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(host, port) as s:
            s.ehlo(); s.starttls(context=ctx); s.login(user, password)
            s.sendmail(from_, [to_email], msg.as_string())


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

def supabase_required(f):
    """Decorator: admin ou pro com allow_supabase"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not (current_user.is_admin() or (current_user.is_pro() and current_user.allow_supabase)):
            flash('Acesso negado. Permissão de Supabase não habilitada para seu usuário.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def nao_free_required(f):
    """Decorator: bloqueia apenas usuários free"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.is_free():
            flash('Esta funcionalidade não está disponível no plano Free. Faça upgrade para acessar.', 'warning')
            return redirect(url_for('assinatura.minha_assinatura'))
        return f(*args, **kwargs)
    return decorated_function

def openfinance_required(f):
    """Decorator: admin ou pro com allow_openfinance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not (current_user.is_admin() or (current_user.is_pro() and current_user.allow_openfinance)):
            flash('Acesso negado. Permissão de OpenFinance não habilitada para seu usuário.', 'danger')
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
        
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
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


@auth_bp.route('/check-username')
def check_username():
    """Verifica disponibilidade de username (AJAX, público)."""
    from flask import jsonify
    u = request.args.get('u', '').strip()
    disponivel = bool(u) and not User.query.filter_by(username=u).first()
    return jsonify({'disponivel': disponivel})


@auth_bp.route('/solicitar-acesso', methods=['GET', 'POST'])
def solicitar_acesso():
    """Auto-cadastro para plano Free com validação de e-mail."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome     = request.form.get('nome', '').strip()
        cpf_raw  = _limpar_cpf(request.form.get('cpf', ''))
        email    = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        senha    = request.form.get('password', '')
        senha2   = request.form.get('password2', '')

        # Validações
        if not nome:
            flash('Nome completo é obrigatório.', 'danger')
            return render_template('auth/solicitar_acesso.html')
        if not cpf_raw or len(cpf_raw) != 11:
            flash('CPF inválido.', 'danger')
            return render_template('auth/solicitar_acesso.html')
        if not _validar_cpf(cpf_raw):
            flash('CPF inválido — verifique os dígitos.', 'danger')
            return render_template('auth/solicitar_acesso.html')
        if senha != senha2:
            flash('As senhas não conferem.', 'danger')
            return render_template('auth/solicitar_acesso.html')
        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('auth/solicitar_acesso.html')
        if User.query.filter_by(cpf=cpf_raw).first():
            flash('Já existe uma conta cadastrada com este CPF.', 'danger')
            return render_template('auth/solicitar_acesso.html')
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado. Use "Esqueceu a senha?" se precisar de acesso.', 'warning')
            return redirect(url_for('auth.login'))
        if User.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso. Escolha outro.', 'warning')
            return render_template('auth/solicitar_acesso.html')

        # Criar usuário inativo, aguardando confirmação
        token = _gerar_token_confirmacao(email)
        novo = User(
            nome=nome,
            cpf=cpf_raw,
            email=email,
            username=username,
            nivel_acesso='free',
            ativo=False,
            email_confirmado=False,
            token_confirmacao=token,
        )
        novo.set_password(senha)
        db.session.add(novo)
        db.session.commit()

        # Criar categorias/meios padrão
        from models import criar_dados_padrao_usuario
        criar_dados_padrao_usuario(novo)

        # Importar dados de planilha de backup (opcional — usuário que já teve conta)
        planilha = request.files.get('planilha_dados')
        if planilha and planilha.filename:
            if planilha.filename.lower().endswith('.xlsx'):
                ok, msg = _importar_planilha_dados_usuario(novo, planilha)
                flash(msg, 'success' if ok else 'warning')
            else:
                flash('Planilha ignorada: envie um arquivo .xlsx exportado pelo FiNan.', 'warning')

        # Enviar e-mail de confirmação
        try:
            confirm_url = url_for('auth.confirmar_email', token=token, _external=True)
            _enviar_email_confirmacao(email, confirm_url)
            flash('Cadastro realizado! Verifique seu e-mail para confirmar e ativar sua conta.', 'success')
        except Exception as e:
            flash(f'Cadastro criado mas não foi possível enviar o e-mail: {e}. '
                  f'Entre em contato com o administrador.', 'warning')

        return redirect(url_for('auth.login'))

    from models import ConfigSistema
    limite_free = int(ConfigSistema.get('limite_registros_free', '500') or 500)
    return render_template('auth/solicitar_acesso.html', limite_free=limite_free)


@auth_bp.route('/confirmar-email/<token>')
def confirmar_email(token):
    """Ativa conta após clique no link de confirmação."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    email = _verificar_token_confirmacao(token)
    if not email:
        return render_template('auth/confirmar_email.html',
                               status='expirado',
                               msg='Link expirado ou inválido. Solicite um novo acesso.')

    user = User.query.filter_by(email=email, token_confirmacao=token).first()
    if not user:
        return render_template('auth/confirmar_email.html',
                               status='erro',
                               msg='Usuário não encontrado.')

    if user.email_confirmado:
        return render_template('auth/confirmar_email.html',
                               status='ja_confirmado',
                               msg='E-mail já confirmado anteriormente. Faça login.')

    user.email_confirmado = True
    user.ativo = True
    user.token_confirmacao = None
    db.session.commit()

    return render_template('auth/confirmar_email.html',
                           status='sucesso',
                           msg='E-mail confirmado! Sua conta está ativa. Faça login.')

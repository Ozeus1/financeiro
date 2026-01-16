from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modelo de usuário com autenticação"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nivel_acesso = db.Column(db.String(20), nullable=False, default='usuario')  # admin, usuario
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_validade = db.Column(db.Date, nullable=True)  # Data de validade do acesso (apenas para usuários normais)
    
    # Relacionamentos
    despesas = db.relationship('Despesa', backref='usuario', lazy=True, cascade='all, delete-orphan')
    receitas = db.relationship('Receita', backref='usuario', lazy=True, cascade='all, delete-orphan')
    balancos_mensais = db.relationship('BalancoMensal', backref='usuario', lazy=True, cascade='all, delete-orphan')
    eventos_caixa = db.relationship('EventoCaixaAvulso', backref='usuario', lazy=True, cascade='all, delete-orphan')
    orcamentos = db.relationship('Orcamento', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Gera hash da senha"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verifica se o usuário é administrador"""
        return self.nivel_acesso == 'admin'
    
    def is_gerente(self):
        """Verifica se o usuário é gerente ou superior"""
        return self.nivel_acesso in ['admin', 'gerente']

    def esta_valido(self):
        """Verifica se o acesso do usuário ainda está válido"""
        # Admin não tem data de validade
        if self.is_admin():
            return True
        # Se não tem data de validade definida, está válido
        if not self.data_validade:
            return True
        # Verifica se ainda não expirou
        from datetime import date
        return date.today() <= self.data_validade

    def dias_restantes(self):
        """Retorna quantos dias restam até expirar (None se sem validade ou admin)"""
        if self.is_admin() or not self.data_validade:
            return None
        from datetime import date
        delta = self.data_validade - date.today()
        return delta.days

    def __repr__(self):
        return f'<User {self.username}>'


class CategoriaDespesa(db.Model):
    """Categorias de despesas (configurável por usuário)"""
    __tablename__ = 'categorias_despesa'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relacionamentos
    usuario = db.relationship('User', backref='categorias_despesa')
    despesas = db.relationship('Despesa', backref='categoria', lazy=True)
    orcamentos = db.relationship('Orcamento', backref='categoria', lazy=True)

    # Constraint único por usuário
    __table_args__ = (db.UniqueConstraint('nome', 'user_id', name='_categoria_despesa_usuario_uc'),)

    def __repr__(self):
        return f'<CategoriaDespesa {self.nome} (User: {self.user_id})>'


class CategoriaReceita(db.Model):
    """Categorias de receitas (configurável por usuário)"""
    __tablename__ = 'categorias_receita'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relacionamentos
    usuario = db.relationship('User', backref='categorias_receita')
    receitas = db.relationship('Receita', backref='categoria', lazy=True)

    # Constraint único por usuário
    __table_args__ = (db.UniqueConstraint('nome', 'user_id', name='_categoria_receita_usuario_uc'),)

    def __repr__(self):
        return f'<CategoriaReceita {self.nome} (User: {self.user_id})>'


class MeioPagamento(db.Model):
    """Meios de pagamento (configurável por usuário)"""
    __tablename__ = 'meios_pagamento'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))  # cartao, transferencia, dinheiro, pix, boleto
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relacionamentos
    usuario = db.relationship('User', backref='meios_pagamento')
    despesas = db.relationship('Despesa', backref='meio_pagamento', lazy=True)
    fechamentos_cartao = db.relationship('FechamentoCartao', backref='meio_pagamento', lazy=True)

    # Constraint único por usuário
    __table_args__ = (db.UniqueConstraint('nome', 'user_id', name='_meio_pagamento_usuario_uc'),)

    def __repr__(self):
        return f'<MeioPagamento {self.nome} (User: {self.user_id})>'


class MeioRecebimento(db.Model):
    """Meios de recebimento (configurável por usuário)"""
    __tablename__ = 'meios_recebimento'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relacionamentos
    usuario = db.relationship('User', backref='meios_recebimento')
    receitas = db.relationship('Receita', backref='meio_recebimento', lazy=True)

    # Constraint único por usuário
    __table_args__ = (db.UniqueConstraint('nome', 'user_id', name='_meio_recebimento_usuario_uc'),)

    def __repr__(self):
        return f'<MeioRecebimento {self.nome} (User: {self.user_id})>'


class Despesa(db.Model):
    """Tabela de despesas"""
    __tablename__ = 'despesas'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    num_parcelas = db.Column(db.Integer, default=1)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    data_pagamento = db.Column(db.Date, nullable=False)
    
    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_despesa.id'), nullable=False)
    meio_pagamento_id = db.Column(db.Integer, db.ForeignKey('meios_pagamento.id'), nullable=False)
    
    def __repr__(self):
        return f'<Despesa {self.descricao} - R$ {self.valor}>'


class Receita(db.Model):
    """Tabela de receitas"""
    __tablename__ = 'receitas'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    num_parcelas = db.Column(db.Integer, default=1)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    data_recebimento = db.Column(db.Date, nullable=False)
    
    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_receita.id'), nullable=False)
    meio_recebimento_id = db.Column(db.Integer, db.ForeignKey('meios_recebimento.id'), nullable=False)
    
    def __repr__(self):
        return f'<Receita {self.descricao} - R$ {self.valor}>'


class Orcamento(db.Model):
    """Orçamento geral por categoria (valor único, não mensal)"""
    __tablename__ = 'orcamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    valor_orcado = db.Column(db.Float, nullable=False)
    
    # Chaves estrangeiras
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_despesa.id'), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Orcamento {self.categoria.nome if self.categoria else "?"} - R$ {self.valor_orcado}>'


class FechamentoCartao(db.Model):
    """Datas de fechamento de cartões de crédito"""
    __tablename__ = 'fechamentos_cartao'
    
    id = db.Column(db.Integer, primary_key=True)
    dia_fechamento = db.Column(db.Integer, nullable=False)  # 1-31
    dia_vencimento = db.Column(db.Integer, nullable=False)  # 1-31
    
    # Chaves estrangeiras
    meio_pagamento_id = db.Column(db.Integer, db.ForeignKey('meios_pagamento.id'), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<FechamentoCartao dia {self.dia_fechamento}>'


class BalancoMensal(db.Model):
    """Balanço mensal consolidado do fluxo de caixa"""
    __tablename__ = 'balanco_mensal'
    
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer, nullable=False)
    mes = db.Column(db.Integer, nullable=False)  # 1-12
    total_entradas = db.Column(db.Float, default=0.0, nullable=False)
    total_saidas = db.Column(db.Float, default=0.0, nullable=False)
    saldo_mes = db.Column(db.Float, default=0.0, nullable=False)
    observacoes = db.Column(db.Text)
    
    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Garantir unicidade por usuário/ano/mês
    __table_args__ = (
        db.UniqueConstraint('user_id', 'ano', 'mes', name='_user_ano_mes_uc'),
    )
    
    def __repr__(self):
        return f'<BalancoMensal {self.mes}/{self.ano} - R$ {self.saldo_mes}>'


class EventoCaixaAvulso(db.Model):
    """Eventos de caixa avulsos (ex: pagamentos de faturas de cartão)"""
    __tablename__ = 'eventos_caixa_avulsos'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    
    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<EventoCaixaAvulso {self.descricao} - R$ {self.valor}>'


class Configuracao(db.Model):
    """Tabela para armazenar configurações do sistema (chave-valor)"""
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Configuracao {self.chave}>'


def init_db(app):
    """Inicializa a extensão do banco de dados"""
    db.init_app(app)

def criar_dados_padrao_usuario(user):
    """Cria categorias e meios de pagamento padrão para um novo usuário"""
    # Categorias de despesa padrão
    categorias_despesa_padrao = [
        'Moradia', 'Contas da casa', 'Alimentação', 'Transporte', 'Saúde',
        'Educação', 'Vestuário', 'Lazer', 'Assinaturas', 'Pets', 'Trabalho',
        'Impostos', 'Dívidas', 'Tarifas bancárias', 'Emergências', 'Outros'
    ]
    for nome in categorias_despesa_padrao:
        if not CategoriaDespesa.query.filter_by(nome=nome, user_id=user.id).first():
            categoria = CategoriaDespesa(nome=nome, ativo=True, user_id=user.id)
            db.session.add(categoria)

    # Categorias de receita padrão
    categorias_receita_padrao = [
        'Salário', 'Pró-labore', 'Aposentadoria', 'Pensão', 'Aluguel recebido',
        'Rendimentos financeiros', 'Comissões', 'Serviços prestados', 'Vendas',
        'Reembolsos', 'Outros'
    ]
    for nome in categorias_receita_padrao:
        if not CategoriaReceita.query.filter_by(nome=nome, user_id=user.id).first():
            categoria = CategoriaReceita(nome=nome, ativo=True, user_id=user.id)
            db.session.add(categoria)

    # Meios de pagamento padrão
    meios_pagamento_padrao = [
        ('Dinheiro', 'dinheiro'),
        ('PIX', 'pix'),
        ('Débito', 'debito'),
        ('Crédito à vista', 'cartao'),
        ('Crédito parcelado', 'cartao'),
        ('Boleto', 'boleto'),
        ('Débito automático', 'debito'),
        ('Transferência bancária', 'transferencia'),
        ('Carteira digital', 'outros'),
        # Especificados pelo usuário, mas mantendo o tipo genérico
        ('Cartão BB', 'cartao'),
        ('Cartão Nubank', 'cartao')
    ]
    for nome, tipo in meios_pagamento_padrao:
        if not MeioPagamento.query.filter_by(nome=nome, user_id=user.id).first():
            meio = MeioPagamento(nome=nome, tipo=tipo, ativo=True, user_id=user.id)
            db.session.add(meio)

    # Meios de recebimento padrão
    meios_recebimento_padrao = [
        'Dinheiro', 'PIX', 'Crédito à vista', 'Crédito parcelado',
        'Transferência bancária', 'Boleto recebido', 'Carteira digital',
        'Depósito bancário',
        # Especificados pelo usuário
        'Cartão BB', 'Cartão Nubank'
    ]
    for nome in meios_recebimento_padrao:
        if not MeioRecebimento.query.filter_by(nome=nome, user_id=user.id).first():
            meio = MeioRecebimento(nome=nome, ativo=True, user_id=user.id)
            db.session.add(meio)

    db.session.commit()


def populate_db(app):
    """Cria tabelas e popula com dados padrão"""
    with app.app_context():
        db.create_all()

        # Criar usuário admin padrão se não existir
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@financeiro.com',
                nivel_acesso='admin',
                ativo=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

            # Criar dados padrão para o admin
            criar_dados_padrao_usuario(admin)

        db.session.commit()
        print("Banco de dados populado com sucesso!")

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

TZ_RECIFE = pytz.timezone('America/Recife')
# datetime.now(TZ_RECIFE)

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'tb_usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    e_administrador = db.Column(db.Boolean, default=False)
    
    def __init__(self, email, password, e_administrador):
        self.email = email
        self.set_password(password)
        self.e_administrador = e_administrador
        
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<Usuario {self.email}>'
    

class Cliente(db.Model):
    __tablename__ = 'tb_clientes'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Cliente {self.email}>'

class Livro(db.Model):
    __tablename__ = 'tb_livro'
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(150), nullable=False)
    genero_id = db.Column(db.Integer, db.ForeignKey('tb_genero.id'), nullable=False)
    qtd_disponivel = db.Column(db.Integer, nullable=False)
    qtd_total = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Livro {self.titulo}>'

class Genero(db.Model):
    __tablename__ = 'tb_genero'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    livros = db.relationship('Livro', backref='genero', lazy=True)

    def __repr__(self):
        return f'<Genero {self.nome}>'

class Emprestimo(db.Model):
    __tablename__ = 'tb_emprestimos'
    id = db.Column(db.Integer, primary_key=True)
    id_livro = db.Column(db.Integer, db.ForeignKey('tb_livro.id'), nullable=False)
    id_cliente = db.Column(db.Integer, db.ForeignKey('tb_clientes.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('tb_usuarios.id'), nullable=False)
    data_emprestimo = db.Column(db.DateTime, default=datetime.now(TZ_RECIFE), nullable=False)
    data_devolucao = db.Column(db.DateTime, nullable=True)

    livro = db.relationship('Livro', backref='emprestimos', lazy=True)
    cliente = db.relationship('Cliente', backref='emprestimos', lazy=True)
    usuario = db.relationship('Usuario', backref='emprestimos', lazy=True)

    def __repr__(self):
        return f'<Emprestimo LivroID={self.id_livro} ClienteID={self.id_cliente}>'

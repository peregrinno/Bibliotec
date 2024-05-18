from flask import Flask, jsonify, render_template, make_response, redirect, url_for, request, flash
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from flask_paginate import Pagination
from config import Config
from models import db
from functools import wraps
from sqlalchemy import desc, func
from datetime import date
from dotenv import load_dotenv
import subprocess
import os

from models import *

# Cria instancia de aplicativo Flask
app = Flask(__name__)

# Define uma nova secret key para o aplicativo
app.secret_key = os.environ.get('SECRET_APP_KEY', 'fn@gs#g8w4r_htgi!jsf')

# Define as configuração do app a partir de um class externa chamada 'Config', consultar arquivo config.py
app.config.from_object(Config)

# Inicia aplicativo encapsulado pelo objeto banco que vem da class externa 'Models', consultar arquivo models.py
db.init_app(app)

# Encapsula o aplicativo na classe CORS para controle de origem de requisições
CORS(app) 

# Cria objeto migrate para caso de mudanças no banco de dados, essas mudanças serem aplicadas
migrate = Migrate(app, db)

# Função interna para realizar o DUMP no banco de dados ou Aplicar mudanças 
def dump_database():
    # Executa flask db init
    subprocess.run(['flask', 'db', 'init']) # > flask db init

    # Executa flask db migrate
    subprocess.run(['flask', 'db', 'migrate']) # > flask db migrate

    # Executa flask db upgrade
    subprocess.run(['flask', 'db', 'upgrade']) # > flask db upgrade

    # ORM - Objeto Gerencial de relacionamento de banco de dados
    existing_user = Usuario.query.filter_by(email='admin@example.com').first()
    # Se isso aqui, não existir, ele entra na condicional abaixo
    
    
    if not existing_user:
        # Se o usuário não existir, cria um novo usuário padrão
        default_user = Usuario(
            email='admin@example.com',
            password='admin123',
            e_administrador=True
        )
        
        # Essa linha, substitui o INSERT INTO 'tb_usuarios' (email, password, e_administrador) VALUES ('','',bool)
        db.session.add(default_user)
        
        # Confirmação da transação
        db.session.commit()

# Função que contextualiza a dump_database
def run_migrations():
    with app.app_context():
        # Executa as migrações antes de iniciar o aplicativo
        dump_database()

#Função para gerar breadcrumbs
def generate_breadcrumbs(crumbs):
    """
    Gera a estrutura de breadcrumbs para ser renderizada no template.

    :param crumbs: Lista de dicionários com 'title' e 'url'.
    :return: Lista de breadcrumbs.
    """
    return crumbs




# Decorator para bloquear rotas da aplicação que necessitem de autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.cookies.get('user_id')
        user_email = request.cookies.get('user_email')

        if user_id and user_email:
            user = Usuario.query.filter_by(id=user_id, email=user_email).first()
            if user:
                # Adiciona o usuário à requisição para ser acessado nas rotas protegidas
                request.user = user
                return f(*args, **kwargs)

        # Redireciona para a página de login se o usuário não estiver autenticado
        return redirect(url_for('login'))

    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_password(password) :
            flash('Login bem-sucedido!', 'success')
            
            # Cria uma resposta personalizada
            response = make_response(redirect(url_for('index')))
            
            # Define cookies
            response.set_cookie('user_id', str(usuario.id))
            response.set_cookie('user_email', usuario.email)
            
            return response
        else:
            flash('Usuário ou(e) senha inválido(s)!', 'danger')
            return render_template('login.html')
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Limpa os cookies de autenticação e redireciona para a página de login
    response = make_response(redirect(url_for('login')))
    response.set_cookie('user_id', '', expires=0)
    response.set_cookie('user_email', '', expires=0)
    return response

@app.route('/index', methods=['GET'])
@login_required
def index():
    breadcrumbs = generate_breadcrumbs([{'title': 'Inicio', 'url': url_for('index')}])
    return render_template('index.html', breadcrumbs=breadcrumbs)

# Rotas de cliente
@app.route('/clientes', methods=['GET', 'POST'])
@login_required
def clientes():       
    if request.method == 'POST':
        cliente_id = request.form.get('id')
        email = request.form.get('email')
        endereco = request.form.get('endereco')
        telefone = request.form.get('telefone')

        if not email or not endereco or not telefone:
            flash('Todos os campos são obrigatórios!', 'danger')
            return redirect(url_for('index'))

        if cliente_id:
            cliente = Cliente.query.get(cliente_id)
            if cliente:
                cliente.email = email
                cliente.endereco = endereco
                cliente.telefone = telefone
                db.session.commit()
                flash('Cliente atualizado com sucesso!', 'success')
        else:
            novo_cliente = Cliente(email=email, endereco=endereco, telefone=telefone)
            db.session.add(novo_cliente)
            db.session.commit()
            flash('Cliente adicionado com sucesso!', 'success')
    
    # Busca
    search_query = request.args.get('search')
    if search_query:
        search = "%{}%".format(search_query)
        clientes = Cliente.query.filter(
            (Cliente.email.ilike(search)) | 
            (Cliente.telefone.ilike(search))
        ).all()
    else:
        clientes = Cliente.query.all()
    
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Clientes', 'url': url_for('clientes')},
    ])
    
    context = {
        'clientes': clientes,
        'search_query': search_query if search_query else ''
    }
    
    return render_template('clientes/clientes.html', context=context, breadcrumbs=breadcrumbs)


@app.route('/excluir_cliente', methods=['POST'])
@login_required
def excluir_cliente():
    cliente_id = request.form.get('id')
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    else:
        flash('Cliente não encontrado!', 'danger')
    
    return redirect(url_for('clientes'))


if __name__ == '__main__':
    #run_migrations()
    
    app.run(debug=True, port=8083)
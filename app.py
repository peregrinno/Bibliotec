from flask import Flask, jsonify, render_template, make_response, redirect, url_for, request, flash
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from flask_paginate import Pagination
from sqlalchemy import desc
from config import Config
from models import db
from functools import wraps
from datetime import date
import subprocess
import os
import pytz

TZ_RECIFE = pytz.timezone('America/Recife')
# datetime.now(TZ_RECIFE)

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

@app.route('/livros', methods=['GET', 'POST'])
@login_required
def livros():
    if request.method == 'POST':
        livro_id = request.form.get('id')
        isbn = request.form.get('isbn')
        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        genero_id = request.form.get('genero_id')
        qtd_disponivel = request.form.get('qtd_disponivel')
        qtd_total = request.form.get('qtd_total')

        if not isbn or not titulo or not autor or not genero_id or not qtd_disponivel or not qtd_total:
            flash('Todos os campos são obrigatórios!', 'danger')
            return redirect(url_for('livros'))

        if livro_id:
            livro = Livro.query.get(livro_id)
            if livro:
                livro.isbn = isbn
                livro.titulo = titulo
                livro.autor = autor
                livro.genero_id = genero_id
                livro.qtd_disponivel = qtd_disponivel
                livro.qtd_total = qtd_total
                db.session.commit()
                flash('Livro atualizado com sucesso!', 'success')
        else:
            novo_livro = Livro(isbn=isbn, titulo=titulo, autor=autor, genero_id=genero_id, qtd_disponivel=qtd_disponivel, qtd_total=qtd_total)
            db.session.add(novo_livro)
            db.session.commit()
            flash('Livro adicionado com sucesso!', 'success')

    # Busca
    search_query = request.args.get('search')
    if search_query:
        search = "%{}%".format(search_query)
        livros = Livro.query.filter(
            (Livro.titulo.ilike(search)) | 
            (Livro.autor.ilike(search)) | 
            (Livro.isbn.ilike(search))
        ).all()
    else:
        livros = Livro.query.all()

    generos = Genero.query.all()  # Carrega todos os gêneros
    
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Livros', 'url': url_for('livros')},
    ])

    context = {
        'livros': livros,
        'generos': generos,
        'search_query': search_query if search_query else ''
    }

    return render_template('livros/livros.html', context=context, breadcrumbs=breadcrumbs)

@app.route('/deletar_livro', methods=['POST'])
@login_required
def deletar_livro():
    livro_id = request.form.get('id')
    livro = Livro.query.get(livro_id)
    if livro:
        db.session.delete(livro)
        db.session.commit()
        flash('Livro deletado com sucesso!', 'success')
    else:
        flash('Livro não encontrado!', 'danger')
    return redirect(url_for('livros'))

@app.route('/adicionar_genero', methods=['POST'])
@login_required
def adicionar_genero():
    nome = request.form.get('nome')
    if not nome:
        flash('Nome do gênero é obrigatório!', 'danger')
        return redirect(url_for('livros'))
    
    novo_genero = Genero(nome=nome)
    db.session.add(novo_genero)
    db.session.commit()
    flash('Gênero adicionado com sucesso!', 'success')
    return redirect(url_for('livros'))

@app.route('/emprestimos', methods=['GET', 'POST'])
@login_required
def emprestimos():
    if request.method == 'POST':
        id_livro = request.form.get('id_livro')
        id_cliente = request.form.get('id_cliente')
        id_usuario = request.cookies.get('user_id')

        livro = Livro.query.get(id_livro)
        cliente = Cliente.query.get(id_cliente)

        # Verificar se o livro está disponível
        if livro.qtd_disponivel <= 0:
            flash('Livro sem estoque disponível.', 'danger')
            return redirect(url_for('emprestimos'))

        # Verificar se o cliente já tem 3 livros emprestados
        emprestimos_cliente = Emprestimo.query.filter_by(id_cliente=id_cliente, data_devolucao=None).count()
        if emprestimos_cliente >= 3:
            flash('Cliente já tem 3 livros emprestados.', 'danger')
            return redirect(url_for('emprestimos'))

        # Criar novo empréstimo
        novo_emprestimo = Emprestimo(id_livro=id_livro, id_cliente=id_cliente, id_usuario=id_usuario)
        db.session.add(novo_emprestimo)

        # Atualizar a quantidade disponível do livro
        livro.qtd_disponivel -= 1

        db.session.commit()
        flash('Empréstimo realizado com sucesso!', 'success')

    # Carregar todos os empréstimos
    emprestimos = Emprestimo.query.order_by(desc(Emprestimo.data_emprestimo)).all()
    livros = Livro.query.filter(Livro.qtd_disponivel > 0).all()
    clientes = Cliente.query.all()
    
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Emprestimos', 'url': url_for('emprestimos')},
    ])

    context = {
        'emprestimos': emprestimos,
        'livros': livros,
        'clientes': clientes,
    }

    return render_template('emprestimos/emprestimos.html', context=context, breadcrumbs=breadcrumbs)

@app.route('/devolucao', methods=['POST'])
@login_required
def devolucao():
    id_emprestimo = request.form.get('id_emprestimo')

    emprestimo = Emprestimo.query.get(id_emprestimo)
    if emprestimo and not emprestimo.data_devolucao:
        # Registrar a data de devolução
        emprestimo.data_devolucao = datetime.now(TZ_RECIFE)

        # Atualizar a quantidade disponível do livro
        livro = Livro.query.get(emprestimo.id_livro)
        livro.qtd_disponivel += 1

        db.session.commit()
        flash('Devolução realizada com sucesso!', 'success')
    else:
        flash('Empréstimo não encontrado ou já devolvido.', 'danger')

    return redirect(url_for('emprestimos'))


if __name__ == '__main__':
    #run_migrations()
    
    app.run(debug=True, port=8083)
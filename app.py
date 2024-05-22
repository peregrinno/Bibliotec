from flask import Flask, jsonify, render_template, make_response, redirect, url_for, request, flash
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import desc, func
from config import Config
from models import db
from functools import wraps
from datetime import datetime, timedelta
import subprocess, os, hashlib
 

# datetime.now(TZ_RECIFE)

from tests import *
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

def hash_string(string):
    hash_object = hashlib.sha256(string.encode())
    return hash_object.hexdigest()

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

# Decorator para bloquear rotas da aplicação que necessitem de autenticação de administrador
def login_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.cookies.get('user_id')
        user_email = request.cookies.get('user_email')

        if user_id and user_email:
            user = Usuario.query.filter_by(id=user_id, email=user_email).first()
            if user and user.e_administrador == True:
                # Adiciona o usuário à requisição para ser acessado nas rotas protegidas
                request.user = user
                return f(*args, **kwargs)

        # Redireciona para a página de login se o usuário não estiver autenticado
        flash('Acesso negado, usuário não autorizado', 'danger')
        return redirect(url_for('index'))

    return decorated_function

def password_reset_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.cookies.get('user_id')
        user_email = request.cookies.get('user_email')
        user_admin = request.cookies.get('valid')
        
        if user_id and user_email:
            user = Usuario.query.filter_by(id=user_id, email=user_email).first()
            
            if user.check_password('bibliotec') == False:
                # Adiciona o usuário à requisição para ser acessado nas rotas protegidas
                request.user = user
                return f(*args, **kwargs)

        # Redireciona para a página de login se o usuário não estiver autenticado
        flash('Acesso restrito, reset sua senha para acessar o sistema', 'danger')
        if user_admin == 'True':
            return redirect(url_for('resetSenhaAdmin'))
        elif user_admin == 'False':
            return redirect(url_for('perfilUsuario'))

    return decorated_function

# Rota para realizar login
@app.route('/', methods=['GET', 'POST']) # Sempre que acessar a rota, explicitar quais os metodos que serão usados
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
            response.set_cookie('valid', str(usuario.e_administrador))
            
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
    response.set_cookie('valid', '', expires=0)
    return response

@app.route('/index', methods=['GET'])
@login_required
@password_reset_required
def index():
    livros_emprestados_atual = Emprestimo.query.filter_by(data_devolucao=None).count() 
    total_livros_emprestados = Emprestimo.query.all()
    clientes_cadastrados = Cliente.query.all()
    livros_cadastrados = Livro.query.all()

    
    context = {
        'livros_emprestados_atual' : livros_emprestados_atual,
        'total_livros_emprestados' : len(total_livros_emprestados),
        'clientes_cadastradors' : len(clientes_cadastrados),
        'livros_cadastrados' : len(livros_cadastrados),
    }
    
    breadcrumbs = generate_breadcrumbs([{'title': 'Inicio', 'url': url_for('index')}])
    return render_template('index.html', breadcrumbs=breadcrumbs, context=context)

@app.route('/administracao', methods=['GET', 'POST'])
@login_required
@login_admin_required
@password_reset_required
def administracao(): 
    if request.method == 'POST':
        usuario_id = request.form.get('id')
        email = request.form.get('email')
        nivel_de_acesso = request.form.get('nivel_de_acesso')
        
        if not email or not nivel_de_acesso:
            flash('Todos os campos são obrigatórios!', 'danger')
            return redirect(url_for('administracao'))
        
        if usuario_id:
            usuario = Usuario.query.get(usuario_id)
            if usuario:
                usuario.email = email
                usuario.e_administrador = True if nivel_de_acesso == '1' else False
                db.session.commit()
                flash('Usuário atualizado com sucesso!', 'success')
                return redirect(url_for('administracao'))
        else:
            novo_usuario = Usuario(
                email=email, 
                e_administrador=True if nivel_de_acesso == '1' else False,
                password='bibliotec'
            )
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Usuário adicionado com sucesso, senha padrão bibliotec adcionada, usuario deve resetar senha para usar o sistema!', 'success')
            return redirect(url_for('administracao'))

    
    search_query = request.args.get('search')
    if search_query:    
        search = "%{}%".format(search_query)
        usuarios = Usuario.query.filter(
            (Usuario.email.ilike(search))
        ).all()
    else:
        usuarios = Usuario.query.all()
    
    context = {
        'usuarios': usuarios,
    }
    
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Administração', 'url': url_for('administracao')}
    ])
    
    return render_template('admin/admin.html', breadcrumbs=breadcrumbs, context=context)

@app.route('/excluir_usuario', methods=['POST'])
@login_required
@login_admin_required
@password_reset_required
def excluir_usuario():
    usuario_id = request.form.get('id')
    
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        user_email = request.cookies.get('user_email')
        if user_email == usuario.email:
            flash('Usuário não pode apagar a propria conta!', 'danger')
        else:
            db.session.delete(usuario)
            db.session.commit()
            flash('Usuário excluído com sucesso!', 'success')
    else:
        flash('Usuário não encontrado!', 'danger')
    
    return redirect(url_for('administracao'))

@app.route('/resetSenhaAdmin', methods=['GET','POST'])
@login_required
@login_admin_required
def resetSenhaAdmin():
    if request.method == 'POST':
        user_id = request.form.get('email')
        nova_senha = request.form.get('nova_senha')
    
        user_id_logged = request.cookies.get('user_id')
        
        usuario = Usuario.query.filter_by(id=user_id).first() #Procura um usuario com o ID
        if usuario: #Se existir, realiza reset
            usuario.reset_password(nova_senha) # Chama metodo de reset e senha
            db.session.commit() #Confirma transação

            if usuario.id == int(user_id_logged): #Se o usuario for igual ao que esta logado, realiza logout para acessar com novas credenciais
                flash('Senha atualizada com sucesso! Acesse com as novas credenciais.', 'success')
                return redirect(url_for('logout'))
            else:
                #Senão. retorna para a pagina de reset de senha
                flash('Senha atualizada com sucesso!', 'success')
                return redirect(url_for('resetSenhaAdmin'))
        
        else:
            flash('Usuário não encontrado', 'danger')
            return redirect(url_for('resetSenhaAdmin'))
        
    usuarios = Usuario.query.all()
    
    context = {
        'usuarios': usuarios,
    }
    
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Administração', 'url': url_for('administracao')},
        {'title': 'Redefinição de senha', 'url': url_for('resetSenhaAdmin')}
    ])
    
    
    return render_template('admin/resetSenha.html', context=context, breadcrumbs=breadcrumbs)

# Rotas de cliente
@app.route('/clientes', methods=['GET', 'POST'])
@login_required
@password_reset_required
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
        'search_query': search_query if search_query else '',
    }
    
    return render_template('clientes/clientes.html', context=context, breadcrumbs=breadcrumbs)

@app.route('/excluir_cliente', methods=['POST'])
@login_required
@password_reset_required
def excluir_cliente():
    cliente_id = request.form.get('id')
    cliente = Cliente.query.get(cliente_id)
    
    emprestimos_cliente = Emprestimo.query.filter_by(id_cliente=cliente_id).first()
    if emprestimos_cliente:
        flash('Não foi possivel apagar esse cliente. Existem emprestimos associados ao mesmo.', 'warning')
        return redirect(url_for('clientes'))
    
    if cliente:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    else:
        flash('Cliente não encontrado!', 'danger')
    
    return redirect(url_for('clientes'))

# Rotas de livros
@app.route('/livros', methods=['GET', 'POST'])
@login_required
@password_reset_required
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
    search_query = request.args.get('search') #127.0.0.1:8083?search='Harry'
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

    usuario = Usuario.query.filter_by(id=request.cookies.get('user_id')).first()
    
    e_admin = usuario.e_administrador
    
    context = {
        'livros': livros,
        'generos': generos,
        'search_query': search_query if search_query else '',
        'e_admin': e_admin
    }

    return render_template('livros/livros.html', context=context, breadcrumbs=breadcrumbs)

@app.route('/deletar_livro', methods=['POST'])
@login_required
@login_admin_required
@password_reset_required
def deletar_livro():
    livro_id = request.form.get('id')
    emprestimos_livro = Emprestimo.query.filter_by(id_livro=livro_id).first()
    
    if emprestimos_livro:
        flash('Não foi possivel apagar esse livro. Existem emprestimos associados ao mesmo.', 'warning')
        return redirect(url_for('livros'))
    
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
@password_reset_required
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

# Rotas de emprestimos
@app.route('/emprestimos', methods=['GET', 'POST'])
@login_required
@password_reset_required
def emprestimos():
    if request.method == 'POST':
        id_livro = request.form.get('id_livro')
        id_cliente = request.form.get('id_cliente')
        id_usuario = request.cookies.get('user_id')
        
        try:
            livro = Livro.query.get(id_livro)
            cliente = Cliente.query.get(id_cliente)
        except:
            flash('Livro ou cliente não exitem', 'danger')
            return redirect(url_for('emprestimos'))
        
        # Verificar se o livro está disponível
        if livro.qtd_disponivel <= 0:
            flash('Livro sem estoque disponível.', 'danger')
            return redirect(url_for('emprestimos'))

        # Verificar se o cliente já tem 3 livros emprestados
        emprestimos_cliente = Emprestimo.query.filter_by(id_cliente=id_cliente, data_devolucao=None).count()
        if emprestimos_cliente >= 3:
            flash('Cliente já tem 3 livros emprestados.', 'danger')
            return redirect(url_for('emprestimos'))
        
        #Verifica se o cliente já tem esse livro emprestado
        emprestimo_livro_cliente = Emprestimo.query.filter_by(id_cliente=id_cliente, id_livro=id_livro, data_devolucao=None).first()
        if emprestimo_livro_cliente:
            flash('Cliente já tem esse livro emprestado.', 'danger')
            return redirect(url_for('emprestimos'))           

        # Criar novo empréstimo
        novo_emprestimo = Emprestimo(id_livro=id_livro, id_cliente=id_cliente, id_usuario=id_usuario)
        db.session.add(novo_emprestimo)

        # Atualizar a quantidade disponível do livro
        livro.qtd_disponivel -= 1

        db.session.commit()
        flash('Empréstimo realizado com sucesso!', 'success')
        return redirect(url_for('gerar_comprovante_emprestimo', id_emprestimo=novo_emprestimo.id))
        
    # Processar filtros
    emprestimos_query = Emprestimo.query.order_by(desc(Emprestimo.data_emprestimo))
    
    cliente_id = request.args.get('cliente')
    if cliente_id:
        emprestimos_query = emprestimos_query.filter_by(id_cliente=cliente_id)
    
    usuario_id = request.args.get('usuario')
    if usuario_id:
        emprestimos_query = emprestimos_query.filter_by(id_usuario=usuario_id)
    
    devolucao = request.args.get('devolucao')
    if devolucao is not None:
        if devolucao == '1':
            emprestimos_query = emprestimos_query.filter(Emprestimo.data_devolucao.isnot(None))
        elif devolucao == '0':
            emprestimos_query = emprestimos_query.filter(Emprestimo.data_devolucao.is_(None))

    # Carregar todos os empréstimos
    emprestimos = emprestimos_query.all()
    livros = Livro.query.filter(Livro.qtd_disponivel > 0).all()
    clientes = Cliente.query.all()
    usuarios = Usuario.query.all()
    
    alertas = []
    
    # Verificar se há algum empréstimo sem devolução há mais de 30 dias
    for emprestimo in emprestimos:
        if not emprestimo.data_devolucao and datetime.now() - emprestimo.data_emprestimo > timedelta(days=30):
            alertas.append(f'O livro "{emprestimo.livro.titulo}" emprestado a cliente {emprestimo.cliente.email} está em atraso!')
    
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Emprestimos', 'url': url_for('emprestimos')},
    ])
    
    usuario = Usuario.query.filter_by(id=request.cookies.get('user_id')).first()
    
    e_admin = usuario.e_administrador

    context = {
        'emprestimos': emprestimos,
        'livros': livros,
        'clientes': clientes,
        'usuarios': usuarios,
        'e_admin': e_admin,
    }

    return render_template('emprestimos/emprestimos.html', context=context, breadcrumbs=breadcrumbs, alertas=alertas)

@app.route('/devolucao', methods=['POST'])
@login_required
@password_reset_required
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
        return redirect(url_for('gerar_comprovante_devolucao', id_emprestimo=emprestimo.id))
    else:
        flash('Empréstimo não encontrado ou já devolvido.', 'danger')

    return redirect(url_for('emprestimos'))

@app.route('/emprestimos/<int:id_emprestimo>/comprovante')
@login_required
def gerar_comprovante_emprestimo(id_emprestimo):
    emprestimo = Emprestimo.query.get_or_404(id_emprestimo)
    data_max = emprestimo.data_emprestimo + timedelta(days=30)
    validation_code = hash_string(f'{emprestimo.id}{emprestimo.cliente}{emprestimo.livro}{emprestimo.data_emprestimo}')
    return render_template('emprestimos/comprovante_emprestimo.html', emprestimo=emprestimo, data_max=data_max, validation_code=validation_code)

@app.route('/emprestimos/<int:id_emprestimo>/comprovante-devolucao')
def gerar_comprovante_devolucao(id_emprestimo):
    emprestimo = Emprestimo.query.get_or_404(id_emprestimo)
    validation_code = hash_string(f'{emprestimo.id}{emprestimo.cliente}{emprestimo.livro}{emprestimo.data_devolucao}')
    return render_template('emprestimos/comprovante_devolucao.html', emprestimo=emprestimo, validation_code=validation_code)

# Rotas de dashboard
@app.route('/emprestimos_mensal', methods=['GET'])
@login_required
def emprestimos_mensal():
    emprestimos = db.session.query(
        db.func.date_format(Emprestimo.data_emprestimo, '%Y-%m').label('month'),
        db.func.count(Emprestimo.id).label('count')
    ).group_by('month').all()

    result = {month: count for month, count in emprestimos}
    return jsonify(result)

@app.route('/generos_emprestados', methods=['GET'])
@login_required
def generos_emprestados():
    generos = db.session.query(
        Genero.nome,
        db.func.count(Emprestimo.id).label('count')
    ).join(Livro, Livro.genero_id == Genero.id)\
     .join(Emprestimo, Emprestimo.id_livro == Livro.id)\
     .group_by(Genero.id).all()

    result = {nome: count for nome, count in generos}
    return jsonify(result)

@app.route('/perfilUsuario', methods=['GET', 'POST'])
@login_required
def perfilUsuario():
    user_email = request.cookies.get('user_email')
    usuario = Usuario.query.filter_by(email=user_email).first()
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')

        # Realiza reset
        usuario.reset_password(nova_senha) # Chama metodo de reset e senha
        db.session.commit() #Confirma transação
        
        flash('Senha atualizada com sucesso! Acesse com as novas credenciais.', 'success')
        return redirect(url_for('logout'))
    
    context = {
        'usuario': usuario,
    }
    
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Perfil', 'url': url_for('perfilUsuario')}
    ])
    
    
    return render_template('usuario/perfilUsuario.html', context=context, breadcrumbs=breadcrumbs)

@app.errorhandler(500)
def internal_server_error(error):
    # Manipulador de erro para o código de erro 500
    flash('Algo não saiu como esperavamos, tente mais tarde.', 'danger')
    return redirect(url_for('index'))
    
@app.errorhandler(404)
def not_found_error(error):
    # Manipulador de erro para o código de erro 404
    flash('Url não encontrada.', 'danger')
    return redirect(url_for('index'))

@app.errorhandler(405)
def not_found_error(error):
    # Manipulador de erro para o código de erro 403
    flash('Acesso negado.', 'danger')
    return redirect(url_for('index'))

def gerar_testes():
    with app.app_context():
        geners = generate_genres()
        books = generate_books()
        customers = generate_customers()
        generos_ids = []
        livros_ids = []
        clients_ids = []
        
        users = Usuario.query.all()
        users_id = [user.id for user in users]
        
        for gener in geners:
            new_gener = Genero(
                nome=gener
            )
            db.session.add(new_gener)
            db.session.commit()
            generos_ids.append(new_gener.id)
        
        for book in books:
            new_book = Livro(
                isbn=book['ISBN'],
                titulo=book['Nome'],
                autor= f'Autor { random.randint(1, 10)}{random.randint(1, 10)}{random.randint(1, 10)}',
                genero_id=random.choice(generos_ids),
                qtd_disponivel=book['Qtd_disponivel'],
                qtd_total=book['Qtd_total'],
            )
            db.session.add(new_book)
            db.session.commit()
            livros_ids.append(new_book.id)
            
        for customer in customers:
            new_customer = Cliente(
                email = customer['Email'],
                endereco = customer['Endereço'],
                telefone = customer['Telefone'],
            )
            db.session.add(new_customer)
            db.session.commit()
            clients_ids.append(new_customer.id)
            
        for i in range(1, 1000):
            livro_id = random.choice(livros_ids)
            cliente_id = random.choice(clients_ids)
            
            data_emprestimo = datetime(2020, 1, 1) + timedelta(days=random.randint(0, (datetime.now() - datetime(2020, 1, 1)).days))
            data_devolucao = data_emprestimo + timedelta(days=random.randint(1, 30))
            
            new_emprestimo = Emprestimo(
                id_livro=livro_id,
                id_cliente=cliente_id,
                id_usuario=random.choice(users_id),
                data_emprestimo=data_emprestimo,
                data_devolucao=data_devolucao,
            )
            db.session.add(new_emprestimo)
            db.session.commit()

if __name__ == '__main__':
    run_migrations()
    #gerar_testes()
    
    app.run(debug=True, port=8083)
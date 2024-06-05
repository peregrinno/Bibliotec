from flask import Flask, jsonify, render_template, make_response, redirect, url_for, request, flash, current_app
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
    # Verifica se o método da requisição é POST
    if request.method == 'POST':
        # Obtém os dados do formulário
        usuario_id = request.form.get('id')
        email = request.form.get('email')
        nivel_de_acesso = request.form.get('nivel_de_acesso')
        
        # Valida se todos os campos obrigatórios foram preenchidos
        if not email or not nivel_de_acesso:
            flash('Todos os campos são obrigatórios!', 'danger')
            return redirect(url_for('administracao'))
        
        if usuario_id:
            # Atualiza um usuário existente
            usuario = Usuario.query.get(usuario_id)
            if usuario:
                usuario.email = email
                usuario.e_administrador = True if nivel_de_acesso == '1' else False
                db.session.commit()
                flash('Usuário atualizado com sucesso!', 'success')
                return redirect(url_for('administracao'))
        else:
            # Cria um novo usuário com senha padrão
            novo_usuario = Usuario(
                email=email, 
                e_administrador=True if nivel_de_acesso == '1' else False,
                password='bibliotec'  # Senha padrão, deve ser alterada pelo usuário
            )
            db.session.add(novo_usuario)
            db.session.commit()
            flash('Usuário adicionado com sucesso, senha padrão "bibliotec" adicionada, usuário deve resetar senha para usar o sistema!', 'success')
            return redirect(url_for('administracao'))

    # Verifica se há uma query de busca
    search_query = request.args.get('search')
    if search_query:    
        search = "%{}%".format(search_query)
        usuarios = Usuario.query.filter(
            Usuario.email.ilike(search)
        ).all()
    else:
        # Obtém todos os usuários se não houver busca
        usuarios = Usuario.query.all()
    
    # Cria o contexto para renderização do template
    context = {
        'usuarios': usuarios,
    }
    
    # Gera breadcrumbs para navegação
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Administração', 'url': url_for('administracao')}
    ])
    
    # Renderiza o template de administração com os dados do contexto e breadcrumbs
    return render_template('admin/admin.html', breadcrumbs=breadcrumbs, context=context)

@app.route('/excluir_usuario', methods=['POST'])
@login_required
@login_admin_required
@password_reset_required
def excluir_usuario():
    # Obtém o ID do usuário a ser excluído do formulário
    usuario_id = request.form.get('id')
    
    # Busca o usuário no banco de dados pelo ID
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        # Obtém o email do usuário logado a partir dos cookies
        user_email = request.cookies.get('user_email')
        
        # Verifica se o usuário está tentando excluir a própria conta
        if user_email == usuario.email:
            flash('Usuário não pode apagar a própria conta!', 'danger')
        else:
            # Exclui o usuário do banco de dados
            db.session.delete(usuario)
            db.session.commit()
            flash('Usuário excluído com sucesso!', 'success')
    else:
        # Exibe mensagem de erro se o usuário não for encontrado
        flash('Usuário não encontrado!', 'danger')
    
    # Redireciona de volta para a página de administração
    return redirect(url_for('administracao'))

@app.route('/resetSenhaAdmin', methods=['GET','POST'])
@login_required
@login_admin_required
def resetSenhaAdmin():
    # Verifica se o método da requisição é POST
    if request.method == 'POST':
        # Obtém o ID do usuário e a nova senha do formulário
        user_id = request.form.get('email')
        nova_senha = request.form.get('nova_senha')
    
        # Obtém o ID do usuário logado a partir dos cookies
        user_id_logged = request.cookies.get('user_id')
        
        # Procura um usuário com o ID fornecido
        usuario = Usuario.query.filter_by(id=user_id).first()
        if usuario:
            # Se o usuário existir, realiza o reset da senha
            usuario.reset_password(nova_senha) # Chama método de reset de senha
            db.session.commit() # Confirma a transação no banco de dados

            # Verifica se o usuário que teve a senha resetada é o mesmo que está logado
            if usuario.id == int(user_id_logged):
                # Se for o mesmo usuário, realiza logout para acessar com as novas credenciais
                flash('Senha atualizada com sucesso! Acesse com as novas credenciais.', 'success')
                return redirect(url_for('logout'))
            else:
                # Senão, retorna para a página de reset de senha
                flash('Senha atualizada com sucesso!', 'success')
                return redirect(url_for('resetSenhaAdmin'))
        else:
            # Exibe mensagem de erro se o usuário não for encontrado
            flash('Usuário não encontrado', 'danger')
            return redirect(url_for('resetSenhaAdmin'))
    
    # Obtém todos os usuários para exibir na página de redefinição de senha
    usuarios = Usuario.query.all()
    
    # Cria o contexto para renderização do template
    context = {
        'usuarios': usuarios,
    }
    
    # Gera breadcrumbs para navegação
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Administração', 'url': url_for('administracao')},
        {'title': 'Redefinição de senha', 'url': url_for('resetSenhaAdmin')}
    ])
    
    # Renderiza o template de redefinição de senha com os dados do contexto e breadcrumbs
    return render_template('admin/resetSenha.html', context=context, breadcrumbs=breadcrumbs)

# Rotas de cliente
@app.route('/clientes', methods=['GET', 'POST'])
@login_required
@password_reset_required
def clientes():       
    # Verifica se o método da requisição é POST
    if request.method == 'POST':
        # Obtém os dados do formulário
        cliente_id = request.form.get('id')
        email = request.form.get('email')
        endereco = request.form.get('endereco')
        telefone = request.form.get('telefone')

        # Valida se todos os campos obrigatórios foram preenchidos
        if not email or not endereco or not telefone:
            flash('Todos os campos são obrigatórios!', 'danger')
            return redirect(url_for('index'))

        if cliente_id:
            # Atualiza um cliente existente
            cliente = Cliente.query.get(cliente_id)
            if cliente:
                cliente.email = email
                cliente.endereco = endereco
                cliente.telefone = telefone
                db.session.commit()
                flash('Cliente atualizado com sucesso!', 'success')
        else:
            # Cria um novo cliente
            novo_cliente = Cliente(email=email, endereco=endereco, telefone=telefone)
            db.session.add(novo_cliente)
            db.session.commit()
            flash('Cliente adicionado com sucesso!', 'success')
    
    # Busca
    search_query = request.args.get('search')
    if search_query:
        # Realiza busca por email ou telefone
        search = "%{}%".format(search_query)
        clientes = Cliente.query.filter(
            (Cliente.email.ilike(search)) | 
            (Cliente.telefone.ilike(search))
        ).all()
    else:
        # Obtém todos os clientes se não houver busca
        clientes = Cliente.query.all()
    
    # Gera breadcrumbs para navegação
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Clientes', 'url': url_for('clientes')},
    ])    
    
    # Cria o contexto para renderização do template
    context = {
        'clientes': clientes,
        'search_query': search_query if search_query else '',
    }
    
    # Renderiza o template de clientes com os dados do contexto e breadcrumbs
    return render_template('clientes/clientes.html', context=context, breadcrumbs=breadcrumbs)

@app.route('/excluir_cliente', methods=['POST'])
@login_required
@password_reset_required
def excluir_cliente():
    # Obtém o ID do cliente a ser excluído do formulário
    cliente_id = request.form.get('id')
    
    # Busca o cliente no banco de dados pelo ID
    cliente = Cliente.query.get(cliente_id)
    
    # Verifica se há empréstimos associados ao cliente
    emprestimos_cliente = Emprestimo.query.filter_by(id_cliente=cliente_id).first()
    if emprestimos_cliente:
        # Exibe mensagem de aviso se existirem empréstimos associados ao cliente
        flash('Não foi possível apagar esse cliente. Existem empréstimos associados ao mesmo.', 'warning')
        return redirect(url_for('clientes'))
    
    if cliente:
        # Exclui o cliente do banco de dados
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    else:
        # Exibe mensagem de erro se o cliente não for encontrado
        flash('Cliente não encontrado!', 'danger')
    
    # Redireciona de volta para a página de clientes
    return redirect(url_for('clientes'))

# Rotas de livros
@app.route('/livros', methods=['GET', 'POST'])
@login_required
@password_reset_required
def livros():
    # Verifica se o método da requisição é POST
    if request.method == 'POST':
        # Obtém os dados do formulário
        livro_id = request.form.get('id')
        isbn = request.form.get('isbn')
        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        genero_id = request.form.get('genero_id')
        qtd_disponivel = request.form.get('qtd_disponivel')
        qtd_total = request.form.get('qtd_total')

        # Valida se todos os campos obrigatórios foram preenchidos
        if not isbn or not titulo or not autor or not genero_id or not qtd_disponivel or not qtd_total:
            flash('Todos os campos são obrigatórios!', 'danger')
            return redirect(url_for('livros'))

        if livro_id:
            # Atualiza um livro existente
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
            # Cria um novo livro
            novo_livro = Livro(
                isbn=isbn, 
                titulo=titulo, 
                autor=autor, 
                genero_id=genero_id, 
                qtd_disponivel=qtd_disponivel, 
                qtd_total=qtd_total
            )
            db.session.add(novo_livro)
            db.session.commit()
            flash('Livro adicionado com sucesso!', 'success')

    # Busca
    search_query = request.args.get('search')
    if search_query:
        # Realiza busca por título, autor ou ISBN
        search = "%{}%".format(search_query)
        livros = Livro.query.filter(
            (Livro.titulo.ilike(search)) | 
            (Livro.autor.ilike(search)) | 
            (Livro.isbn.ilike(search))
        ).all()
    else:
        # Obtém todos os livros se não houver busca
        livros = Livro.query.all()

    # Carrega todos os gêneros
    generos = Genero.query.all()
    
    # Gera breadcrumbs para navegação
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Livros', 'url': url_for('livros')},
    ])

    # Obtém o usuário logado a partir dos cookies
    usuario = Usuario.query.filter_by(id=request.cookies.get('user_id')).first()
    
    # Verifica se o usuário é administrador
    e_admin = usuario.e_administrador
    
    # Cria o contexto para renderização do template
    context = {
        'livros': livros,
        'generos': generos,
        'search_query': search_query if search_query else '',
        'e_admin': e_admin
    }

    # Renderiza o template de livros com os dados do contexto e breadcrumbs
    return render_template('livros/livros.html', context=context, breadcrumbs=breadcrumbs)

@app.route('/deletar_livro', methods=['POST'])
@login_required
@login_admin_required
@password_reset_required
def deletar_livro():
    # Obtém o ID do livro a ser deletado do formulário
    livro_id = request.form.get('id')
    
    # Verifica se há empréstimos associados ao livro
    emprestimos_livro = Emprestimo.query.filter_by(id_livro=livro_id).first()
    if emprestimos_livro:
        # Exibe mensagem de aviso se existirem empréstimos associados ao livro
        flash('Não foi possível apagar esse livro. Existem empréstimos associados ao mesmo.', 'warning')
        return redirect(url_for('livros'))
    
    # Busca o livro no banco de dados pelo ID
    livro = Livro.query.get(livro_id)
    if livro:
        # Exclui o livro do banco de dados
        db.session.delete(livro)
        db.session.commit()
        flash('Livro deletado com sucesso!', 'success')
    else:
        # Exibe mensagem de erro se o livro não for encontrado
        flash('Livro não encontrado!', 'danger')
    
    # Redireciona de volta para a página de livros
    return redirect(url_for('livros'))

@app.route('/adicionar_genero', methods=['POST'])
@login_required
@password_reset_required
def adicionar_genero():
    # Obtém o nome do gênero a partir do formulário
    nome = request.form.get('nome')
    
    # Verifica se o campo nome está preenchido
    if not nome:
        flash('Nome do gênero é obrigatório!', 'danger')
        return redirect(url_for('livros'))
    
    # Cria uma nova instância de Genero com o nome fornecido
    novo_genero = Genero(nome=nome)
    
    # Adiciona o novo gênero à sessão do banco de dados
    db.session.add(novo_genero)
    
    # Confirma a transação no banco de dados
    db.session.commit()
    
    # Exibe uma mensagem de sucesso
    flash('Gênero adicionado com sucesso!', 'success')
    
    # Redireciona de volta para a página de livros
    return redirect(url_for('livros'))

# Rotas de emprestimos
@app.route('/emprestimos', methods=['GET', 'POST'])
@login_required
@password_reset_required
def emprestimos():
    # Verifica se o método da requisição é POST
    if request.method == 'POST':
        # Obtém os dados do formulário
        id_livro = request.form.get('id_livro')
        id_cliente = request.form.get('id_cliente')
        id_usuario = request.cookies.get('user_id')
        
        try:
            # Tenta obter o livro e o cliente pelo ID
            livro = Livro.query.get(id_livro)
            cliente = Cliente.query.get(id_cliente)
        except:
            flash('Livro ou cliente não existem', 'danger')
            return redirect(url_for('emprestimos'))
        
        # Verifica se o livro está disponível
        if livro.qtd_disponivel <= 0:
            flash('Livro sem estoque disponível.', 'danger')
            return redirect(url_for('emprestimos'))

        # Verifica se o cliente já tem 3 livros emprestados
        emprestimos_cliente = Emprestimo.query.filter_by(id_cliente=id_cliente, data_devolucao=None).count()
        if emprestimos_cliente >= 3:
            flash('Cliente já tem 3 livros emprestados.', 'danger')
            return redirect(url_for('emprestimos'))
        
        # Verifica se o cliente já tem esse livro emprestado
        emprestimo_livro_cliente = Emprestimo.query.filter_by(id_cliente=id_cliente, id_livro=id_livro, data_devolucao=None).first()
        if emprestimo_livro_cliente:
            flash('Cliente já tem esse livro emprestado.', 'danger')
            return redirect(url_for('emprestimos'))           

        # Cria um novo empréstimo
        novo_emprestimo = Emprestimo(id_livro=id_livro, id_cliente=id_cliente, id_usuario=id_usuario)
        db.session.add(novo_emprestimo)

        # Atualiza a quantidade disponível do livro
        livro.qtd_disponivel -= 1

        # Confirma a transação no banco de dados
        db.session.commit()
        flash('Empréstimo realizado com sucesso!', 'success')
        
        # Redireciona para gerar comprovante de empréstimo
        return redirect(url_for('gerar_comprovante_emprestimo', id_emprestimo=novo_emprestimo.id))
        
    # Processa filtros
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

    # Carrega todos os empréstimos de acordo com os filtros
    emprestimos = emprestimos_query.all()
    
    # Carrega todos os livros disponíveis
    livros = Livro.query.filter(Livro.qtd_disponivel > 0).all()
    
    # Carrega todos os clientes e usuários
    clientes = Cliente.query.all()
    usuarios = Usuario.query.all()
    
    # Lista para armazenar alertas
    alertas = []
    
    # Verifica se há algum empréstimo sem devolução há mais de 30 dias
    for emprestimo in emprestimos:
        if not emprestimo.data_devolucao and datetime.now() - emprestimo.data_emprestimo > timedelta(days=30):
            alertas.append(f'O livro "{emprestimo.livro.titulo}" emprestado ao cliente {emprestimo.cliente.email} está em atraso!')
    
    # Gera breadcrumbs para navegação
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Emprestimos', 'url': url_for('emprestimos')},
    ])
    
    # Obtém o usuário logado a partir dos cookies
    usuario = Usuario.query.filter_by(id=request.cookies.get('user_id')).first()
    
    # Verifica se o usuário é administrador
    e_admin = usuario.e_administrador

    # Cria o contexto para renderização do template
    context = {
        'emprestimos': emprestimos,
        'livros': livros,
        'clientes': clientes,
        'usuarios': usuarios,
        'e_admin': e_admin,
    }

    # Renderiza o template de empréstimos com os dados do contexto, breadcrumbs e alertas
    return render_template('emprestimos/emprestimos.html', context=context, breadcrumbs=breadcrumbs, alertas=alertas)

@app.route('/devolucao', methods=['POST'])
@login_required
@password_reset_required
def devolucao():
    # Obtém o ID do empréstimo a ser devolvido do formulário
    id_emprestimo = request.form.get('id_emprestimo')

    # Busca o empréstimo no banco de dados pelo ID
    emprestimo = Emprestimo.query.get(id_emprestimo)
    
    # Verifica se o empréstimo existe e se ainda não foi devolvido
    if emprestimo and not emprestimo.data_devolucao:
        # Registrar a data de devolução
        emprestimo.data_devolucao = datetime.now(TZ_RECIFE)

        # Atualizar a quantidade disponível do livro
        livro = Livro.query.get(emprestimo.id_livro)
        livro.qtd_disponivel += 1

        # Confirma a transação no banco de dados
        db.session.commit()
        flash('Devolução realizada com sucesso!', 'success')
        
        # Redireciona para gerar comprovante de devolução
        return redirect(url_for('gerar_comprovante_devolucao', id_emprestimo=emprestimo.id))
    else:
        # Exibe mensagem de erro se o empréstimo não for encontrado ou já tiver sido devolvido
        flash('Empréstimo não encontrado ou já devolvido.', 'danger')

    # Redireciona de volta para a página de empréstimos
    return redirect(url_for('emprestimos'))

@app.route('/emprestimos/<int:id_emprestimo>/comprovante')
@login_required
def gerar_comprovante_emprestimo(id_emprestimo):
    # Obtém o empréstimo pelo ID ou retorna 404 se não encontrado
    emprestimo = Emprestimo.query.get_or_404(id_emprestimo)
    
    # Calcula a data máxima de devolução (30 dias após a data de empréstimo)
    data_max = emprestimo.data_emprestimo + timedelta(days=30)
    
    # Gera um código de validação único baseado nos dados do empréstimo
    validation_code = hash_string(f'{emprestimo.id}{emprestimo.cliente}{emprestimo.livro}{emprestimo.data_emprestimo}')
    
    # Renderiza o template do comprovante de empréstimo com os dados do empréstimo, data máxima e código de validação
    return render_template('emprestimos/comprovante_emprestimo.html', emprestimo=emprestimo, data_max=data_max, validation_code=validation_code)

@app.route('/emprestimos/<int:id_emprestimo>/comprovante-devolucao')
@login_required
def gerar_comprovante_devolucao(id_emprestimo):
    # Obtém o empréstimo pelo ID ou retorna 404 se não encontrado
    emprestimo = Emprestimo.query.get_or_404(id_emprestimo)
    
    # Gera um código de validação único baseado nos dados da devolução
    validation_code = hash_string(f'{emprestimo.id}{emprestimo.cliente}{emprestimo.livro}{emprestimo.data_devolucao}')
    
    # Renderiza o template do comprovante de devolução com os dados do empréstimo e código de validação
    return render_template('emprestimos/comprovante_devolucao.html', emprestimo=emprestimo, validation_code=validation_code)

# Rotas de dashboard
@app.route('/emprestimos_mensal', methods=['GET'])
@login_required
def emprestimos_mensal():
    if current_app.config['ENV'] == 'production':
        # Consulta para Postgres
        emprestimos = db.session.query(
            db.func.to_char(Emprestimo.data_emprestimo, 'YYYY-MM').label('month'),
            db.func.count(Emprestimo.id).label('count')
        ).group_by('month').all()
    else:
        # Consulta para SQLite
        emprestimos = db.session.query(
            db.func.strftime('%Y-%m', Emprestimo.data_emprestimo).label('month'),
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

@app.route('/authDocs', methods=['GET', 'POST'])
@login_required
def authDocs():
    # Verifica se o método da requisição é POST
    if request.method == 'POST':
        # Obtém os dados do formulário
        id_emprestimo = request.form.get('id_emprestimo')
        tipo_hash = request.form.get('tipo_hash')  # Verifica se é empréstimo ou devolução
        hash_code = request.form.get('hash_code')
        
        # Busca o empréstimo no banco de dados pelo ID ou retorna 404 se não encontrado
        emprestimo = Emprestimo.query.get_or_404(id_emprestimo)

        if int(tipo_hash) == 1:  # Se for 1 então é empréstimo
            # Gera o hash do empréstimo
            hash_emprestimo = hash_string(f'{emprestimo.id}{emprestimo.cliente}{emprestimo.livro}{emprestimo.data_emprestimo}')
            
            if hash_code == hash_emprestimo:
                flash('Autenticado com sucesso!', 'success')
                return redirect(url_for('authDocs'))
            else:
                flash('Autenticação inválida!', 'danger')
                return redirect(url_for('authDocs'))
        else:  # Se não for 1, então é devolução
            # Gera o hash da devolução
            hash_devolucao = hash_string(f'{emprestimo.id}{emprestimo.cliente}{emprestimo.livro}{emprestimo.data_devolucao}')
            if hash_code == hash_devolucao:
                flash('Autenticado com sucesso!', 'success')
                return redirect(url_for('authDocs'))
            else:
                flash('Autenticação inválida!', 'danger')
                return redirect(url_for('authDocs'))

    # Gera breadcrumbs para navegação
    breadcrumbs = generate_breadcrumbs([
        {'title': 'Inicio', 'url': url_for('index')},
        {'title': 'Autenticar documentos', 'url': url_for('authDocs')}
    ])
    
    # Renderiza o template de autenticação de documentos com os breadcrumbs
    return render_template('emprestimos/authDocs.html', breadcrumbs=breadcrumbs)


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

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

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
    #run_migrations() #Para caso de produção, aplica alterações
    #gerar_testes() #Para caso de desenvolvimento, gera novos dados, BANCO DE DESENVOLVIMENTO JÁ APLICADO, NÃO USAR NOVAMENTE.
    app.run(debug=True, port=8083)
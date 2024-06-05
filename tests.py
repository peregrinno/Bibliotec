import random
import string

def generate_isbn():
    return ''.join(random.choices(string.digits, k=13))

def generate_genres():
    return ["Ficção", "Não-ficção", "Fantasia", "Mistério", "Romance", "Ficção Científica", "Biografia", "História", "Autobiografia", "Terror"]

def generate_books(num_books=50):
    books = []

    for i in range(num_books):
        book = {
            "Nome": f"Livro {i+1}",
            "ISBN": generate_isbn(),
            "Qtd_disponivel": random.randint(1, 10),
            "Qtd_total": 0  # Placeholder for now
        }
        book["Qtd_total"] = random.randint(book["Qtd_disponivel"], book["Qtd_disponivel"] + 10)
        books.append(book)

    return books


def generate_email(existing_emails):
    while True:
        domains=["gmail.com", "yahoo.com", "hotmail.com"]
        
        nomes = [
        "antonio", "beatriz", "carla", "diego", "eduarda", 
        "fernando", "gabriela", "henrique", "isabela", "joao", 
        "karina", "leonardo", "mariana", "nicolas", "olivia", 
        "paulo", "quiteria", "rafael", "sabrina", "tiago"
        ]

        sobrenomes = [
            "almeida", "barbosa", "costa", "dias", "esteves", 
            "ferreira", "gomes", "henriques", "isidoro", "junior", 
            "keller", "lima", "martins", "neves", "oliveira", 
            "pereira", "quintela", "ribeiro", "santos", "teixeira"
        ]
        
        conectores = [ '.', '_']
        
        email = f"{random.choice(nomes)}{random.choice(conectores)}{random.choice(sobrenomes)}{random.randint(0, 9)}@{random.choice(domains)}"
        if email not in existing_emails:
            existing_emails.add(email)
            return email

def generate_address():
    streets = [
    "rua das flores", "avenida central", "travessa do sol", "praca da liberdade",
    "rua nova", "rua da paz", "avenida dos estados", "rua dos pinheiros", 
    "travessa da alegria", "praca do comercio", "rua dos andradas", 
    "avenida paulista", "rua santa maria", "rua das acacias", "rua do porto", 
    "rua sao joao", "avenida brasil", "rua do mercado", "praca da matriz", 
    "rua dos girassois", "rua das hortensias", "rua do sol nascente", 
    "rua das laranjeiras", "avenida independencia", "rua do rosario", 
    "travessa das violetas", "rua das camelias", "rua da serra", 
    "praca do estudante", "rua dos cravos"
    ]
    cities = ["Caruaru", "Barcarena", "São Paulo"]
    states = ["Pernambuco", "Pará", "São Paulo"]
    street = random.choice(streets)
    number = random.randint(1, 1000)
    city = random.choice(cities)
    state = random.choice(states)
    return f"{street}, {number}, {city} - {state}"

def generate_phone():
    return f"({random.randint(10, 99)}) {random.randint(90000, 99999)}-{random.randint(1000, 9999)}"

def generate_customers(num_customers=50):
    existing_emails = set()
    customers = []

    for i in range(num_customers):
        customer = {
            "Email": generate_email(existing_emails),
            "Endereço": generate_address(),
            "Telefone": generate_phone()
        }
        customers.append(customer)

    return customers
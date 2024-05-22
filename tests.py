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


def generate_email(existing_emails, domain="example.com"):
    while True:
        email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + "@" + domain
        if email not in existing_emails:
            existing_emails.add(email)
            return email

def generate_address():
    streets = ["Rua A", "Rua B", "Rua C", "Avenida X", "Avenida Y"]
    cities = ["Cidade 1", "Cidade 2", "Cidade 3"]
    states = ["Estado A", "Estado B", "Estado C"]
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
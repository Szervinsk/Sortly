import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

# 1. Cria a aplicação Flask
app = Flask(__name__)

# 2. Configurações
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configuração do Banco de Dados (SQLite)
# O arquivo será criado em instance/database.db ou na raiz app/database.db dependendo da versão
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. Inicializa o Banco ligado ao App
db = SQLAlchemy(app)

# 4. Importa as views e models (IMPORTANTE: Fica no final)
# Isso evita o erro de "importação circular". O Python lê o arquivo de cima para baixo,
# então quando chega aqui, a variável 'app' e 'db' já existem para o views.py usar.
with app.app_context():
    from app import views  # Carrega as rotas
    from app import models # Carrega as tabelas na memória do SQLAlchemy
    
    # Cria as tabelas se elas não existirem
    db.create_all()
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask_cors import CORS

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data-learn3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '123'
app.config['SESSION_PERMANENT'] = True  # Sessão permanente
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=14)

db = SQLAlchemy(app)

CORS(app)


# Importe e registre as blueprints (rotas) da sua aplicação
from app.routes import artigos_bp, users_bp, sessoes_bp, redacao_bp, geral_bp, estudaplay_bp
app.register_blueprint(artigos_bp)
app.register_blueprint(users_bp)
app.register_blueprint(sessoes_bp)
app.register_blueprint(redacao_bp)
app.register_blueprint(geral_bp)
app.register_blueprint(estudaplay_bp)
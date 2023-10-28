from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Crie as instâncias do Flask, SQLAlchemy e LoginManager
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myapp2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '123'
db = SQLAlchemy(app)




# Importe e registre as blueprints (rotas) da sua aplicação
from app.routes import artigos_bp, users_bp, duvidas_bp, iaplan_bp
app.register_blueprint(artigos_bp)
app.register_blueprint(users_bp)
app.register_blueprint(duvidas_bp)
app.register_blueprint(iaplan_bp)
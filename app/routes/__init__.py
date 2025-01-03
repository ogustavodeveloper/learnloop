from flask import Blueprint

artigos_bp = Blueprint('artigos', __name__)
users_bp = Blueprint('users', __name__)
iaplan_bp = Blueprint('learnplan', __name__)
feciba_bp = Blueprint('feciba', __name__)
redacao_bp = Blueprint('redacao', __name__)
simulados_bp = Blueprint("simulado", __name__)

from app.routes import artigos, users, plan, feciba, redacao, simulado
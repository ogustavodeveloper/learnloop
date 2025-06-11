from flask import Blueprint

artigos_bp = Blueprint('artigos', __name__)
users_bp = Blueprint('users', __name__)
sessoes_bp = Blueprint('sessoes', __name__)
redacao_bp = Blueprint('redacao', __name__)
geral_bp = Blueprint('geral', __name__)
estudaplay_bp = Blueprint('estudaplay', __name__)
revisoes_bp = Blueprint('revisoes', __name__)

from app.routes import artigos, sessoes, users, redacao, geral, estudaplay, revisoes
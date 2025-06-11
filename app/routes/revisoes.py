from app.routes import revisoes_bp
from app.models import Revisoes, SessionStudie
from flask import render_template

@revisoes_bp.route("/register-revisao")
def registerRevisao():
    return False
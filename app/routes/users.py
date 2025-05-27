from flask import request, session, jsonify, redirect
from app import db
from app.models import User
from passlib.hash import bcrypt_sha256
import uuid
from app.routes import users_bp
import logging

logger = logging.getLogger(__name__)

def hash_password(password):
    return bcrypt_sha256.hash(password)

@users_bp.before_request
def before_request():
    logger.debug("Requisição recebida no Blueprint de 'users'.")

@users_bp.route('/api/signup', methods=["POST"])
def signup():
    data = request.form
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify({"error": "Todos os campos são obrigatórios."}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Usuário ou e-mail já cadastrado."}), 409

    try:
        hashed_password = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            id=str(uuid.uuid4())
        )
        db.session.add(new_user)
        db.session.commit()
        session["user"] = new_user.id
        session.permanent = True
        return jsonify({"msg": "Usuário cadastrado com sucesso."}), 201
    except Exception as e:
        logger.error(f"Erro ao cadastrar usuário: {e}")
        db.session.rollback()
        return jsonify({"error": "Erro interno ao cadastrar usuário."}), 500

@users_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or request.form
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Usuário e senha são obrigatórios."}), 400

    user = User.query.filter_by(username=username).first()
    if user and bcrypt_sha256.verify(password, user.password):
        session["user"] = user.id
        session.permanent = True
        return jsonify({"msg": "Login realizado com sucesso."}), 200
    return jsonify({"error": "Usuário ou senha incorretos."}), 401

@users_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"msg": "Logout realizado com sucesso."}), 200

@users_bp.route("/api/user", methods=["GET"])
def get_user():
    user_id = session.get("user")
    if not user_id:
        return jsonify({"error": "Usuário não autenticado."}), 401
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200

@users_bp.route("/api/delete-user", methods=["POST"])
def delete_user():
    user_id = session.get("user")
    if not user_id:
        return jsonify({"error": "Usuário não autenticado."}), 401
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404

    data = request.get_json()
    senha = data.get("senha")
    if not senha or not bcrypt_sha256.verify(senha, user.password):
        return jsonify({"error": "Senha incorreta."}), 401

    try:
        db.session.delete(user)
        db.session.commit()
        session.clear()
        return jsonify({"msg": "Usuário deletado com sucesso."}), 200
    except Exception as e:
        logger.error(f"Erro ao deletar usuário: {e}")
        db.session.rollback()
        return jsonify({"error": "Erro interno ao deletar usuário."}), 500

@users_bp.route("/api/update-user", methods=["POST"])
def update_user():
    user_id = session.get("user")
    if not user_id:
        return jsonify({"error": "Usuário não autenticado."}), 401
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username:
        user.username = username
    if password:
        user.password = hash_password(password)

    try:
        db.session.commit()
        return jsonify({"msg": "Usuário atualizado com sucesso."}), 200
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário: {e}")
        db.session.rollback()
        return jsonify({"error": "Erro interno ao atualizar usuário."}), 500
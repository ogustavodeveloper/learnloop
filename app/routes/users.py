from flask import render_template, request, session, jsonify, redirect, url_for, make_response, Response
from flask.json import jsonify
from app.routes import users_bp
from app.models import User, buscas, Artigo, Redacao, Correcoes
from passlib.hash import bcrypt_sha256
from app import db
import uuid
import markdown

@users_bp.route("/termos-de-uso")
def termosDeUso():
    return render_template("termos.html")

@users_bp.route("/politica-de-privacidade")
def politicaPrivacidade():
    
    return render_template("privacidade.html")

@users_bp.route("/sobre")
def sobrePage():
   return render_template("sobre.html")

@users_bp.route("/contato")
def contatoPage():
   return render_template("contato.html")

@users_bp.route("/guia")
def guia():
  return render_template("guia.html")

# Rota para criar um novo usuário
@users_bp.route("/cadastro")
def cadastroPage():
    return render_template("signup.html")

@users_bp.route("/login")
def loginPage():
    return render_template("login.html")

@users_bp.route('/listar')
def listar_usuarios():
    usuarios = User.query.all()
    return render_template('users/listar.html', usuarios=usuarios)

def crip(dado):
  dado_criptografado = bcrypt_sha256.hash(dado)
  return str(dado_criptografado)

@users_bp.route('/api/signup', methods=["POST"])
def signup():

  username = request.form["username"]
  password = crip(request.form["password"])
  email = request.form["email"]

  newUser = User(username=username, email=email, password=password, id=str(uuid.uuid4()))
  db.session.add(newUser)
  db.session.commit()
  session["user"] = newUser.id 

  
  return redirect("/")

@users_bp.route("/api/login", methods=["GET"])
def login():
  username = request.args.get("username")
  password = request.args.get("password")
  user = User.query.filter_by(username=username).first()
  if user and bcrypt_sha256.verify(password, user.password):
    session["user"] = user.id

    return redirect("/")
  else:
    return "<h1>Usuário ou senha incorreto</h1>"

@users_bp.route("/api/logout")
def logout():
  session.clear()
  return redirect("/login")

@users_bp.route("/api/user")
def user():
  user_id = session.get("user")
  user = User.query.filter_by(id=user_id).first()
  return jsonify({"user": user})

@users_bp.route("/api/delete-user", methods=["POST"])
def delete_user():
  user_id = session.get("user")
  user = User.query.filter_by(id=user_id).first()
  senha = request.get_json()["senha"]
  if bcrypt_sha256.verify(senha, user.password):
    db.session.delete(user)
    db.session.commit()
    session.clear()
    return jsonify({"msg": "usuario deletado com sucesso"})
  else:
    return jsonify({"msg": "Senha incorreta"})

@users_bp.route("/api/update-user", methods=["POST"])
def update_user():
  data = request.get_json()
  user_id = session.get("user")
  user = User.query.filter_by(id=user_id).first()
  user.username = data["username"]
  user.password = data["password"]
  db.session.commit()
  return jsonify({"msg": "usuario atualizado com sucesso"})

@users_bp.route('/sitemap.xml')
def sitemap():
    artigos = Artigo.query.all()
    urls = [f"https://learnloop.site/artigo/{artigo.id}" for artigo in artigos]
    sitemap_xml = render_template('sitemap.xml', urls=urls)
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response

@users_bp.route('/admin/28092007')
def admin_panel():
    users = User.query.all()
    searches = buscas.query.all()
    articles = Artigo.query.all()
    corrections = Correcoes.query.all()
    return render_template('admin.html', users=users, searches=searches, articles=articles, correcoes=corrections)

# Rota para excluir um artigo
@users_bp.route('/delete_article')
def delete_article():
    artigos = Artigo.query.all()
    for art in artigos:
        db.session.delete(art)
        db.session.commit()

    return "todos deletados."

# Rota para excluir um arquivo
@users_bp.route('/delete_file/<file_id>', methods=['POST'])
def delete_file(file_id):
    file = Files.query.get(file_id)
    if file:
        db.session.delete(file)
        db.session.commit()
    return redirect("/admin/28092007")

# Rota para excluir um grupo
@users_bp.route('/delete_group', methods=['POST'])
def delete_group():
    group_id = request.form.get('group_id')
    group = Grupo.query.filter_by(id=group_id).first()
    if group:
        db.session.delete(group)
        db.session.commit()
    return redirect("/admin/28092007")

@users_bp.route('/robots.txt')
def robots_txt():
    robots_txt_content = """
    User-agent: *
    Disallow: /admin/
    Disallow: /user/
    Disallow: /settings/
    Disallow: /private/

    User-agent: Googlebot
    Allow: /public/

    Sitemap: https://learnloop.site/sitemap.xml
    """
    return Response(robots_txt_content, mimetype='text/plain')

@users_bp.route("/api/save-redacao", methods=["POST"])
def SalvarRedacoes():
    data = request.get_json()
    user = User.query.filter_by(id=session["user"]).first()
    redacao = Redacao(user=user.id, titulo=data["titulo"], texto=markdown.markdown(data["texto"]))
    db.session.add(redacao)
    db.session.commit()

    return jsonify({
        "msg": "success"
    })


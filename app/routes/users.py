from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for, make_response, Response
from app import db
from app.models import User, Artigo, Redacao, buscas, Corrections
from passlib.hash import bcrypt_sha256
import uuid
import markdown
from app.routes import users_bp
from datetime import datetime


# Função que será executada antes de cada requisição dentro deste Blueprint
@users_bp.before_request
def before_request():
    print("Esta função será chamada antes de cada requisição no Blueprint de 'users'.")

# Rota para termos de uso
@users_bp.route("/termos-de-uso")
def termosDeUso():
    return render_template("termos.html")

# Rota para política de privacidade
@users_bp.route("/politica-de-privacidade")
def politicaPrivacidade():
    return render_template("privacidade.html")

# Rota sobre a página
@users_bp.route("/sobre")
def sobrePage():
    return render_template("sobre.html")

# Rota de contato
@users_bp.route("/contato")
def contatoPage():
    return render_template("contato.html")

# Rota guia
@users_bp.route("/guia")
def guia():
    return render_template("guia.html")

# Rota para o cadastro de usuário
@users_bp.route("/cadastro")
def cadastroPage():
    return render_template("signup.html")

# Rota para login de usuário
@users_bp.route("/login")
def loginPage():
    return render_template("login.html")

# Rota para listar todos os usuários
@users_bp.route('/listar')
def listar_usuarios():
    usuarios = User.query.all()
    return render_template('users/listar.html', usuarios=usuarios)

# Função de criptografia de senha
def crip(dado):
    dado_criptografado = bcrypt_sha256.hash(dado)
    return str(dado_criptografado)

# Rota para o cadastro de um novo usuário via API
@users_bp.route('/api/signup', methods=["POST"])
def signup():
    username = request.form["username"]
    password = crip(request.form["password"])
    email = request.form["email"]

    newUser = User(username=username, email=email, password=password, id=str(uuid.uuid4()))
    db.session.add(newUser)
    db.session.commit()
    session["user"] = newUser.id
    session.permanent = True

    return redirect("/")

# Rota de login de usuário via API
@users_bp.route("/api/login", methods=["GET"])
def login():
    username = request.args.get("username")
    password = request.args.get("password")
    user = User.query.filter_by(username=username).first()
    if user and bcrypt_sha256.verify(password, user.password):
        session["user"] = user.id
        session.permanent = True

        return redirect("/")
    else:
        return "<h1>Usuário ou senha incorretos</h1>"

# Rota para logout
@users_bp.route("/api/logout")
def logout():
    session.clear()
    return redirect("/login")

# Rota para obter informações do usuário logado
@users_bp.route("/api/user")
def user():
    user_id = session.get("user")
    user = User.query.filter_by(id=user_id).first()
    return jsonify({"user": user})

# Rota para excluir o usuário
@users_bp.route("/api/delete-user", methods=["POST"])
def delete_user():
    user_id = session.get("user")
    user = User.query.filter_by(id=user_id).first()
    senha = request.get_json()["senha"]
    if bcrypt_sha256.verify(senha, user.password):
        db.session.delete(user)
        db.session.commit()
        session.clear()
        return jsonify({"msg": "usuário deletado com sucesso"})
    else:
        return jsonify({"msg": "Senha incorreta"})

# Rota para atualizar os dados do usuário
@users_bp.route("/api/update-user", methods=["POST"])
def update_user():
    data = request.get_json()
    user_id = session.get("user")
    user = User.query.filter_by(id=user_id).first()
    user.username = data["username"]
    user.password = data["password"]
    db.session.commit()
    return jsonify({"msg": "usuário atualizado com sucesso"})

# Rota do Sitemap


@users_bp.route('/sitemap.xml')
def sitemap():
    artigos = Artigo.query.all()
    
    # Gerar as URLs e incluir a data formatada para cada artigo
    urls = []
    for artigo in artigos:
        # Formatar a data de criação do artigo no formato ISO 8601
        data_criacao = datetime.strptime(artigo.data, '%Y-%m-%dT%H:%M:%S+00:00').strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        # Adicionar a URL e a data formatada à lista de URLs
        urls.append({
            'loc': f"https://learnloop.com.br/artigo/{artigo.id}",
            'lastmod': data_criacao
        })

    # Renderizar o sitemap.xml usando o template, passando as URLs
    sitemap_xml = render_template('sitemap.xml', urls=urls)
    
    # Criar a resposta e definir o cabeçalho Content-Type para 'application/xml'
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response

# Rota para o painel de administração
@users_bp.route('/admin/28092007')
def admin_panel():
    users = User.query.all()
    searches = buscas.query.all()
    articles = Artigo.query.all()
    correcoes = Corrections.query.all()
    
    return render_template('admin.html', users=users, searches=searches, articles=articles, correcoes=correcoes)

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

# Rota para o arquivo robots.txt
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

# Rota para salvar redações
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

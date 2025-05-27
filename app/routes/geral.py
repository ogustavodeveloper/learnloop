from flask import render_template, request, session, jsonify, redirect, make_response, Response
from app import db
from app.models import User, Artigo, Redacao, buscas, Corrections
from app.routes import geral_bp
from datetime import datetime

# Rota para termos de uso
@geral_bp.route("/termos-de-uso")
def termosDeUso():
    return render_template("termos.html")

# Rota para política de privacidade
@geral_bp.route("/politica-de-privacidade")
def politicaPrivacidade():
    return render_template("privacidade.html")

# Rota sobre a página
@geral_bp.route("/sobre")
def sobrePage():
    return render_template("sobre.html")

# Rota de contato
@geral_bp.route("/contato")
def contatoPage():
    return render_template("contato.html")

# Rota guia
@geral_bp.route("/guia")
def guia():
    return render_template("guia.html")

# Rota para o cadastro de usuário
@geral_bp.route("/cadastro")
def cadastroPage():
    return render_template("signup.html")

# Rota para login de usuário
@geral_bp.route("/login")
def loginPage():
    return render_template("login.html")


@geral_bp.route('/sitemap.xml')
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
@geral_bp.route('/admin/28092007')
def admin_panel():
    users = User.query.all()
    searches = buscas.query.all()
    articles = Artigo.query.all()
    correcoes = Corrections.query.all()
    
    return render_template('admin.html', users=users, searches=searches, articles=articles, correcoes=correcoes)

# Rota para excluir um artigo
@geral_bp.route('/delete_article')
def delete_article():
    artigos = Artigo.query.all()
    for art in artigos:
        db.session.delete(art)
        db.session.commit()

    return "todos deletados."





# Rota para o arquivo robots.txt
@geral_bp.route('/robots.txt')
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
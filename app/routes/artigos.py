# Importação dos módulos e classes necessárias
from flask import render_template, redirect, session, jsonify, request, send_file
from app.routes import artigos_bp
from app.models import Artigo, User, buscas
from app import db
import uuid
import markdown
import os
from dotenv import load_dotenv
from passlib.hash import bcrypt_sha256
from datetime import datetime

load_dotenv()

@artigos_bp.route("/create-artigo", methods=["POST", "GET"])
def criarArtigo():
    if request.method == "POST":
        title = request.form["title-art"]
        conteudo = request.form["conteudo-art"]
        categoria = request.form["category"]
        tags = request.form["tags"]
    
        if title == "" or title == " " or len(conteudo) < 1:
            return "Digite algo válido!"

        try:
            user = session["user"]
        except KeyError:
            user = "visit"

        if user == "visit":
            return "Você precisa estar logado."

        # Captura a data e hora atuais e formata para o padrão do sitemap.xml
        data = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')

        newArtigo = Artigo(
            titulo=title, 
            texto=markdown.markdown(conteudo), 
            autor=user, 
            data=data,  # Salvando a data formatada
            categoria=categoria, 
            tags=tags, 
            likes=0, 
            id=str(uuid.uuid4()), 
            views=0
        )
        db.session.add(newArtigo)
        db.session.commit()

        return redirect("/artigo/" + newArtigo.id)

    try:
        user = session['user']
    except KeyError:
        return redirect("/login")

    return render_template("create-artigo.html")

# Rota para excluir um artigo
@artigos_bp.route("/delete-artigo/<id>", methods=["GET"])
def deleteArtigo(id):
    artigo = Artigo.query.filter_by(id=id).first()
    user = User.query.filter_by(id=artigo.autor).first()

    if artigo:
        senha = request.args.get("senha")

        if bcrypt_sha256.verify(senha, user.password):
            db.session.delete(artigo)
            db.session.commit()
            return jsonify({"msg": "success"})
        else:
            return redirect("/artigo/"+artigo.id)
    else:
        return "Artigo Não Existe"

@artigos_bp.route("/artigo/<id>")
def artigoPage(id):
    try:
        user = session['user']
    except KeyError:
        user = 'visit'

    artigo = Artigo.query.filter_by(id=id).first()
    artigo.views = artigo.views + 1
    
    db.session.commit()
    autor = User.query.filter_by(id=artigo.autor).first()
    if artigo:
        return render_template("post.html", artigo=artigo, autor=autor)
    else:
        return "<h1>Artigo Não Existe</h1"

@artigos_bp.route("/search")
def pageSearch():
    categorias = Artigo.query.with_entities(Artigo.categoria).distinct().all()
    nomesCategorias = [categoria[0] for categoria in categorias]
    return render_template("search.html", categorys=nomesCategorias)

def search_word_files(directory, search_terms):
    results = set()

    for filename in os.listdir(directory):
        if filename.endswith(".docx"):
            file_path = os.path.join(directory, filename)
            document = Document(file_path)

            for paragraph in document.paragraphs:
                for run in paragraph.runs:
                    text = run.text
                    for term in search_terms:
                        if term.lower() in text.lower():
                            results.add(filename)

    return [{"file_name": filename} for filename in results]

@artigos_bp.route("/search/artigos")
def artigosSearch():
    pesquisa_i = request.args.get("pesquisa")
    pesquisa = pesquisa_i.lower()

    try:
        user = session["user"]
    except:
        user = "visit"
    newBsc = buscas(user=user, termo=pesquisa)
    db.session.add(newBsc)
    db.session.commit()

    artigos = Artigo.query.filter(
        (Artigo.titulo.ilike(f"%{pesquisa}%")) |
        (Artigo.autor.ilike(f"%{pesquisa}%")) |
        (Artigo.categoria.ilike(f"%{pesquisa}%")) |
        (Artigo.data.ilike(f"%{pesquisa}%")) |
        (Artigo.tags.ilike(f"%{pesquisa}%"))
    ).all()

    directory_path = "app/static/feciba"
    search_terms = pesquisa_i.split(" ")
    word_search_results = search_word_files(directory_path, search_terms)

    return render_template("feed.html", artigos=artigos, feciba_results=word_search_results)

@artigos_bp.route("/download-file/<filename>")
def download_file(filename):
    directory_path = os.path.abspath("app/static/feciba")
    file_path = os.path.join(directory_path, filename)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "Arquivo não encontrado", 404

@artigos_bp.route("/feed/artigos")
def feed_artigos():
    artigos = Artigo.query.all()
    return render_template("feed.html", artigos=artigos, feciba_results=None)

@artigos_bp.route("/api/gerar-artigo-ai", methods=["POST"])
def gerarArtigoPorIa():
    try:
        user = session['user']
        userDb = User.query.filter_by(id=user).first()
        if userDb:
            data = request.get_json()


            # Fazendo a chamada à API do Azure OpenAI
            chat_completion = client.chat.completions.create(
                model="gpt-4o",  # Nome do deployment configurado no Azure
                messages=[
                    {"role": "system", "content": "Você gera artigos autônomos longos e bem estruturados, com base na entrada do usuário, com linguagem informal e atraente."},
                    {"role": "user", "content": f"Resumo: {data['resumo']}"}
                ]
            )

            assistant_response = chat_completion.choices[0].message.content

            return jsonify({
                "msg": "success",
                "response": assistant_response
            })
    except Exception as e:
        return jsonify({"msg": f"Erro: {e}"})

@artigos_bp.route("/api/tirar-duvida-artigo", methods=["POST"])
def tiraDuvidaArtigo():
    try:  
        data = request.get_json()
        user_message = f"Artigo: {data['conteudo_artigo']}. Dúvida: {data['duvida']}"


        # Fazendo a chamada à API do Azure OpenAI
        chat_completion = client.chat.completions.create(
            model="gpt-4o",  # Nome do deployment configurado no Azure
            messages=[
                {"role": "system", "content": "Você responde dúvidas sobre o conteúdo de artigos de forma clara e direta."},
                {"role": "user", "content": user_message}
            ]
        )

        assistant_response = chat_completion.choices[0].message.content


        return jsonify({
            "msg": "success",
            "resposta": assistant_response
        })
    except Exception as e:
        return jsonify({"msg": f"Houve um erro: {e}"})

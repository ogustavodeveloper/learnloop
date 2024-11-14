# Importação dos módulos e classes necessárias
from flask import render_template, redirect, session, jsonify, request, send_file
from app.routes import iaplan_bp
from app.models import SessionStudie, User
from app import db
import uuid
import markdown
import os
import datetime
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

@iaplan_bp.route("/session")
def planPage():
    try:
        user = session['user']
    except:
        return render_template("plan.html", sessions=[])
    sessoes = SessionStudie.query.filter_by(user=session["user"]).all()
    return render_template("plan.html", sessions=sessoes)

@iaplan_bp.route("/download-db")
def download_file():
    # Diretório onde os documentos do Word estão localizados
    directory_path = os.path.abspath("instance")

    file_path = os.path.join(directory_path, "data-learnloop-5.db")

    # Verifica se o arquivo existe e retorna-o para download
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "Arquivo não encontrado", 404

@iaplan_bp.route("/save-session", methods=["POST"])
def saveSession():
    try:
        user = session["user"]
        user_db = User.query.filter_by(id=user).first()
        if user_db:
            data = request.get_json()
            tempo = data["tempo"]
            data_session = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            resumo = markdown.markdown(data["resumo"])
            assunto = data["assunto"]
            newSession = SessionStudie(user=user_db.id, assunto=assunto, resumo=resumo, data=data_session, tempo=tempo, id=str(uuid.uuid4()))
            db.session.add(newSession)
            db.session.commit()

            return jsonify({"msg": "success"})

    except Exception as e:
        return jsonify({"msg": f"deu erro: {e}"})

@iaplan_bp.route("/api/delete-session/<id>")
def removeSession(id):
    session = SessionStudie.query.filter_by(id=id).first()
    db.session.delete(session)
    db.session.commit()

    return redirect("/session")

@iaplan_bp.route("/api/get-resumo-ia", methods=["POST"])
def getResumo():
    try:
        user = session["user"]
        data = request.get_json()
        anotacoes = data["notes"]
        user_message = {"role": "user", "content": f"Minhas anotações: {anotacoes}"}

        # Usando o Azure OpenAI para gerar o resumo
        chat_completion = client.chat.completions.create(
            model="gpt-4o",  # model = "deployment_name"
            messages=[
                {"role": "system", "content": "Você é uma Inteligência Artificial para estudos. Com base nas anotações que o usuário enviar, você deverá criar um resumo bem estruturado do que ele aprendeu."},
                user_message
            ]
        )

        resposta = chat_completion.choices[0].message.content

        return jsonify({"msg": resposta})

    except Exception as e:
        return jsonify({"msg": f"deu erro: {e}"})

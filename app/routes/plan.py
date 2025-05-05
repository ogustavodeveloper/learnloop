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
from azure.storage.blob import BlobServiceClient

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def upload_to_azure_blob(container_name, file_path, blob_name):
        try:
                # Obter a connection string dos segredos (variável de ambiente)
            connection_string = os.getenv('CONECTION')
            if not connection_string:
                raise ValueError("Connection string não encontrada nos segredos.")

                                                    # Conectar ao serviço Blob e ao container
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
                                                                            
                                                                                    # Fazer upload do arquivo
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
                                                                                                                
                                                                                                                        # Gerar e retornar o link de acesso ao blob
            blob_url = blob_client.url
            return blob_url

        except Exception as e:
            print(f"Erro ao enviar o arquivo: {e}")
            return None

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

    file_path = os.path.join(directory_path, "data-learn2.db")

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
            
            tempo = request.form.get("tempo")
            data_session = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            resumo = markdown.markdown(request.form.get("resumo"))
            assunto = request.form.get("assunto")
            documento = request.files.get("documento")
            print(documento.filename)
            caminho_doc_temp = os.path.join("/tmp", documento.filename)
            documento.save(caminho_doc_temp)
            projeto_az = upload_to_azure_blob("learnloop-projetos", caminho_doc_temp, documento.filename)

            newSession = SessionStudie(user=user_db.id, assunto=assunto, resumo=resumo, data=data_session, tempo=tempo, id=str(uuid.uuid4()), documento=projeto_az)
            db.session.add(newSession)
            db.session.commit()

            return jsonify({"msg": "success", "msg": documento.filename})

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

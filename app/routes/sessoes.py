# Importação dos módulos e classes necessárias
from flask import render_template, redirect, session, jsonify, request, send_file
from app.routes import sessoes_bp
from app.models import SessionStudie, User, Documento, Simulado, Pergunta, Revisoes
from app import db
import uuid
import markdown
import os
import datetime
from openai import AzureOpenAI
from azure.storage.blob import BlobServiceClient
import json 


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

        # Conectar ao serviço Blob
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Tentar criar o container (ignorar erro se já existir)
        try:
            blob_service_client.create_container(container_name)
        except Exception as e:
            # Se o erro for porque já existe, ignore
            if "ContainerAlreadyExists" not in str(e):
                raise

        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        blob_url = blob_client.url
        return blob_url

    except Exception as e:
        print(f"Erro ao enviar o arquivo: {e}")
        return None

@sessoes_bp.route("/session/<id>")
def planPage(id):
    try:
        user = session['user']
    except:
        return render_template("plan.html", sessions=[])
    sessao = SessionStudie.query.filter_by(id=id).first()
    documentos = Documento.query.filter_by(sessao=id).all()
    quizzes = Simulado.query.filter_by(sessao=id).all()
    return render_template("session.html", documentos=documentos, sessao=sessao, quizzes=quizzes)

@sessoes_bp.route("/add-doc", methods=["POST"])
def addDoc():
    try:
      documento = request.files.get("documento")
      sessao = request.form.get("assunto")
      caminho_doc_temp = os.path.join("/tmp", documento.filename)
      documento.save(caminho_doc_temp)
      filename = documento.filename 
      projeto_az = upload_to_azure_blob("learnloop-projetes", caminho_doc_temp, documento.filename)

      new_doc = Documento(id=str(uuid.uuid4()), filename=filename, url=projeto_az, sessao=sessao)
      db.session.add(new_doc)
      db.session.commit()

      return jsonify({
        "msg": "success",
        "id": new_doc.id,
        "url": new_doc.url,
        "filename": new_doc.filename
    })

    except Exception as e:
      return jsonify({"msg": f"deu erro: {e}"})
    

    

@sessoes_bp.route("/feed-session")
def feedSession():
    sessions = SessionStudie.query.filter_by(user=session["user"])
    return render_template("feed-sessions.html", sessions=sessions)

@sessoes_bp.route("/download-db")
def download_file():
    # Diretório onde os documentos do Word estão localizados
    directory_path = os.path.abspath("instance")

    file_path = os.path.join(directory_path, "data-learn3.db")

    # Verifica se o arquivo existe e retorna-o para download
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "Arquivo não encontrado", 404

@sessoes_bp.route("/save-session", methods=["POST"])
def saveSession():
    try:
        user = session["user"]
        user_db = User.query.filter_by(id=user).first()
        if user_db:
            print(datetime.date.today())
            data_atual = datetime.datetime.now()
            dia_seguinte = data_atual + datetime.timedelta(days=1)

            print(f"Data atual: {data_atual.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Dia seguinte: {dia_seguinte.strftime('%Y-%m-%d %H:%M:%S')}")
            
            data_session = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            resumo = markdown.markdown(request.form.get("resumo"))
            assunto = request.form.get("assunto")

            #user_message = {"role": "user", "content": f"Tema: {assunto}. Minhas anotações: {resumo}"}

                    # Usando o Azure OpenAI para gerar o resumo
            # chat_completion = client.chat.completions.create(
                                  #      model="gpt-4o",  # model = "deployment_name"
                                    #    messages=[
                                        #    {"role": "system", "content": "Você é uma Inteligência Artificial voltada para auxiliar nos estudos. "
                                       #                     "Quando o usuário fornecer anotações, reestruture o conteúdo de forma clara, coerente e bem organizada, sem usar markdown. "
                                               #                             "Caso o conteúdo esteja em branco, identifique o tema indicado e crie uma nova anotação explicativa. "
                                                  #                                          "Essa nova anotação deve ensinar os conceitos fundamentais que o estudante precisa saber para compreender o assunto, "
                                                        #                                                    "e também incluir uma parte dedicada especificamente ao tema central proposto."},
                                   #         user_message
                                   #     ]
                                  #  )

           # resposta = chat_completion.choices[0].message.content

            newSession = SessionStudie(user=user_db.id, assunto=assunto, resumo="", data=data_session, id=str(uuid.uuid4()), revisao=0)
            db.session.add(newSession)
            db.session.commit()

            revisoes = [1, 7, 14, 30]

            for revisao in revisoes:
                data_atual = datetime.datetime.now().date()
                dia = data_atual + datetime.timedelta(days=revisao)
                newRevisao = Revisoes(id=str(uuid.uuid4()), user=session["user"], assunto=assunto, data=dia, status="pendente", id_session=newSession.id)
                db.session.add(newRevisao)
                db.session.commit()

            return jsonify({"msg": "success", "id": newSession.id})

    except Exception as e:
        return jsonify({"msg": f"deu erro: {e}"})

@sessoes_bp.route("/update-anotacao", methods=["POST"])
def updateAnotacao():
    id = request.form.get("sessao")
    anotado = request.form.get("anotacao")
    sessao = SessionStudie.query.filter_by(id=id).first()
    sessao.resumo = anotado 
    db.session.commit()

    return jsonify({
        "msg": "success"
    })

@sessoes_bp.route("/api/delete-session/<id>")
def removeSession(id):
    session = SessionStudie.query.filter_by(id=id).first()
    db.session.delete(session)
    db.session.commit()

    return redirect("/feed-session")

@sessoes_bp.route("/api/get-resumo-ia", methods=["POST"])
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
    
@sessoes_bp.route("/api/gerar-quiz", methods=["POST"])
def gerarQuiz():
    try:
        
        sessao = request.form.get("sessao")
        print(sessao)
        sessaodb = SessionStudie.query.filter_by(id=sessao).first()
        anotacao = request.form.get("anotacao")
        assunto = request.form.get("assunto")

        chat_completion = client.chat.completions.create(
            model="gpt-4o",  # Nome do deployment configurado no Azure
            messages=[
                {"role": "system", "content": """
                Você é um gerador de simulado para ENEM.
                Sua função é criar 5 perguntas com base na anotação que o usuário mandar, e retornar nesse formato em JSON:
                 
                 {
                    "pergunta1": {
                        "pergunta": pergunta gerada,
                        "alternativas": alternativas separadas em /,
                        "respostaCerta": alternativa certa,
                        "resolucao": explicação detalhada da resposta correta
                    },
                    ...
                 }
                 Atenção: cada pergunta deve obrigatoriamente conter uma resolução clara e detalhada no campo "resolucao".
                """},
                {"role": "user", "content": f"Assunto: {assunto}. Anotação: {anotacao}"}
            ],
            temperature=0.1,
            top_p=1.0
        )

        assistant_response = chat_completion.choices[0].message.content.replace('\n', '').replace('json', '').replace('`','')
        assistant_response = json.loads(assistant_response)


        newQuiz = Simulado(id=str(uuid.uuid4()), titulo=assunto, sessao=sessao, user=session["user"], views=0, acertos=0)
        db.session.add(newQuiz)
        db.session.commit()
        
        # Exemplo para a primeira pergunta:
        new_pergunta = Pergunta(
            id=str(uuid.uuid4()),
            questao=assistant_response["pergunta1"]["pergunta"],
            resposta_certa=assistant_response["pergunta1"]["respostaCerta"],
            alternativas=assistant_response["pergunta1"]["alternativas"],
            resolucao=assistant_response["pergunta1"]["resolucao"],  # <-- Adicione esta linha
            quiz=newQuiz.id
        )

        db.session.add(new_pergunta)
        db.session.commit()

        new_pergunta = Pergunta(
            id=str(uuid.uuid4()),
            questao=assistant_response["pergunta2"]["pergunta"],
            resposta_certa=assistant_response["pergunta2"]["respostaCerta"],
            alternativas=assistant_response["pergunta2"]["alternativas"],
            resolucao=assistant_response["pergunta2"]["resolucao"],  # <-- Adicione esta linha
            quiz=newQuiz.id
        )

        db.session.add(new_pergunta)
        db.session.commit()

        new_pergunta = Pergunta(
            id=str(uuid.uuid4()),
            questao=assistant_response["pergunta3"]["pergunta"],
            resposta_certa=assistant_response["pergunta3"]["respostaCerta"],
            alternativas=assistant_response["pergunta3"]["alternativas"],
            resolucao=assistant_response["pergunta3"]["resolucao"],  # <-- Adicione esta linha
            quiz=newQuiz.id
        )

        db.session.add(new_pergunta)
        db.session.commit()

        new_pergunta = Pergunta(
            id=str(uuid.uuid4()),
            questao=assistant_response["pergunta4"]["pergunta"],
            resposta_certa=assistant_response["pergunta4"]["respostaCerta"],
            alternativas=assistant_response["pergunta4"]["alternativas"],
            resolucao=assistant_response["pergunta4"]["resolucao"],  # <-- Adicione esta linha
            quiz=newQuiz.id
        )

        db.session.add(new_pergunta)
        db.session.commit()

        new_pergunta = Pergunta(
            id=str(uuid.uuid4()),
            questao=assistant_response["pergunta5"]["pergunta"],
            resposta_certa=assistant_response["pergunta5"]["respostaCerta"],
            alternativas=assistant_response["pergunta5"]["alternativas"],
            resolucao=assistant_response["pergunta5"]["resolucao"],  # <-- Adicione esta linha
            quiz=newQuiz.id
        )

        db.session.add(new_pergunta)
        db.session.commit()



        return jsonify({
            "msg": "success",
            "id": newQuiz.id
        })
    except Exception as e:
        return jsonify({
            "msg": "error",
            "details": str(e)
        })

@sessoes_bp.route("/quiz/<id>")
def pageQuiz(id):

    quiz = Simulado.query.filter_by(id=id).first()

    if not quiz:
        return "Quiz não encontrado", 404

    perguntas = Pergunta.query.filter_by(quiz=quiz.id).all()

    return render_template("quiz.html", perguntas=perguntas, quiz=quiz)

@sessoes_bp.route("/api/delete-doc/<id>", methods=["POST"])
def delete_doc(id):
    doc = Documento.query.filter_by(id=id).first()
    if not doc:
        return jsonify({"msg": "Documento não encontrado"}), 404
    db.session.delete(doc)
    db.session.commit()
    return jsonify({"msg": "success"})

# Importação dos módulos e classes necessárias
from flask import render_template, redirect, session, jsonify, request
from app.routes import sessoes_bp
from app.models import SessionStudie, User, Documento, Simulado, Pergunta, Revisoes
from app import db
import uuid
import os
import datetime
import re
import unicodedata
import base64
from io import BytesIO
from urllib.parse import urlparse, unquote
from openai import OpenAI
from azure.storage.blob import BlobServiceClient
import json 

client = OpenAI(
    api_key=os.environ.get("API_KEY"),
    base_url="https://estudae-ia.openai.azure.com/openai/v1",
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

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}


def normalize_text(text):
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def is_valid_file_type(filename, mimetype=""):
    if not filename:
        return False
    extension = os.path.splitext(filename.lower())[1]
    if extension in ALLOWED_EXTENSIONS:
        return True
    return mimetype.startswith("image/")


def extract_letter(answer_text):
    if not answer_text:
        return None
    match = re.match(r"^\s*([a-zA-Z])\)\s*", answer_text)
    if match:
        return match.group(1).lower()
    return None


def download_blob_bytes_from_url(blob_url):
    try:
        connection_string = os.getenv('CONECTION')
        if not connection_string:
            return None

        parsed = urlparse(blob_url)
        path = parsed.path.lstrip('/')
        parts = path.split('/', 1)
        if len(parts) != 2:
            return None

        container_name, blob_name = parts
        blob_name = unquote(blob_name)

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        return blob_client.download_blob().readall()
    except Exception:
        return None


def extract_text_from_bytes(filename, file_bytes, content_type=""):
    if not file_bytes:
        return ""

    filename = filename.lower()
    is_image = any(filename.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")) or content_type.startswith("image/")
    is_pdf = filename.endswith(".pdf") or content_type == "application/pdf"

    if is_image:
        mime_type = content_type or "image/png"
        image_data_url = f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode('utf-8')}"

        system_prompt = (
            "Você é um transcritor de texto manuscrito. "
            "Leia cuidadosamente a imagem enviada e retorne apenas o texto escrito, "
            "sem markdown, sem explicações e sem nenhum comentário adicional."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url,
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.0,
            top_p=1.0
        )

        assistant_response = chat_completion.choices[0].message.content
        if isinstance(assistant_response, list):
            return ''.join(
                part.get('text', '') if isinstance(part, dict) else str(part)
                for part in assistant_response
            ).strip()
        return str(assistant_response).strip()

    if is_pdf:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return ""

        try:
            reader = PdfReader(BytesIO(file_bytes))
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception:
            return ""

    return ""


def extract_text_from_uploaded_file(uploaded_file):
    if not uploaded_file or not uploaded_file.filename:
        return ""

    if not is_valid_file_type(uploaded_file.filename, uploaded_file.mimetype or ""):
        return ""

    file_bytes = uploaded_file.read()
    if not file_bytes or len(file_bytes) > MAX_FILE_SIZE:
        return ""

    return extract_text_from_bytes(uploaded_file.filename, file_bytes, uploaded_file.mimetype or "")


def extract_text_from_document(doc):
    if not doc or not doc.url or not doc.filename:
        return ""

    if not is_valid_file_type(doc.filename):
        return ""

    file_bytes = download_blob_bytes_from_url(doc.url)
    if not file_bytes or len(file_bytes) > MAX_FILE_SIZE:
        return ""
    return extract_text_from_bytes(doc.filename, file_bytes)


@sessoes_bp.route("/caderno/<id>")
def planPage(id):
    try:
        user = session['user']
    except:
        return render_template("plan.html", sessions=[])
    sessao = SessionStudie.query.filter_by(id=id).first()
    documentos = Documento.query.filter_by(sessao=id).all()
    quizzes = Simulado.query.filter_by(sessao=id).all()
    quiz_result = request.args.get("quiz_result")
    quiz_result_id = request.args.get("quiz_id")
    last_quiz = None
    if quiz_result_id:
        last_quiz = Simulado.query.filter_by(id=quiz_result_id).first()
    return render_template(
        "session.html",
        documentos=documentos,
        sessao=sessao,
        quizzes=quizzes,
        last_quiz=last_quiz,
        quiz_result=quiz_result,
    )

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
    
@sessoes_bp.route("/caderno-digital")
def feedSession():
    sessions = SessionStudie.query.filter_by(user=session["user"])
    return render_template("feed-sessions.html", sessions=sessions)

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
            assunto = request.form.get("assunto")


            newSession = SessionStudie(user=user_db.id, assunto=assunto, resumo="", data=data_session, id=str(uuid.uuid4()), revisao=0)
            db.session.add(newSession)
            db.session.commit()

            print("Sessão salva com sucesso")

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

@sessoes_bp.route("/api/get-session/<id>")
def getSession(id):
    sessiondb = SessionStudie.query.filter_by(id=id).first()
    if not sessiondb:
        return jsonify({"msg": "Sessão não encontrada"}), 404
    
    return jsonify({
        "id": sessiondb.id,
        "assunto": sessiondb.assunto,
        "resumo": sessiondb.resumo,
        "data": sessiondb.data
    })

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
    
@sessoes_bp.route("/api/gerar-quiz", methods=["POST"])
def gerarQuiz():
    try:
        
        sessao = request.form.get("sessao")
        print(sessao)
        sessaodb = SessionStudie.query.filter_by(id=sessao).first()
        anotacao = request.form.get("anotacao") or ""
        assunto = request.form.get("assunto")
        arquivo = request.files.get("arquivo_quiz")
        arquivo_texto = ""

        if arquivo and arquivo.filename:
            if not is_valid_file_type(arquivo.filename, arquivo.mimetype or ""):
                return jsonify({"msg": "error", "details": "Formato de arquivo inválido. Use PDF ou imagem."})
            arquivo.seek(0, os.SEEK_END)
            arquivo_size = arquivo.tell()
            arquivo.seek(0)
            if arquivo_size > MAX_FILE_SIZE:
                return jsonify({"msg": "error", "details": "Arquivo muito grande. Máximo 5 MB."})

        documentos = Documento.query.filter_by(sessao=sessao).all()
        documentos_texto = []
        for documento in documentos:
            documento_texto = extract_text_from_document(documento)
            if documento_texto:
                documentos_texto.append(f"Documento {documento.filename}:\n{documento_texto}")

        if arquivo and arquivo.filename:
            usuario_texto = extract_text_from_uploaded_file(arquivo)
            if usuario_texto:
                documentos_texto.insert(0, f"Arquivo enviado pelo usuário {arquivo.filename}:\n{usuario_texto}")

        if documentos_texto:
            arquivo_texto = "\n\n".join(documentos_texto)
            arquivo_texto = arquivo_texto[:2500] + ("\n... (texto truncado)" if len(arquivo_texto) > 2500 else "")

        anotacao_limp = normalize_text(anotacao)
        if not anotacao_limp and not arquivo_texto:
            return jsonify({"msg": "error", "details": "Envie uma anotação ou um arquivo válido para gerar o quiz."})
        if anotacao_limp and len(anotacao_limp) < 20 and not arquivo_texto:
            return jsonify({"msg": "error", "details": "Anotação muito curta. Escreva pelo menos 20 caracteres ou envie um arquivo válido."})

        prompt_content = [
            f"Assunto: {assunto}.",
            f"Anotação: {anotacao}."
        ]
        if arquivo and arquivo.filename:
            prompt_content.append(f"Arquivo enviado: {arquivo.filename}.")
        if documentos and not arquivo_texto:
            prompt_content.append(f"{len(documentos)} arquivo(s) já estão salvos na sessão e devem ser considerados para a criação do quiz.")
        if arquivo_texto:
            prompt_content.append("Conteúdo extraído dos arquivos:")
            prompt_content.append(arquivo_texto)
        prompt_content.append("Use todas as informações disponíveis — especialmente a anotação do aluno — para criar questões de múltipla escolha no estilo ENEM com resolução detalhada.")

        chat_completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": """
                Você é um gerador de simulado para ENEM.
                Sua função é criar 5 perguntas com base nas informações que o usuário mandar, e retornar nesse formato em JSON:
                 
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
                {"role": "user", "content": " ".join(prompt_content)}
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
            resolucao=assistant_response["pergunta1"]["resolucao"],  
            quiz=newQuiz.id
        )

        db.session.add(new_pergunta)
        db.session.commit()

        new_pergunta = Pergunta(
            id=str(uuid.uuid4()),
            questao=assistant_response["pergunta2"]["pergunta"],
            resposta_certa=assistant_response["pergunta2"]["respostaCerta"],
            alternativas=assistant_response["pergunta2"]["alternativas"],
            resolucao=assistant_response["pergunta2"]["resolucao"], 
            quiz=newQuiz.id
        )

        db.session.add(new_pergunta)
        db.session.commit()

        new_pergunta = Pergunta(
            id=str(uuid.uuid4()),
            questao=assistant_response["pergunta3"]["pergunta"],
            resposta_certa=assistant_response["pergunta3"]["respostaCerta"],
            alternativas=assistant_response["pergunta3"]["alternativas"],
            resolucao=assistant_response["pergunta3"]["resolucao"],  
            quiz=newQuiz.id
        )

        db.session.add(new_pergunta)
        db.session.commit()

        new_pergunta = Pergunta(
            id=str(uuid.uuid4()),
            questao=assistant_response["pergunta4"]["pergunta"],
            resposta_certa=assistant_response["pergunta4"]["respostaCerta"],
            alternativas=assistant_response["pergunta4"]["alternativas"],
            resolucao=assistant_response["pergunta4"]["resolucao"],  
            quiz=newQuiz.id
        )

        db.session.add(new_pergunta)
        db.session.commit()

        new_pergunta = Pergunta(
            id=str(uuid.uuid4()),
            questao=assistant_response["pergunta5"]["pergunta"],
            resposta_certa=assistant_response["pergunta5"]["respostaCerta"],
            alternativas=assistant_response["pergunta5"]["alternativas"],
            resolucao=assistant_response["pergunta5"]["resolucao"],
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


@sessoes_bp.route("/enviar_respostas/<id>", methods=["POST"])
def enviar_respostas(id):
    quiz = Simulado.query.filter_by(id=id).first()
    if not quiz:
        return "Quiz não encontrado", 404

    perguntas = Pergunta.query.filter_by(quiz=quiz.id).all()
    respostas = {}
    for key, value in request.form.items():
        if key.startswith("resposta[") and key.endswith("]"):
            try:
                index = int(key[len("resposta["):-1])
            except ValueError:
                continue
            respostas[index] = value

    total_acertos = 0
    for idx, pergunta in enumerate(perguntas):
        resposta_enviada = respostas.get(idx, "").strip()
        if not resposta_enviada:
            continue

        correta = pergunta.resposta_certa or ""
        options = [opt.strip() for opt in pergunta.alternativas.split("/") if opt.strip()]
        norm_correta = normalize_text(correta)
        norm_resposta = normalize_text(resposta_enviada)

        acertou = False
        if norm_resposta and norm_resposta == norm_correta:
            acertou = True
        else:
            correta_letra = extract_letter(correta)
            if not correta_letra:
                for index, opt in enumerate(options):
                    if normalize_text(opt) == norm_correta:
                        correta_letra = extract_letter(opt) or chr(97 + index)
                        break

            resposta_letra = extract_letter(resposta_enviada)
            if not resposta_letra:
                for index, opt in enumerate(options):
                    if normalize_text(opt) == norm_resposta:
                        resposta_letra = extract_letter(opt) or chr(97 + index)
                        break

            if resposta_letra and correta_letra and resposta_letra == correta_letra:
                acertou = True

        if acertou:
            total_acertos += 1

    quiz.acertos = total_acertos
    quiz.views = (quiz.views or 0) + 1
    db.session.commit()

    return redirect(f"/caderno/{quiz.sessao}?quiz_result={total_acertos}&quiz_id={quiz.id}")


@sessoes_bp.route("/api/delete-doc/<id>", methods=["POST"])
def delete_doc(id):
    doc = Documento.query.filter_by(id=id).first()
    if not doc:
        return jsonify({"msg": "Documento não encontrado"}), 404
    db.session.delete(doc)
    db.session.commit()
    return jsonify({"msg": "success"})

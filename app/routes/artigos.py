# Importação dos módulos e classes necessárias
from flask import render_template, redirect, session, jsonify, request, make_response, send_file
from app.routes import artigos_bp
from app.models import Corrections, SessionStudie, Simulado
from app import db
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
if azure_endpoint is None:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set.")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-07-01-preview",
    azure_endpoint=azure_endpoint
)

@artigos_bp.route("/")
def homepage():
    
    try:
        user = session['user']
        correcoes = Corrections.query.filter_by(user=user).all()
        sessoes = SessionStudie.query.filter_by(user=user).all()
        quiz = Simulado.query.filter_by(user=user).all()

        return render_template("index.html", user=user, correcoes=correcoes, sessoes=sessoes, quiz=quiz)
    except Exception as e:
        return render_template("login.html")

from datetime import datetime


@artigos_bp.route("/download-file/<filename>")
def download_file(filename):
    directory_path = os.path.abspath("instance")
    file_path = os.path.join(directory_path, filename)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "Arquivo não encontrado", 404

from PIL import Image
import base64
import io

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

@artigos_bp.route("/api/carregar-redacao", methods=["POST"])
def carregar_redacao():
    try:
        if 'foto' not in request.files or not request.files['foto'].filename:
            return jsonify({"msg": "Nenhum arquivo enviado"}), 400

        foto = request.files['foto']
        filename = foto.filename
        image_path = os.path.join('/tmp', filename)
        foto.save(image_path)

        img_base64 = image_to_base64(image_path)

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Transcreva apenas o texto da redação manuscrita da imagem enviada, sem comentários, explicações ou introduções. Retorne somente o texto."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Transcreva o texto da imagem."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ]
        )

        texto_extraido = chat_completion.choices[0].message.content.strip()

        return jsonify({"msg": "success", "redacao": texto_extraido})

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

@artigos_bp.route("/api/gerar-artigo", methods=["POST"])
def gerar_artigo():
    try:
        if 'foto' not in request.files or not request.files['foto'].filename:
            return jsonify({"msg": "Nenhum arquivo enviado"}), 400

        foto = request.files['foto']
        filename = foto.filename
        image_path = os.path.join('/tmp', filename)
        foto.save(image_path)

        img_base64 = image_to_base64(image_path)

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Gere apenas o artigo completo, estruturado e informal, a partir do conteúdo manuscrito da imagem enviada. Não inclua comentários, explicações ou introduções. Retorne somente o artigo. Não deixe referências a imagem, ou seja, apenas o conteúdo do artigo, faz de conta que nem te enviaram uma imagem."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Gere o artigo a partir do texto manuscrito da imagem."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ]
        )

        content = chat_completion.choices[0].message.content
        texto_extraido = content.strip() if content else ""

        return jsonify({"msg": "success", "artigo": texto_extraido})

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"msg": "error", "error": str(e)}), 500

    finally:
        if os.path.exists(image_path):
            os.remove(image_path)


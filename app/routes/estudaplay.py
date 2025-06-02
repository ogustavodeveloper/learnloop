# Importação dos módulos e classes necessárias
from flask import render_template, redirect, session, jsonify, request, make_response, send_file
from app.routes import estudaplay_bp
from app.models import Artigo, User, buscas, VideoYt
from app import db
from passlib.hash import bcrypt_sha256
import uuid
import markdown
import os
from docx import Document
from sqlalchemy import desc
from openai import AzureOpenAI
from dotenv import load_dotenv

import re

load_dotenv()

azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
if azure_endpoint is None:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set.")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-07-01-preview",
    azure_endpoint=azure_endpoint
)

from googleapiclient.discovery import build
import re

# Sua chave da API já definida no código ou importada do ambiente seguro
API_KEY = os.getenv("API_YT")

def obter_dados_video(video_url: str, max_comentarios: int = 10) -> str:
    """Retorna string formatada com título, descrição e comentários do vídeo do YouTube"""

    # Validação da chave de API
    if not API_KEY or len(API_KEY) < 30 or API_KEY.count("AIza") > 1:
        return "❌ Erro de configuração: chave da API do YouTube inválida ou duplicada."

    # Extrair ID do vídeo
    match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', video_url)
    if not match:
        return "❌ Link inválido: não foi possível extrair o ID do vídeo."

    video_id = match.group(1)

    try:
        # Conectar API
        youtube = build('youtube', 'v3', developerKey=API_KEY)

        # Buscar dados do vídeo
        video_response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()

        if not video_response['items']:
            return "❌ Vídeo não encontrado na API."

        snippet = video_response['items'][0]['snippet']
        titulo = snippet['title']
        descricao = snippet['description']

        # Buscar comentários
        comentarios = []
        comment_response = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            textFormat='plainText',
            maxResults=max_comentarios
        ).execute()

        for item in comment_response.get('items', []):
            comentario = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comentarios.append(comentario)

        # Montar string final
        resultado = f"📺 Título:\n{titulo}\n\n📝 Descrição:\n{descricao}\n\n💬 Comentários:"
        if comentarios:
            for i, c in enumerate(comentarios, 1):
                resultado += f"\n{i}. {c}"
        else:
            resultado += "\nNenhum comentário disponível."

        return resultado

    except Exception as e:
        return f"❌ Erro ao acessar a API do YouTube: {str(e)}"

@estudaplay_bp.route("/feed/videos")
def feedVideoYts():
    VideoYts = VideoYt.query.all()
    return render_template("video-list.html", videos=VideoYts)

@estudaplay_bp.route("/api/publicar-video", methods=["POST"])
def publicarVideoYt():
    try:
        link = request.form.get("video-yt-link")
        titulo = request.form.get("titulo-yt")

        transcricao = obter_dados_video(link)
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", link) # type: ignore
        if not match:
            raise ValueError("URL inválida. Não foi possível extrair o ID do vídeo.")
        video_id = match.group(1)
        print(video_id)
        print(transcricao) 

        chat_completion = client.chat.completions.create(
                    model="gpt-4o-mini",  # Nome do deployment configurado no Azure
                   messages=[
                       {"role": "system", "content": "Você é um assistente de estudos de um vestibulando, e apenas transforma as informações que ele enviar, em um resumo do vídeo/assunto. Com base na descrição, título, e comentários(e aprimore a resposta com base também nos comentários) sem nenhuma referência a nenhum dado enviado pelo usuário."},
                     {"role": "user", "content": f"Informações: {transcricao}"}
                   ]
                )

        assistant_response = chat_completion.choices[0].message.content

        new_video = VideoYt(id=str(uuid.uuid4()), titulo=titulo, resumo=assistant_response, transcricao=transcricao, id_video=str(video_id))
        db.session.add(new_video)
        db.session.commit()

        return jsonify({
            "msg": "success"
        })
    
    except Exception as e:
        return jsonify({
            "msg": "error",
            "details": f"{str(e)}"
        })

@estudaplay_bp.route("/video/<id>")
def pageVideoYt(id):
    video = VideoYt.query.filter_by(id=id).first()
    return render_template("video.html", video=video)

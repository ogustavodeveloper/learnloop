from flask import render_template, request, jsonify, session, redirect
from app.routes import feciba_bp 
from app.models import Feciba, User 
import os
from azure.storage.blob import BlobServiceClient
import uuid
from app import db
import markdown

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

@feciba_bp.route("/api/postar-projeto", methods=["POST"])
def postarProjeto():
    try:
        imagem = request.files["imagem"]
        nome_arquivo = imagem.filename if imagem else None
        print(nome_arquivo)
        projeto = request.files["projeto"]
        nome_projeto = projeto.filename if projeto else None
        participantes = request.form["participantes"]
        tags = request.form["tags"]

        if not imagem or not projeto:
            return jsonify({"error": "Imagem ou projeto não foram fornecidos."}), 400

        caminho_imagem_temp = os.path.join("/tmp", nome_arquivo)
        imagem.save(caminho_imagem_temp)

        caminho_projeto_temp = os.path.join("/tmp", nome_projeto)
        projeto.save(caminho_projeto_temp)
      
        imagem_az = upload_to_azure_blob("learnloop-img", caminho_imagem_temp, nome_arquivo)
        projeto_az = upload_to_azure_blob("learnloop-projetos", caminho_projeto_temp, nome_projeto)

        # Salvar tudo no banco de dados 
        feciba = Feciba(title=request.form["title"], resumo=markdown.markdown(request.form["resumo"]), id=str(uuid.uuid4()), image_url=imagem_az, project_url=projeto_az, author=session["user"], participantes=participantes, tags=tags)
        db.session.add(feciba)
        db.session.commit()

        return redirect(f"/projeto/{feciba.id}")

    except Exception as e:
        return jsonify({"error": f"Erro ao postar o projeto: {e}"}), 500



                                      
@feciba_bp.route("/api/deletar-projeto/<id>")
def deletarProjeto(id):
  try:
    projeto = Feciba.query.filter_by(id=id).first()
    db.session.delete(projeto)
    db.session.commit()
    return redirect("/")
  except Exception as e:
    print(f"erro: {e}")

@feciba_bp.route("/feciba-add")
def pageFecibaAdd():
  return render_template("feciba-add.html")

@feciba_bp.route("/feciba-mostra")
def mostraFeciba():
  projetos = Feciba.query.all()
  return render_template("feciba-mostra.html", projetos=projetos)

@feciba_bp.route("/projeto/<id>")
def pageProjeto(id):
    try:
      projeto = Feciba.query.filter_by(id=id).first()
      btnExcluir = f"<a href='/api/deletar-projeto/{projeto.id}'><button>Excluir Projeto</button></a>"
      if session["user"] == projeto.author:
          return render_template("projeto.html", projeto=projeto, btnExcluir=btnExcluir)
      else:
          return render_template("projeto.html", projeto=projeto, btnExcluir="")
    except Exception as e:
        print(f"erro: {e}")
        return redirect("/login")
        

from app.routes import repertorio_bp 
from flask import render_template, request, jsonify, session, redirect
from app.models import Repertorio, User, db
from azure.storage.blob import BlobServiceClient
import os 
import uuid 

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

@repertorio_bp.route("/publicar-repertorio", methods=["POST", "GET"])
def publicar_repertorio():
    if request.method == "POST":
        data = request.form 
        titulo = data.get("nome")
        arquivo = request.files.get("arquivo")
        eixos = data.get("eixos")
        autor = data.get("autor")
        user = session.get("user")

        # Arquivo opcional
        new_arquivo = None
        if arquivo and arquivo.filename:
            caminho = os.path.join("/tmp", arquivo.filename)
            arquivo.save(caminho)
            new_arquivo = upload_to_azure_blob("repertorio", caminho, arquivo.filename)

        capa = request.files.get("capa")
        caminho_capa = os.path.join("/tmp", capa.filename)
        capa.save(caminho_capa)
        new_capa = upload_to_azure_blob("repertorio-capa", caminho_capa, capa.filename)
        
        new_repertorio = Repertorio(
            titulo=titulo,
            arquivo=new_arquivo,
            eixos=eixos,
            autor=autor,
            user=user,
            id=str(uuid.uuid4()),
            resumo=data.get("resumo"),
            capa=new_capa,
            tipo=data.get("tipo")
        )

        db.session.add(new_repertorio)
        db.session.commit()

        return redirect(f"/repertorio/{new_repertorio.id}")

    return render_template("publicar-repertorio.html")

@repertorio_bp.route("/repertorio/<id>")
def exibirRepertorio(id):
    repertorio = Repertorio.query.filter_by(id=id).first()
    return render_template("repertorio.html", repertorio=repertorio)

@repertorio_bp.route("/repertorios")
def repertorios():
    repertorios = Repertorio.query.all()
    tipos = ["livro", "filme", "serie", "podcast", "outro"]
    agrupados = {tipo: [] for tipo in tipos}
    for r in repertorios:
        # Se não tiver tipo, coloca em "outro"
        tipo = getattr(r, "tipo", None) or "outro"
        if tipo not in agrupados:
            agrupados["outro"].append(r)
        else:
            agrupados[tipo].append(r)
    return render_template("list-repertorio.html", repertorios_por_tipo=agrupados)
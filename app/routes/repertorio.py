from app.routes import repertorio_bp 
from flask import render_template, request, jsonify, session, redirect
from app.models import Repertorio, User, db
from azure.storage.blob import BlobServiceClient
import os 
import uuid 

def upload_to_azure_blob(container_name, file_path, blob_name):
    try:
        # Obter a connection string dos segredos (variável de ambiente)
        connection_string = os.getenv('CONECTION') or os.getenv('AZURE_STORAGE_CONNECTION_STRING') or os.getenv('AZURE_STORAGE_CONNECTION')
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

        unique_blob_name = f"{uuid.uuid4().hex}_{blob_name}"
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=unique_blob_name)

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
        tipo_envio = data.get("tipo_envio")
        arquivo = request.files.get("arquivo") if tipo_envio == "arquivo" else None
        link = data.get("link") if tipo_envio == "link" else None
        eixos = data.get("eixos")
        autor = data.get("autor")
        user = session.get("user")

        if isinstance(user, dict):
            user = user.get("id") or user.get("username")

        new_arquivo = None
        caminho_arquivo = None
        if arquivo and arquivo.filename:
            safe_name = f"{uuid.uuid4().hex}_{os.path.basename(arquivo.filename)}"
            caminho_arquivo = os.path.join("/tmp", safe_name)
            arquivo.save(caminho_arquivo)
            try:
                new_arquivo = upload_to_azure_blob("repertorio", caminho_arquivo, arquivo.filename)
            except Exception as e:
                print(f"Erro upload arquivo repertório: {e}")

        capa = request.files.get("capa")
        new_capa = None
        caminho_capa = None
        if capa and capa.filename:
            safe_capa = f"{uuid.uuid4().hex}_{os.path.basename(capa.filename)}"
            caminho_capa = os.path.join("/tmp", safe_capa)
            capa.save(caminho_capa)
            try:
                new_capa = upload_to_azure_blob("repertorio-capa", caminho_capa, capa.filename)
            except Exception as e:
                print(f"Erro upload capa repertório: {e}")

        new_repertorio = Repertorio(
            id=str(uuid.uuid4()),
            user=user,
            titulo=titulo,
            arquivo=new_arquivo,
            link=link,
            eixos=eixos,
            autor=autor,
            resumo=data.get("resumo"),
            capa=new_capa,
            tipo=data.get("tipo") or "outro",
        )

        try:
            db.session.add(new_repertorio)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar repertório no banco: {e}")
            return render_template("error.html", message="Erro ao salvar repertório")
        finally:
            # Limpa arquivos temporários quando existirem
            try:
                if caminho_arquivo and os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)
                if caminho_capa and os.path.exists(caminho_capa):
                    os.remove(caminho_capa)
            except Exception:
                pass

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
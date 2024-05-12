# Importação dos módulos e classes necessárias
from flask import render_template, redirect, session, jsonify, request, url_for, make_response, send_file
from app.routes import iaplan_bp
from app.models import LearnPlan, SessionStudie, User
from app import db
from passlib.hash import bcrypt_sha256
import uuid
import markdown
import openai 
import os
import datetime

openai.api_key = os.environ["OPENAI"]

@iaplan_bp.route("/plan")
def planPage():
  try:
    user = session['user']
  except:
    return redirect('/login')
  sessoes = SessionStudie.query.filter_by(user=session["user"]).all()
  return render_template("plan.html", sessions=sessoes)



@iaplan_bp.route("/download-db")
def download_file():
    # Diretório onde os documentos do Word estão localizados
    directory_path = os.path.abspath("instance")

    file_path = os.path.join(directory_path, "data-2024-learnloop.db")

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
      data = datetime.date.today()
      resumo = data["resumo"]
      assunto = data["assunto"]
      newSession = SessionStudie(user=user_db.id, assunto= assunto, resumo=resumo, data=data, tempo=tempo, id=str(uuid.uuid4()))
      db.session.add(newSession)
      db.session.commit()

      return jsonify({"msg": "success"})

  except:
      return redirect("/login")

@iaplan_bp.route("/api/delete-session/<id>")
def removeSession(id):
  session = SessionStudie.query.filter_by(id=id).first()
  db.session.delete(session)
  db.session.commit()

  return redirect("/plan")

@iaplan_bp.route("/api/get-resumo-ia", methods=["POST"])
def getResumo():
  try:
    user = session["user"]
    anotacoes = data["notes"]
    user_message = {"role": "user", "content": f"Minhas anotações: {anotacoes}"}

    conversation = [
      {"role": "system", "content": "Você, é uma Inteligência Artificial para estudos, com base nas anotações que o usuário enviar, você deverá criar um resumo bem estruturado do que ele aprendeu"},
      user_message
    ]

    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=conversation
    )

    resposta = response.choices[0].message["content"]

    return ({"msg": resposta})

  except:
    return redirect("/login")

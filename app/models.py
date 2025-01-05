from app import db, app


class User(db.Model):
  id = db.Column(db.String(), primary_key=True)
  username = db.Column(db.String(64), index=True, unique=True)
  password = db.Column(db.String())
  

  def __init__(self, id, username, password):
    self.id = id
    self.username = username
    self.password = password


class Artigo(db.Model):
  id = db.Column(db.String(), primary_key=True)
  titulo = db.Column(db.String(128))
  texto = db.Column(db.String(1024))
  autor = db.Column(db.String(64))
  data = db.Column(db.String(64))
  categoria = db.Column(db.String(64))
  tags = db.Column(db.String(64))
  likes = db.Column(db.Integer)
  views = db.Column(db.Integer)

  def __init__(self, titulo, texto, autor, data, categoria, tags, likes, id, views):
    self.titulo = titulo
    self.texto = texto
    self.autor = autor
    self.data = data
    self.categoria = categoria
    self.tags = tags
    self.likes = likes
    self.id = id
    self.views = views

class Material(db.Model):
  id = db.Column(db.String(), primary_key=True)
  nome = db.Column(db.String(255))
  link = db.Column(db.String())
  autor = db.Column(db.String())

class buscas(db.Model):
  user = db.Column(db.String())
  termo = db.Column(db.String())
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)

  def __init__(self, user, termo):
    self.user = user
    self.termo = termo

class SessionStudie(db.Model):
  user = db.Column(db.String())
  assunto = db.Column(db.String())
  resumo = db.Column(db.String())
  id = db.Column(db.String(), primary_key=True)
  data = db.Column(db.String())
  tempo = db.Column(db.String())

  def __init__(self, user, assunto, resumo, data, tempo, id):
    self.user = user
    self.assunto = assunto
    self.resumo = resumo 
    self.data = data
    self.tempo = tempo
    self.id = id

class Redacao(db.Model):
  user = db.Column(db.String())
  titulo = db.Column(db.String())
  texto = db.Column(db.String(), primary_key=True)

  def __init__(self, user, titulo, texto):
    self.user = user 
    self.titulo = titulo 
    self.texto = texto

class Feciba(db.Model):
  title = db.Column(db.String())
  resumo = db.Column(db.String())
  id = db.Column(db.String(), primary_key=True)
  image_url = db.Column(db.String())
  project_url = db.Column(db.String())
  author = db.Column(db.String())
  participantes = db.Column(db.String())
  tags = db.Column(db.String())
  

  def __init__(self, title, resumo, id, image_url, project_url, author, participantes, tags):
    self.title = title 
    self.resumo = resumo 
    self.id = id 
    self.image_url = image_url
    self.project_url = project_url 
    self.author = author
    self.participantes = participantes
    self.tags = tags

class Correcoes(db.Model):
  user = db.Column(db.String())
  titulo = db.Column(db.String())
  texto = db.Column(db.String())
  correcao = db.Column(db.String(), primary_key=True)

  def __init__(self, user, titulo, texto, correcao):
    self.user = user 
    self.titulo = titulo 
    self.texto = texto
    self.correcao = correcao 

class Corrections(db.Model):
  id = db.Column(db.String())
  user = db.Column(db.String())
  tema = db.Column(db.String())
  texto = db.Column(db.String(), primary_key=True)
  cp1 = db.Column(db.String())
  cp2 = db.Column(db.String())
  cp3 = db.Column(db.String())
  cp4 = db.Column(db.String())
  cp5 = db.Column(db.String())
  final = db.Column(db.String())
  data = db.Column(db.String())

  def __init__(self, id, user, tema, texto, cp1, cp2, cp3, cp4, cp5, final, data):
    self.id = id
    self.user = user
    self.tema = tema
    self.texto = texto
    self.cp1 = cp1
    self.cp2 = cp2 
    self.cp3 = cp3 
    self.cp4 = cp4
    self.cp5 = cp5
    self.final = final
    self.data = data 


with app.app_context():
  db.create_all()

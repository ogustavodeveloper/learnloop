from app import db, app


class User(db.Model):
  id = db.Column(db.String(), primary_key=True)
  username = db.Column(db.String(64), index=True, unique=True)
  email = db.Column(db.String())
  password = db.Column(db.String())
  

  def __init__(self, id, username, email, password):
    self.id = id
    self.username = username
    self.email = email
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
  revisao = db.Column(db.Integer())

  def __init__(self, user, assunto, resumo, data, id, revisao):
    self.user = user
    self.assunto = assunto
    self.resumo = resumo 
    self.data = data 
    self.id = id
    self.revisao = revisao 

class Redacao(db.Model):
  user = db.Column(db.String())
  titulo = db.Column(db.String())
  texto = db.Column(db.String(), primary_key=True)

  def __init__(self, user, titulo, texto):
    self.user = user 
    self.titulo = titulo 
    self.texto = texto

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


class Documento(db.Model):
  id = db.Column(db.String(), primary_key=True)
  filename = db.Column(db.String())
  url = db.Column(db.String())
  sessao = db.Column(db.String())

  def __init__(self, id, filename, url, sessao):
    self.id = id 
    self.filename = filename 
    self.url = url 
    self.sessao = sessao 

class Simulado(db.Model):
  id = db.Column(db.String(), primary_key=True)
  titulo = db.Column(db.String())
  sessao = db.Column(db.String())
  user = db.Column(db.String())
  views = db.Column(db.Integer, default=0)
  acertos = db.Column(db.Integer, default=0)


  def __init__(self, id, titulo, sessao, user, views, acertos):
    self.id = id
    self.titulo = titulo
    self.sessao = sessao 
    self.user = user
    self.views = views
    self.acertos = acertos
  
class Pergunta(db.Model):
  id = db.Column(db.String(), primary_key=True)
  questao = db.Column(db.String())
  resposta_certa = db.Column(db.String())
  alternativas = db.Column(db.String())
  quiz = db.Column(db.String())
  resolucao = db.Column(db.String())

  def __init__(self, id, questao, resposta_certa, alternativas, quiz, resolucao):
    self.id = id
    self.questao = questao 
    self.resposta_certa = resposta_certa
    self.alternativas = alternativas 
    self.quiz = quiz
    self.resolucao = resolucao 

class VideoYt(db.Model):
  id = db.Column(db.String(), primary_key=True)
  titulo = db.Column(db.String())
  resumo = db.Column(db.String())
  transcricao = db.Column(db.String())
  id_video = db.Column(db.String())

  def __init__(self, id, titulo, resumo, transcricao, id_video):
    self.id = id
    self.titulo = titulo 
    self.resumo = resumo
    self.transcricao = transcricao 
    self.id_video = id_video

class Revisoes(db.Model):
  id = db.Column(db.String(), primary_key=True)
  user = db.Column(db.String())
  assunto = db.Column(db.String())
  data = db.Column(db.DateTime)
  status = db.Column(db.String())
  id_session = db.Column(db.String())

  def __init__(self, id, user, assunto, data, status, id_session):
    self.id = id
    self.user = user
    self.assunto = assunto
    self.data = data
    self.status = status
    self.id_session = id_session

class Repertorio(db.Model):
  id = db.Column(db.String(), primary_key=True)
  user = db.Column(db.String())
  titulo = db.Column(db.String())
  arquivo = db.Column(db.String())
  link = db.Column(db.String())  # Novo campo
  eixos = db.Column(db.String())
  autor = db.Column(db.String())
  resumo = db.Column(db.Text)
  capa = db.Column(db.String())
  tipo = db.Column(db.String(), default="outro")
  
  def __init__(self, id, user, titulo, arquivo, link, eixos, autor, resumo, capa, tipo):
    self.id = id
    self.user = user
    self.titulo = titulo 
    self.arquivo = arquivo 
    self.link = link
    self.eixos = eixos 
    self.autor = autor 
    self.resumo = resumo 
    self.capa = capa
    self.tipo = tipo
    
class Avaliacao(db.Model):
  id = db.Column(db.String(), primary_key=True)
  tipo = db.Column(db.String())
  nota = db.Column(db.Float())
  comentario = db.Column(db.String())
  user = db.Column(db.String())
  correcao_id = db.Column(db.String())
  
  def __init__(self, id, tipo, nota, comentario, user, correcao_id):
    self.id = id
    self.tipo = tipo
    self.nota = nota
    self.comentario = comentario
    self.user = user
    self.correcao_id = correcao_id 
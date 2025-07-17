from flask import render_template, request, session, jsonify, redirect, make_response, Response
from app import db
from app.models import User, Artigo, Redacao, buscas, Corrections
from app.routes import geral_bp
from datetime import datetime
import markdown

# Rota para termos de uso
@geral_bp.route("/termos-de-uso")
def termosDeUso():
    return render_template("termos.html")

# Rota para política de privacidade
@geral_bp.route("/politica-de-privacidade")
def politicaPrivacidade():
    return render_template("privacidade.html")

# Rota sobre a página
@geral_bp.route("/sobre")
def sobrePage():
    return render_template("sobre.html")

# Rota de contato
@geral_bp.route("/contato")
def contatoPage():
    return render_template("contato.html")

# Rota guia
@geral_bp.route("/guia")
def guia():
    return render_template("guia.html")

# Rota para o cadastro de usuário
@geral_bp.route("/cadastro")
def cadastroPage():
    return render_template("signup.html")

# Rota para login de usuário
@geral_bp.route("/login")
def loginPage():
    return render_template("login.html")


@geral_bp.route('/sitemap.xml')
def sitemap():
    artigos = Artigo.query.all()
    
    # Gerar as URLs e incluir a data formatada para cada artigo
    urls = []
    for artigo in artigos:
        # Formatar a data de criação do artigo no formato ISO 8601
        data_criacao = datetime.strptime(artigo.data, '%Y-%m-%dT%H:%M:%S+00:00').strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        # Adicionar a URL e a data formatada à lista de URLs
        urls.append({
            'loc': f"https://learnloop.com.br/artigo/{artigo.id}",
            'lastmod': data_criacao
        })

    # Renderizar o sitemap.xml usando o template, passando as URLs
    sitemap_xml = render_template('sitemap.xml', urls=urls)
    
    # Criar a resposta e definir o cabeçalho Content-Type para 'application/xml'
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response

# Rota para o painel de administração
@geral_bp.route('/admin/28092007')
def admin_panel():
    users = User.query.all()
    searches = buscas.query.all()
    articles = Artigo.query.all()
    correcoes = Corrections.query.all()
    
    return render_template('admin.html', users=users, searches=searches, articles=articles, correcoes=correcoes)

# Rota para excluir um artigo
@geral_bp.route('/delete_article')
def delete_article():
    artigos = Artigo.query.all()
    for art in artigos:
        db.session.delete(art)
        db.session.commit()

    return "todos deletados."





# Rota para o arquivo robots.txt
@geral_bp.route('/robots.txt')
def robots_txt():
    robots_txt_content = """
    User-agent: *
    Disallow: /admin/
    Disallow: /user/
    Disallow: /settings/
    Disallow: /private/

    User-agent: Googlebot
    Allow: /public/

    Sitemap: https://learnloop.site/sitemap.xml
    """
    return Response(robots_txt_content, mimetype='text/plain')

from openai import AzureOpenAI
import os
import json 


azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
if azure_endpoint is None:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set.")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-07-01-preview",
    azure_endpoint=azure_endpoint
)

@geral_bp.route('/radar-conhecimento')
def radar_conhecimento():
    return render_template("radar-conhecimento.html")

@geral_bp.route('/api/gerar-radar', methods=['POST'])
def gerar_radar():
    data = request.get_json()
    
    curso = data.get('curso')
    faculdade = data.get('faculdade')
    
    chat_completion = client.chat.completions.create(
            model="gpt-4o",  # Nome do deployment configurado no Azure
            messages=[
                {"role": "system", "content": """
                Você é um assistente especializado em gerar 20 questões de múltipla escolha para o ENEM, com foco em quatro áreas: Matemática, Ciências da Natureza, Ciências Humanas e Linguagens.
                O estudante deseja fazer um simulado diagnóstico para o ENEM 2025, respondendo a 20 perguntas divididas igualmente entre as quatro áreas.
                Cada pergunta deve conter uma pergunta clara e objetiva, quatro alternativas (A, B, C, D) e uma resposta correta.
                As perguntas devem ser de nível básico a intermediário, adequadas para o ENEM, e devem abranger os principais tópicos de cada área.
                O estudante deve saber o básico e intermediário de cada área.
                Assuntos que devem estar presentes nas questões:
                Matemática: Equação de primeiro e segundo grau, estatística básica, geometria plana e espacial, funções, porcentagem, juros simples e compostos.
                Ciências da Natureza: Física básica (mecânica, termodinâmica), química básica (ligações químicas, reações), biologia básica (ecologia, genética).
                Ciências Humanas: História do Brasil (colonização, império, república), geografia do Brasil (climas, relevo, hidrografia), filosofia e sociologia básica (direitos humanos, cidadania).
                Linguagens: Interpretação de texto, gramática básica (ortografia, concordância), literatura brasileira (movimentos literários, autores clássicos), artes (música, artes visuais).
                
                A resposta deve ser um JSON com o seguinte formato:
 
 {
    "pergunta1": {
        "area": "Matemática", 
        "pergunta": pergunta gerada,
        "alternativas": alternativas separadas em /,
        "respostaCerta": alternativa certa
    },
    ...
 }
 
não coloque explicações, apenas o JSON
      
                """},
                {"role": "user", "content": f"Curso que o estudante deseja cursar: {curso}. Faculdade: {faculdade}."}
            ],
            temperature=0.1,
            top_p=1.0
        )
    # Extrair a resposta do assistente e remover quebras de linha e formatação JSON
    print(chat_completion.choices[0].message.content)
    assistant_response = chat_completion.choices[0].message.content.replace('\n', '').replace('json', '').replace('`','')
    assistant_response = json.loads(assistant_response)
    
    print(assistant_response)
    
    return jsonify({
        "msg": "success",
        "questoes": assistant_response
    })

@geral_bp.route('/api/corrigir-radar', methods=['POST'])
def corrigir_radar():
    data = request.get_json()
    respostas = data.get('respostas')
    questoes = data.get('questoes')
    curso = data.get('curso', '')
    faculdade = data.get('faculdade', '')

    # Calcula acertos por área
    acertos = {"Matemática":0, "Ciências da Natureza":0, "Ciências Humanas":0, "Linguagens":0}
    total = {"Matemática":0, "Ciências da Natureza":0, "Ciências Humanas":0, "Linguagens":0}
    for key in questoes:
        q = questoes[key]
        resposta_certa = q['respostaCerta'].strip()
        resposta_usuario = respostas.get(key, '').strip()
        area = q.get('area', '')  # Usa o campo area da questão
        if area not in acertos:
            continue  # Ignora áreas desconhecidas
        total[area] += 1
        if resposta_usuario == resposta_certa:
            acertos[area] += 1

    # Monta histórico detalhado para IA
    historico = []
    for key in questoes:
        q = questoes[key]
        resposta_usuario = respostas.get(key, '')
        historico.append({
            "numero": key,
            "area": q.get('area', ''),
            "pergunta": q['pergunta'],
            "alternativas": q['alternativas'],
            "resposta_certa": q['respostaCerta'],
            "resposta_usuario": resposta_usuario
        })

    # Prompt padronizado para relatório
    prompt = f"""
    Você é um orientador educacional especialista em ENEM.
    Um estudante fez um simulado diagnóstico para o ENEM 2025, respondendo a 20 perguntas divididas em quatro áreas: Matemática, Ciências da Natureza, Ciências Humanas e Linguagens.

    O aluno deseja cursar: {curso}
    Faculdade desejada: {faculdade}
    
    Assuntos que devem estar presentes nas questões:
                Matemática: Equação de primeiro e segundo grau, estatística básica, geometria plana e espacial, funções, porcentagem, juros simples e compostos.
                Ciências da Natureza: Física básica (mecânica, termodinâmica), química básica (ligações químicas, reações), biologia básica (ecologia, genética).
                Ciências Humanas: História do Brasil (colonização, império, república), geografia do Brasil (climas, relevo, hidrografia), filosofia e sociologia básica (direitos humanos, cidadania).
                Linguagens: Interpretação de texto, gramática básica (ortografia, concordância), literatura brasileira (movimentos literários, autores clássicos), artes (música, artes visuais).

    Aqui está o histórico do simulado do estudante (lista de perguntas, alternativas, resposta correta e resposta do aluno):
    {historico}

    Gere um relatório objetivo e organizado sobre o desempenho do aluno, focando exclusivamente no ENEM e considerando o curso e faculdade desejados.
    O estudante deve saber o básico e intermediário de cada área, mas não o avançado, para que ele possa passar pelo menos com a TRI.
    O relatório deve ser um JSON com o seguinte formato, sem comentários ou explicações extras:

    {{
        "Matemática": {{
            "assuntos_sabendo": ["assunto1", "assunto2"],
            "assuntos_nao_sabendo": ["assunto3", "assunto4"],
            "recomendacoes": "Texto curto e direto para esta área."
        }},
        "Ciências da Natureza": {{
            "assuntos_sabendo": [],
            "assuntos_nao_sabendo": [],
            "recomendacoes": ""
        }},
        "Ciências Humanas": {{
            "assuntos_sabendo": [],
            "assuntos_nao_sabendo": [],
            "recomendacoes": ""
        }},
        "Linguagens": {{
            "assuntos_sabendo": [],
            "assuntos_nao_sabendo": [],
            "recomendacoes": ""
        }}
    }}

    Preencha todos os campos, mesmo que estejam vazios. Não inclua nada fora do JSON.
    """

    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um orientador educacional especialista em ENEM."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        top_p=1.0
    )
    relatorio = chat_completion.choices[0].message.content.replace('\n', '').replace('json', '').replace('`','')
    print(relatorio)
    try:
        relatorio_json = json.loads(relatorio)
    except Exception as e:
        print("Erro ao processar o relatório:", e)
        relatorio_corrigido = relatorio.replace("'", '"')
        try:
            relatorio_json = json.loads(relatorio_corrigido)
        except Exception as e2:
            print("Erro ao tentar corrigir o relatório:", e2)
            relatorio_json = {
                "Matemática": {"assuntos_sabendo": [], "assuntos_nao_sabendo": [], "recomendacoes": ""},
                "Ciências da Natureza": {"assuntos_sabendo": [], "assuntos_nao_sabendo": [], "recomendacoes": ""},
                "Ciências Humanas": {"assuntos_sabendo": [], "assuntos_nao_sabendo": [], "recomendacoes": ""},
                "Linguagens": {"assuntos_sabendo": [], "assuntos_nao_sabendo": [], "recomendacoes": ""}
            }

    # Garante que todos os campos estejam presentes
    areas = ["Matemática", "Ciências da Natureza", "Ciências Humanas", "Linguagens"]
    for area in areas:
        if area not in relatorio_json:
            relatorio_json[area] = {"assuntos_sabendo": [], "assuntos_nao_sabendo": [], "recomendacoes": ""}
        else:
            for campo in ["assuntos_sabendo", "assuntos_nao_sabendo", "recomendacoes"]:
                if campo not in relatorio_json[area]:
                    relatorio_json[area][campo] = [] if "assuntos" in campo else ""

    return jsonify({
        "relatorio": relatorio_json
    })
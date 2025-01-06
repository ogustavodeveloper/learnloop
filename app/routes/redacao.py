from app.routes import redacao_bp
from app import db
from flask import render_template, redirect, session, jsonify, request, url_for, make_response

from openai import AzureOpenAI
from dotenv import load_dotenv
import uuid
import markdown
import os

from app.models import Artigo, User, buscas, Redacao, Corrections
import uuid
import json
from datetime import datetime
import markdown

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

@redacao_bp.route("/avaliar-redacao")
def redacionPage():
    try:
        user = session["user"]
        redacoes = Corrections.query.filter_by(user=user).all()
        return render_template("treino-redacao.html", redacoes=redacoes)
    except Exception as e:
        return render_template("treino-redacao.html", redacoes=[])


@redacao_bp.route("/learn-ai/redacao", methods=["POST"])
def gerarAvaliacaoPorIa():
    try:
        user = session.get("user")
        if not user:
            return redirect('/login')
        
        data = request.get_json()
        nivel = data.get("nivel")
        tema = data.get("tema")
        conteudo = data.get("content")
        titulo = data.get("title")

        # Verifica se todos os campos necessários foram preenchidos
        if not all([nivel, tema, conteudo]):
            return jsonify({"msg": "error", "details": "Dados insuficientes para avaliação"}), 400

        # Fazendo a chamada à API do Azure OpenAI
        chat_completion = client.chat.completions.create(
    model="gpt-4o",  # Nome do deployment configurado no Azure
    messages=[
        {"role": "system", "content": """
            Você é um assistente de IA especializado na correção de redações com base nos critérios do ENEM. Sua tarefa é avaliar a redação fornecida e gerar uma análise detalhada para cada competência do exame. A avaliação deve ser rigorosa e equilibrada, garantindo que todos os aspectos da redação sejam considerados de maneira justa e precisa. Considere sempre o contexto geral da redação e evite penalizações desnecessárias ou irrelevantes. Baseie-se exclusivamente nos critérios estabelecidos, comparando com redações nota MIL para referência. A pontuação e a análise devem refletir o desempenho real do texto. Sua saída deve ser exclusivamente no formato JSON, mas certifique-se de que as análises sejam detalhadas, sem priorizar o formato em detrimento da qualidade.

            Exemplo de formato JSON:
            {
                "competencia1": {
                    "nota": 100,
                    "analise": "Análise do domínio da modalidade escrita formal da língua portuguesa. Penalize se houver erros de ortografia, concordância verbal e nominal, pontuação inadequada ou uso incorreto da norma culta."
                },
                "competencia2": {
                    "nota": 120,
                    "analise": "Análise da capacidade de compreender a proposta de redação e desenvolver o tema de maneira clara, dentro dos limites do formato dissertativo-argumentativo. Penalize se o tema não for abordado de forma adequada ou se o desenvolvimento for superficial."
                },
                "competencia3": {
                    "nota": 140,
                    "analise": "Análise da organização e interpretação das informações, fatos, opiniões e argumentos. A argumentação deve ser clara, bem estruturada e coerente. Penalize falhas na lógica ou na articulação das ideias."
                },
                "competencia4": {
                    "nota": 120,
                    "analise": "Análise do uso adequado dos mecanismos linguísticos, como coesão, coerência e conectivos. Penalize se a redação apresentar falhas de coesão ou desconexão entre as ideias."
                },
                "competencia5": {
                    "nota": 100,
                    "analise": "Análise da proposta de intervenção. A proposta deve ser clara, viável e detalhada, respeitando os direitos humanos. Penalize se a proposta for vaga, irrealista ou não abordar adequadamente a solução do problema."
                },
                "notaFinal": {
                    "nota": 500,
                    "analise": "Descrição geral do desempenho da redação, considerando as cinco competências. A nota final deve refletir a soma das notas das competências, com penalizações para falhas em aspectos essenciais como coesão, argumentação, adequação ao tema e proposta de intervenção."
                }
            }
        """},
        {"role": "user", "content": f"Título: {titulo}. Tema: {tema}. Redação: {conteudo}"}
    ],
    temperature=0.2,
    top_p=0.7
)

        assistant_response = chat_completion.choices[0].message.content.replace('\n', '').replace('json', '').replace('`','')
        print(assistant_response)
        # Converte o JSON de resposta em um dicionário de forma segura
        try:
            response_data = json.loads(assistant_response)
            print(response_data)
        except json.JSONDecodeError:
            return jsonify({"msg": "error", "details": "Erro ao processar a resposta da IA"}), 500

        # Formata cada competência como "nota\analise"
        cp1 = f"{response_data.get('competencia1', {}).get('nota', 0)}\\{response_data.get('competencia1', {}).get('analise', '')}"
        cp2 = f"{response_data.get('competencia2', {}).get('nota', 0)}\\{response_data.get('competencia2', {}).get('analise', '')}"
        cp3 = f"{response_data.get('competencia3', {}).get('nota', 0)}\\{response_data.get('competencia3', {}).get('analise', '')}"
        cp4 = f"{response_data.get('competencia4', {}).get('nota', 0)}\\{response_data.get('competencia4', {}).get('analise', '')}"
        cp5 = f"{response_data.get('competencia5', {}).get('nota', 0)}\\{response_data.get('competencia5', {}).get('analise', '')}"
        final = f"{response_data.get('notaFinal', {}).get('nota', 0)}\\{response_data.get('notaFinal', {}).get('analise', '')}"

        # Cria uma nova entrada de correção no banco de dados
        new_correction = Corrections(
            id=str(uuid.uuid4()),
            user=user,
            tema=tema,
            texto=conteudo,
            cp1=cp1,
            cp2=cp2,
            cp3=cp3,
            cp4=cp4,
            cp5=cp5,
            final=final,
            data=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        db.session.add(new_correction)
        db.session.commit()

        return jsonify({
            "msg": "success",
            "response": str(new_correction.id)
        })

    except Exception as e:
        # Log da exceção para depuração
        print(f"Erro ao gerar avaliação: {e}")
        return jsonify({"msg": "error", "details": str(e)}), 500

@redacao_bp.route('/redacao')
def redacaoPage():
    try:
      correcoes = Corrections.query.filter_by(user=session['user']).all()

      return render_template('redacoes.html', redacoes=correcoes)
    except Exception as e:
        return redirect("/login")

@redacao_bp.route("/correcao/<id>")
def correcaoPage(id):
    try:
        # Busca a correção no banco de dados pelo ID
        correcao = Corrections.query.filter_by(id=id).first()
        
        # Verifica se a correção foi encontrada
        if not correcao:
            return render_template("redacao-page.html", error="Correção não encontrada.")
        
        # Renderiza o template com a correção
        return render_template("redacao-page.html", correcao=correcao)
    except Exception as e:
        # Em caso de erro, exibe uma mensagem apropriada
        print(f"Erro ao carregar a correção: {e}")
        return render_template("redacao-page.html", error="Erro ao carregar a correção.")

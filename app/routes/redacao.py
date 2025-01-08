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
            Você é um assistente de IA especializado na correção de redações do ENEM, com base nos critérios oficiais estabelecidos. Sua tarefa é:

1. Avaliar a redação fornecida considerando as cinco competências do ENEM:
   - Competência 1: Domínio da norma padrão da língua escrita.
   - Competência 2: Compreensão da proposta e aplicação do formato dissertativo-argumentativo.
   - Competência 3: Seleção, organização e relação de argumentos, fatos e opiniões.
   - Competência 4: Uso de mecanismos linguísticos de coesão e coerência.
   - Competência 5: Elaboração de proposta de intervenção detalhada e respeitosa.

2. Gerar uma análise detalhada para cada competência, destacando pontos fortes e indicando melhorias específicas, sem penalizar excessivamente erros que não impactem significativamente a clareza ou os critérios.

3. Basear-se no desempenho real do texto em comparação com redações nota 1000 do ENEM, garantindo rigor e equilíbrio na avaliação.

4. A saída deve ser em formato JSON, contendo:
   - Nota individual para cada competência (de 0 a 200 pontos).
   - Análise qualitativa detalhada para cada competência.
   - Nota final (soma das notas das competências).
   - Feedback geral destacando os principais pontos positivos e as principais sugestões de melhoria.

Exemplo de saída JSON:
{
    "competencia1": {
        "nota": 200,
        "analise": "O texto apresenta um bom domínio da norma padrão da língua portuguesa, com pequenos deslizes gramaticais que não comprometem a compreensão."
    },
    "competencia2": {
        "nota": 200,
        "analise": "A redação aborda bem o tema proposto, com argumentos relevantes, mas a abordagem poderia ser mais profunda em certos pontos."
    },
    "competencia3": {
        "nota": 180,
        "analise": "Há organização dos argumentos, mas a coesão interna entre alguns parágrafos está comprometida."
    },
    "competencia4": {
        "nota": 180,
        "analise": "Os mecanismos de coesão são bem utilizados, embora alguns conectivos estejam repetitivos."
    },
    "competencia5": {
        "nota": 200,
        "analise": "A proposta de intervenção é clara, detalhada e viável, respeitando os direitos humanos."
    },
    "notaFinal": {
        "nota": 900,
        "analise": "A redação é muito boa, mas pequenos ajustes em coesão e aprofundamento de ideias podem melhorar ainda mais o desempenho."
    }
}
Seja rigoroso, mas justo, e evite exagerar nas penalizações por erros mínimos. Concentre-se na avaliação precisa do desempenho geral.                
        """},
        {"role": "user", "content": f"Título: {titulo}. Tema: {tema}. Redação: {conteudo}"}
    ],
    temperature=0.1,
    top_p=1.0
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

@redacao_bp.route("/api/redacao-guiada", methods=["POST"])
def redacaoGuiada():
    try:
        user = session.get("user")
        if not user:
            return redirect('/login')
        
        data = request.get_json()
        
        texto = data.get("texto")
        
        tema = data.get("tema")

        # Verifica se todos os campos necessários foram preenchidos
        if not all([texto, tema]):
            return jsonify({"msg": "error", "details": "Dados insuficientes para avaliação"}), 400

        # Fazendo a chamada à API do Azure OpenAI
        chat_completion = client.chat.completions.create(
                model="gpt-4o-mini",  # Nome do deployment configurado no Azure
                messages=[
                    {"role": "system", "content": "Você é um assistente na produção de redações para o ENEM, e irá ajudar o usuário a saber o que escrever nas próximas linhas com base no que já foi escrito e de acordo com o tema. Não coloque informações excessivas, apenas as próximas linhas, por exemplo: Se está no começo, ajuda na introdução, identifique em qual parte ele está(introdução, desenvolvimento ou conclusão). Lembre-se: o estudante está perdido! Exemplo de resposta: 'Nas próximas linhas, tente pensar tais coisas...', ofereça um repertório bacana."},
                    {"role": "user", "content": f"Tema: {tema}. Redação: {texto}"}
                ]
            )

        assistant_response = chat_completion.choices[0].message.content
        print(assistant_response)
        return jsonify({
            "msg": "success",
            "guia": assistant_response 
        })
    except Exception as e:
        print(str(e))
        return jsonify({
            "msg": "error",
            "error": str(e)
        })

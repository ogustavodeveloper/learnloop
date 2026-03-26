from app.routes import redacao_bp
from app import db
from flask import render_template, redirect, session, jsonify, request
from openai import OpenAI
import uuid
import json
import os
from datetime import datetime

from app.models import Corrections, Avaliacao

client = OpenAI(
    api_key=os.environ.get("API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

# Helper functions
def clean_json_response(content):
    """Remove markdown artifacts from JSON response"""
    return content.replace('\n', '').replace('json', '').replace('`', '')


def extract_competency_score(response_data, competency_key):
    """Extract and format competency score from response data"""
    data = response_data.get(competency_key, {})
    nota = data.get('nota', 0)
    analise = data.get('analise', '')
    return f"{nota}\\{analise}"

def extract_scores_from_corrections(correcoes):
    """Extract scores and dates from corrections"""
    notas = []
    datas = []
    for c in correcoes:
        try:
            nota = int(str(c.final).split("\\")[0])
            notas.append(nota)
            datas.append(c.data)
        except Exception:
            continue
    return notas, datas

def parse_ai_response(content):
    """Parse and validate AI response JSON"""
    try:
        cleaned = clean_json_response(content)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None

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

        if not all([nivel, tema, conteudo]):
            return jsonify({"msg": "error", "details": "Dados insuficientes para avaliação"}), 400
        
        if len(conteudo) < 60:
            return jsonify({"msg": "error", "details": "Sua redação precisa ser maior!"})

        system_prompt = """Você é um corretor de redações do ENEM. Avalie a redação com base nas 5 competências do ENEM, atribuindo nota (0–200) e um comentário breve (máx. 2 frases) por competência.

Retorne o resultado em JSON com este formato:
{
  "competencia1": {"nota": int, "analise": str},
  "competencia2": {"nota": int, "analise": str},
  "competencia3": {"nota": int, "analise": str},
  "competencia4": {"nota": int, "analise": str},
  "competencia5": {"nota": int, "analise": str},
  "notaFinal": {"nota": int, "analise": str}
}
Seja direto e objetivo."""

        chat_completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Título: {titulo}. Tema: {tema}. Redação: {conteudo}"}
            ],
            temperature=0.1,
            top_p=1.0
        )

        content = chat_completion.choices[0].message.content
        if not content:
            return jsonify({"msg": "error", "details": "A resposta da IA está vazia."}), 500

        response_data = parse_ai_response(content)
        if not response_data:
            return jsonify({"msg": "error", "details": "Erro ao processar a resposta da IA"}), 500

        corrections_data = {
            f"cp{i}": extract_competency_score(response_data, f"competencia{i}")
            for i in range(1, 6)
        }
        corrections_data["final"] = extract_competency_score(response_data, "notaFinal")

        new_correction = Corrections(
            id=str(uuid.uuid4()),
            user=user,
            tema=tema,
            texto=conteudo,
            **corrections_data,
            data=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        db.session.add(new_correction)
        db.session.commit()

        return jsonify({
            "msg": "success",
            "response": str(new_correction.id)
        })

    except Exception as e:
        return jsonify({"msg": "error", "details": str(e)}), 500

@redacao_bp.route('/redacao')
def redacaoPage():
    try:
        correcoes = Corrections.query.filter_by(user=session['user']).all()
        notas, datas = extract_scores_from_corrections(correcoes)

        maior_nota = max(notas) if notas else 0
        menor_nota = min(notas) if notas else 0
        media_nota = round(sum(notas) / len(notas), 2) if notas else 0

        return render_template(
            'redacoes.html',
            redacoes=correcoes,
            total_redacoes=len(correcoes),
            maior_nota=maior_nota,
            menor_nota=menor_nota,
            media_nota=media_nota,
            notas=notas,
            datas=datas
        )
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
        estagio = data.get("estagio")

        if not all([texto, tema, estagio]):
            return jsonify({"msg": "error", "details": "Dados insuficientes para avaliação"}), 400

        sistema = (
            "Você é um assistente na produção de redações para o ENEM. Irá ajudar o usuário a saber o que escrever nas próximas linhas com base no que já foi escrito e de acordo com o tema e o estágio informado. "
            "Responda objetivamente, indicando o que o estudante pode escrever a seguir, mencionando recursos de repertório quando relevante. Não escreva a redação inteira; dê apenas as próximas linhas, dicas práticas e sugestões de argumentos. E o mais importante: não use markdown (negrito etc.)"
        )

        chat_completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": f"Tema: {tema}. Estágio declarado pelo usuário: {estagio}. Redação atual: {texto}"}
            ]
        )

        assistant_response = chat_completion.choices[0].message.content
        return jsonify({
            "msg": "success",
            "guia": assistant_response
        })
    except Exception as e:
        return jsonify({
            "msg": "error",
            "error": str(e)
        })

@redacao_bp.route("/api/recorrigir-competencia", methods=["POST"])
def recorrigir_competencia():
    try:
        data = request.get_json()
        competencia = int(data.get("competencia"))
        correcao_id = data.get("correcao_id")

        correcao = Corrections.query.filter_by(id=correcao_id).first()
        if not correcao:
            return jsonify({"msg": "error", "details": "Correção não encontrada."}), 404

        if competencia not in [1, 2, 3, 4, 5]:
            return jsonify({"msg": "error", "details": "Competência inválida."}), 400

        competency_prompts = {
            1: "Competência 1: Demonstre o domínio da norma culta da língua escrita.",
            2: "Competência 2: Compreenda a proposta de redação e aplique conceitos de várias áreas para desenvolver o tema.",
            3: "Competência 3: Selecione, relacione, organize e interprete informações, fatos, opiniões e argumentos em defesa de um ponto de vista.",
            4: "Competência 4: Demonstre conhecimento dos mecanismos linguísticos necessários para a construção da argumentação.",
            5: "Competência 5: Elabore proposta de intervenção para o problema abordado, respeitando os direitos humanos."
        }

        system_prompt = "Você é um corretor de redações do ENEM. Seja direto e objetivo."
        user_prompt = f"Avalie apenas a {competency_prompts[competencia]} do ENEM para o texto abaixo, pois o estudante achou algum erro. Dê uma nota de 0 a 200 e um comentário breve (máx. 2 frases). Responda em JSON: {{'nota': int, 'analise': str}}. Tema: {correcao.tema}. Redação: {correcao.texto}"

        chat_completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            top_p=1.0
        )

        result = parse_ai_response(chat_completion.choices[0].message.content)
        if not result:
            return jsonify({"msg": "error", "details": "Erro ao processar resposta da IA."}), 500

        nota = str(result.get("nota", 0))
        analise = result.get("analise", "")
        setattr(correcao, f"cp{competencia}", f"{nota}\\{analise}")

        # Recalculate final score
        notas = []
        for i in range(1, 6):
            valor = getattr(correcao, f"cp{i}")
            nota_comp = int(valor.split("\\")[0]) if valor else 0
            notas.append(nota_comp)

        # Generate new final analysis
        prompt_final = (
            f"Estas são as notas das competências do ENEM para a redação abaixo: "
            f"{notas}. Some as notas para dar a nota final (máx. 1000) e faça uma análise geral em até 2 frases. "
            f"Responda em JSON: {{'nota': int, 'analise': str}}. Tema: {correcao.tema}. Redação: {correcao.texto}"
        )

        chat_final = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_final}
            ],
            temperature=0.1,
            top_p=1.0
        )

        result_final = parse_ai_response(chat_final.choices[0].message.content)
        nota_final = str(result_final.get("nota", sum(notas))) if result_final else str(sum(notas))
        analise_final = result_final.get("analise", "Análise final não disponível.") if result_final else "Análise final não disponível."

        correcao.final = f"{nota_final}\\{analise_final}"
        db.session.commit()

        return jsonify({
            "msg": "success",
            "nota": nota,
            "analise": analise,
            "nota_final": nota_final,
            "analise_final": analise_final
        })
    except Exception as e:
        return jsonify({"msg": "error", "details": str(e)}), 500

@redacao_bp.route("/api/avaliar-redacao", methods=["POST"])
def avaliar_redacao():
    try:
        user = session["user"]
        
        data = request.get_json()
        
        nota = float(data["nota"])
        comentario = data["comentario"]
        correcao_id = data["correcao_id"]
        
        tipo = "redacao"
        
        new_avaliacao = Avaliacao(
            id=str(uuid.uuid4()),
            tipo=tipo,
            nota=nota,
            comentario=comentario,
            user=user,
            correcao_id=correcao_id
        )
        
        db.session.add(new_avaliacao)
        db.session.commit()
        
        return jsonify({"msg": "success"})
    except Exception as e:
        return jsonify({"msg": "error", "details": str(e)}), 500
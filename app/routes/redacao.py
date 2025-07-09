from app.routes import redacao_bp
from app import db
from flask import render_template, redirect, session, jsonify, request

from openai import AzureOpenAI
import uuid

import os

from app.models import Corrections
import uuid
import json
from datetime import datetime

azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
if azure_endpoint is None:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set.")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-07-01-preview",
    azure_endpoint=azure_endpoint
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
        
        if len(conteudo) < 60:
            return jsonify({"msg": "error", "details": "Sua redação precisa ser maior!"})

        # Fazendo a chamada à API do Azure OpenAI
        chat_completion = client.chat.completions.create(
    model="gpt-4o",  # Nome do deployment configurado no Azure
    messages=[
        {"role": "system", "content": """
           Você é um corretor de redações do ENEM. Avalie a redação com base nas 5 competências do ENEM, atribuindo nota (0–200) e um comentário breve (máx. 2 frases) por competência.

Retorne o resultado em JSON com este formato:
{
  "competencia1": {"nota": int, "analise": str},
  "competencia2": {"nota": int, "analise": str},
  "competencia3": {"nota": int, "analise": str},
  "competencia4": {"nota": int, "analise": str},
  "competencia5": {"nota": int, "analise": str},
  "notaFinal": {"nota": int, "analise": str}
}
Seja direto e objetivo.                
        """},
        {"role": "user", "content": f"Título: {titulo}. Tema: {tema}. Redação: {conteudo}"}
    ],
    temperature=0.1,
    top_p=1.0
)

        content = chat_completion.choices[0].message.content
        if content is None:
            return jsonify({"msg": "error", "details": "A resposta da IA está vazia."}), 500
        assistant_response = content.replace('\n', '').replace('json', '').replace('`','')
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
        return jsonify({"msg": "error", "details": str(e)}), 500

@redacao_bp.route('/redacao')
def redacaoPage():
    try:
        correcoes = Corrections.query.filter_by(user=session['user']).all()

        # Estatísticas
        total = len(correcoes)
        datas = []
        notas = []
        for c in correcoes:
            try:
                nota = int(str(c.final).split("\\")[0])
                notas.append(nota)
                datas.append(c.data)
            except Exception:
                continue

        maior_nota = max(notas) if notas else 0
        menor_nota = min(notas) if notas else 0
        media_nota = round(sum(notas)/len(notas), 2) if notas else 0

        return render_template(
            'redacoes.html',
            redacoes=correcoes,
            total_redacoes=total,
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

from flask import request, jsonify

@redacao_bp.route("/api/recorrigir-competencia", methods=["POST"])
def recorrigir_competencia():
    try:
        data = request.get_json()
        competencia = int(data.get("competencia"))
        correcao_id = data.get("correcao_id")

        correcao = Corrections.query.filter_by(id=correcao_id).first()
        if not correcao:
            return jsonify({"msg": "error", "details": "Correção não encontrada."}), 404

        if competencia not in [1,2,3,4,5]:
            return jsonify({"msg": "error", "details": "Competência inválida."}), 400

        prompts = [
            "Competência 1: Demonstre o domínio da norma culta da língua escrita.",
            "Competência 2: Compreenda a proposta de redação e aplique conceitos de várias áreas para desenvolver o tema.",
            "Competência 3: Selecione, relacione, organize e interprete informações, fatos, opiniões e argumentos em defesa de um ponto de vista.",
            "Competência 4: Demonstre conhecimento dos mecanismos linguísticos necessários para a construção da argumentação.",
            "Competência 5: Elabore proposta de intervenção para o problema abordado, respeitando os direitos humanos."
        ]
        prompt = f"Avalie apenas a {prompts[competencia-1]} do ENEM para o texto abaixo, pois o estudante achou algum erro. Dê uma nota de 0 a 200 e um comentário breve (máx. 2 frases). Responda em JSON: {{'nota': int, 'analise': str}}. Tema: {correcao.tema}. Redação: {correcao.texto}"

        chat_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um corretor de redações do ENEM. Seja direto e objetivo."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            top_p=1.0
        )
        content = chat_completion.choices[0].message.content.replace('\n', '').replace('json', '').replace('`','')
        import json
        try:
            result = json.loads(content)
            nota = str(result.get("nota", 0))
            analise = result.get("analise", "")
        except Exception:
            return jsonify({"msg": "error", "details": "Erro ao processar resposta da IA."}), 500

        # Atualiza a competência recorrigida no banco
        campo = f"cp{competencia}"
        setattr(correcao, campo, f"{nota}\\{analise}")

        # Recalcula a nota final e pede nova análise final para a IA
        notas = []
        for i in range(1, 6):
            valor = getattr(correcao, f"cp{i}")
            nota_comp = int(valor.split("\\")[0]) if valor else 0
            notas.append(nota_comp)
        nova_nota_final = sum(notas)

        # Gera nova análise final com a IA
        prompt_final = (
            f"Estas são as notas das competências do ENEM para a redação abaixo: "
            f"{notas}. Some as notas para dar a nota final (máx. 1000) e faça uma análise geral em até 2 frases. "
            f"Responda em JSON: {{'nota': int, 'analise': str}}. Tema: {correcao.tema}. Redação: {correcao.texto}"
        )
        chat_final = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um corretor de redações do ENEM. Seja direto e objetivo."},
                {"role": "user", "content": prompt_final}
            ],
            temperature=0.1,
            top_p=1.0
        )
        content_final = chat_final.choices[0].message.content.replace('\n', '').replace('json', '').replace('`','')
        try:
            result_final = json.loads(content_final)
            nota_final = str(result_final.get("nota", nova_nota_final))
            analise_final = result_final.get("analise", "")
        except Exception:
            nota_final = str(nova_nota_final)
            analise_final = "Análise final não disponível."

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

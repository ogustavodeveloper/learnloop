# salvar como: transcricao_youtube.py

from youtube_transcript_api import YouTubeTranscriptApi
import re

def obter_transcricao(video_url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", video_url)
    if not match:
        raise ValueError("URL inválida. Não foi possível extrair o ID do vídeo.")
    video_id = match.group(1)

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        texto_completo = " ".join([entry['text'] for entry in transcript])
        return texto_completo
    except Exception as e:
        return f"Erro ao obter transcrição: {str(e)}"

if __name__ == "__main__":
    url = input("Digite a URL da videoaula do YouTube: ")
    transcricao = obter_transcricao(url)
    print("\nTranscrição:\n")
    print(transcricao)

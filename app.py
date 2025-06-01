
#!/usr/bin/env python
"""
AutoMeetAI - Interface Web com Streamlit

Este script implementa uma interface web para o AutoMeetAI utilizando Streamlit.
Permite que os usuários:
1. Carreguem arquivos de vídeo
2. Configurem parâmetros de transcrição
3. Obtenham transcrições com identificação de falantes
4. Gerem resumos e análises das reuniões

Uso:
    streamlit run app.py
"""

import streamlit as st
import uuid
import os
import tempfile
from typing import Dict, Any, Optional

from annotated_text import annotated_text

from src.factory import AutoMeetAIFactory
from src.utils.logging import get_logger, configure_logger
from src.exceptions import AutoMeetAIError

# Inicializa o logger para este módulo
logger = get_logger(__name__)

# Configura o logger raiz
configure_logger()

# Tenta obter as chaves de API do Streamlit Secrets, com fallback para user_preferences.json
from src.config.user_preferences_provider import UserPreferencesProvider

# Inicializa o provedor de preferências do usuário
user_prefs = UserPreferencesProvider()

# Tenta obter as chaves de API do Streamlit Secrets
try:
    aai_api_key = st.secrets['assemblyai']['api_key']
    openai_api_key = st.secrets['openai']['api_key']
    logger.info("API keys obtidas do Streamlit Secrets")
except Exception as e:
    # Fallback para user_preferences.json
    logger.info(f"Não foi possível obter API keys do Streamlit Secrets: {e}")
    logger.info("Tentando obter API keys de user_preferences.json")

    aai_api_key = user_prefs.get('assemblyai_api_key')
    openai_api_key = user_prefs.get('openai_api_key')

    if not aai_api_key or not openai_api_key:
        st.error("API keys não encontradas. Configure-as no arquivo user_preferences.json ou no Streamlit Secrets.")
        logger.error("API keys não encontradas em user_preferences.json")
        st.stop()

    logger.info("API keys obtidas de user_preferences.json")


# Códigos de idioma suportados pelo serviço de transcrição
language_codes = {
    "Portuguese": "pt",          # Português
    "Global English": "en",      # Inglês Global
    "Australian English": "en_au", # Inglês Australiano
    "British English": "en_uk",  # Inglês Britânico
    "Spanish": "es",             # Espanhol
    "US English": "en_us",       # Inglês Americano
    "French": "fr",              # Francês
    "German": "de",              # Alemão
    "Italian": "it",             # Italiano
    "Dutch": "nl",               # Holandês
    "Hindi": "hi",               # Hindi
    "Japanese": "ja",            # Japonês
    "Chinese": "zh",             # Chinês
    "Finnish": "fi",             # Finlandês
    "Korean": "ko",              # Coreano
    "Polish": "pl",              # Polonês
    "Russian": "ru",             # Russo
    "Turkish": "tr",             # Turco
    "Ukrainian": "uk",           # Ucraniano
    "Vietnamese": "vi"           # Vietnamita
}




st.title('🤖 AutomeetAI')

prompt_system = st.text_area("Forneça instruções gerais ou estabeleça o tom para o \"assistente\" de IA:", "Você é um ótimo gerente de projetos com grandes capacidades de criação de atas de reunião.")

prompt_text = st.text_area("O que o usuário deseja que o assistente faça?", """Em uma redação de nível especializado, resuma as notas da reunião em um único parágrafo.
Em seguida, escreva uma lista de cada um de seus pontos-chaves tratados na reunião.
Por fim, liste as próximas etapas ou itens de ação sugeridos pelos palestrantes, se houver.""")

st.divider()


col21, col22 = st.columns(2)


with col21:
	speakers_expected = st.number_input("Total de pessoas falantes:", 1, 15)

with col22:
	language = st.selectbox("Selecione o idioma falado:", tuple(language_codes.keys()))


uploaded_file = st.file_uploader("Selecione o seu arquivo", accept_multiple_files=False, type=['mp4'])


st.divider()




if uploaded_file:
    try:
        # Cria uma instância do AutoMeetAI usando a fábrica
        factory = AutoMeetAIFactory()
        app = factory.create(
            assemblyai_api_key=aai_api_key,
            openai_api_key=openai_api_key,
            include_text_generation=True,
            use_cache=True
        )

        # Salva o arquivo carregado em um arquivo temporário
        with st.spinner('Preparando o arquivo de vídeo...'):
            # Cria um arquivo temporário para o vídeo
            temp_dir = tempfile.mkdtemp()
            mp4_filename = os.path.join(temp_dir, uploaded_file.name)

            # Salva o conteúdo do arquivo carregado no arquivo temporário
            with open(mp4_filename, 'wb') as f:
                f.write(uploaded_file.read())

            logger.info(f"Arquivo de vídeo salvo temporariamente em: {mp4_filename}")

        # Configura as opções de transcrição
        transcription_config = {
            "speaker_labels": True,
            "speakers_expected": speakers_expected,
            "language_code": language_codes[language]
        }

        # Processa o vídeo (converte para áudio e transcreve)
        with st.spinner('Processando o vídeo (convertendo e transcrevendo)...'):
            # Define uma função de callback para mostrar o progresso
            def progress_callback(stage, current, total):
                # Atualiza a mensagem de progresso no Streamlit
                progress_text = f"{stage} ({int(current)}/{int(total)})"
                st.text(progress_text)

            # Processa o vídeo
            transcription = app.process_video(
                video_file=mp4_filename,
                transcription_config=transcription_config,
                save_audio=False,
                progress_callback=progress_callback
            )

            if not transcription:
                st.error("Falha ao processar o vídeo. Verifique o arquivo e tente novamente.")
                logger.error("Falha ao processar o vídeo")
                st.stop()

            st.success("Vídeo processado e transcrito com sucesso!")

            # Prepara o texto transcrito e os dados para anotação
            texto_transcrito = ''
            texto_anotado = []

            for utterance in transcription.utterances:
                texto_transcrito += f"Speaker {utterance.speaker}: {utterance.text}\n"
                texto_anotado.append((utterance.text, f"Speaker {utterance.speaker}"))

        # Gera a análise da transcrição
        with st.spinner('Gerando ata de reunião...'):
            # Prepara o prompt para análise
            user_prompt_template = prompt_text + "\n===========\n{transcription}"

            # Gera a análise
            texto_retorno = app.analyze_transcription(
                transcription=transcription,
                system_prompt=prompt_system,
                user_prompt_template=user_prompt_template
            )

            if not texto_retorno:
                st.error("Falha ao gerar a ata da reunião.")
                logger.error("Falha ao gerar a ata da reunião")
                st.stop()

            st.success("Ata gerada com sucesso!")

        # Exibe os resultados
        st.subheader('Transcrição original')
        annotated_text(texto_anotado)

        st.subheader('Ata gerada')
        st.markdown(texto_retorno)

        # Limpa os arquivos temporários
        try:
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"Diretório temporário removido: {temp_dir}")
        except Exception as e:
            logger.warning(f"Não foi possível remover o diretório temporário: {e}")

    except AutoMeetAIError as e:
        # Exibe mensagens de erro amigáveis para o usuário
        st.error(f"Erro: {e.get_user_friendly_message()}")
        logger.error(f"AutoMeetAIError: {e}")

    except Exception as e:
        # Trata outros erros inesperados
        st.error(f"Ocorreu um erro inesperado: {e}")
        logger.error(f"Erro inesperado: {e}", exc_info=True)

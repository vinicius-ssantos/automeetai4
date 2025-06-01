
import streamlit as st
import uuid
import os
import tempfile
from typing import Optional, Dict, Any

from src.factory import AutoMeetAIFactory
from src.utils.logging import get_logger, configure_logger
from src.config.env_config_provider import EnvConfigProvider
from src.config.user_preferences_provider import UserPreferencesProvider
from src.config.composite_config_provider import CompositeConfigProvider

from annotated_text import annotated_text

# Configure logging
configure_logger()
logger = get_logger(__name__)

# Function to safely access Streamlit secrets
def get_secret(section, key, env_var=None):
    try:
        # Try to get from Streamlit secrets
        value = st.secrets.get(section, {}).get(key)
        if value:
            return value
    except Exception as e:
        # Log at debug level instead of warning since this is expected behavior
        logger.debug(f"Error accessing Streamlit secrets: {e}")

    # Fall back to environment variables if specified
    if env_var and env_var in os.environ:
        return os.environ.get(env_var)

    return None

# Get API keys from Streamlit secrets or environment variables
aai_api_key = get_secret('assemblyai', 'api_key', 'ASSEMBLYAI_API_KEY')
openai_api_key = get_secret('openai', 'api_key', 'OPENAI_API_KEY')

# Check if API keys are available
if not aai_api_key or not openai_api_key:
    st.error("""
    ### API Keys Missing

    One or both required API keys are missing. Please configure your API keys using one of these methods:

    1. Create a `.streamlit/secrets.toml` file with your API keys
    2. Set environment variables: ASSEMBLYAI_API_KEY and OPENAI_API_KEY

    See the README file for more details on configuration.
    """)
    # Initialize with None to avoid errors, but functionality will be limited
    automeetai = None
else:
    # Initialize AutoMeetAI
    factory = AutoMeetAIFactory()
    automeetai = factory.create(
        assemblyai_api_key=aai_api_key,
        openai_api_key=openai_api_key,
        use_cache=True
    )


language_codes = {
	"Portuguese": "pt",		  # Key: Portuguese, Value: 'pt'
	"Global English": "en",	  # Key: Global English, Value: 'en'
	"Australian English": "en_au", # Key: Australian English, Value: 'en_au'
	"British English": "en_uk",  # Key: British English, Value: 'en_uk'
	"Spanish": "es",			 # Key: Spanish, Value: 'es'
	"US English": "en_us",	   # Key: US English, Value: 'en_us'
	"French": "fr",			  # Key: French, Value: 'fr'
	"German": "de",			  # Key: German, Value: 'de'
	"Italian": "it",			 # Key: Italian, Value: 'it'
	"Dutch": "nl",			   # Key: Dutch, Value: 'nl'
	"Hindi": "hi",			   # Key: Hindi, Value: 'hi'
	"Japanese": "ja",			# Key: Japanese, Value: 'ja'
	"Chinese": "zh",			 # Key: Chinese, Value: 'zh'
	"Finnish": "fi",			 # Key: Finnish, Value: 'fi'
	"Korean": "ko",			  # Key: Korean, Value: 'ko'
	"Polish": "pl",			  # Key: Polish, Value: 'pl'
	"Russian": "ru",			 # Key: Russian, Value: 'ru'
	"Turkish": "tr",			 # Key: Turkish, Value: 'tr'
	"Ukrainian": "uk",		   # Key: Ukrainian, Value: 'uk'
	"Vietnamese": "vi"		   # Key: Vietnamese, Value: 'vi'
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
    # Check if automeetai is initialized
    if automeetai is None:
        st.error("Cannot process video: API keys are missing. Please configure your API keys first.")
    else:
        # Create a temporary file to save the uploaded video
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(uploaded_file.read())
            video_path = tmp_file.name

        try:
            # Configure transcription options
            transcription_config = {
                "speaker_labels": True,
                "speakers_expected": speakers_expected,
                "language_code": language_codes[language]
            }

            # Process the video file
            with st.spinner('Processando o vídeo...'):
                # Progress callback to show progress in Streamlit
                def progress_callback(stage, current, total):
                    if total > 0:
                        progress = current / total
                        st.progress(progress)

                # Process the video and get transcription
                transcription = automeetai.process_video(
                    video_file=video_path,
                    transcription_config=transcription_config,
                    save_audio=True,
                    progress_callback=progress_callback
                )

            st.success("Processamento do vídeo concluído!")

            if transcription:
                # Prepare text for display and analysis
                texto_transcrito = ''
                texto_anotado = []

                for utterance in transcription.utterances:
                    texto_transcrito += f"Speaker {utterance.speaker}: {utterance.text}"
                    texto_transcrito += '\n'
                    texto_anotado.append((utterance.text, f"Speaker {utterance.speaker}"))

                # Generate meeting minutes
                with st.spinner('Gerando ata de reunião...'):
                    # Prepare prompts for analysis
                    system_prompt = prompt_system
                    user_prompt_template = prompt_text + "\n===========\n{transcription}"

                    # Replace placeholder with actual transcription
                    user_prompt = user_prompt_template.replace("{transcription}", texto_transcrito)

                    # Analyze transcription
                    texto_retorno = automeetai.analyze_transcription(
                        transcription=transcription,
                        system_prompt=system_prompt,
                        user_prompt_template=user_prompt
                    )

                st.success("Ata gerada com sucesso!")

                # Display results
                st.subheader('Transcrição original')
                annotated_text(texto_anotado)

                st.subheader('Ata gerada')
                st.markdown(texto_retorno)
            else:
                st.error("Falha ao processar o vídeo. Verifique o formato do arquivo e tente novamente.")

        finally:
            # Clean up temporary file
            if 'video_path' in locals() and os.path.exists(video_path):
                try:
                    os.unlink(video_path)
                except Exception as e:
                    logger.error(f"Erro ao remover arquivo temporário: {e}")

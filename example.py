#!/usr/bin/env python
"""
Example script demonstrating how to use AutoMeetAI programmatically.
"""

from src.factory import AutoMeetAIFactory
from src.utils.logging import get_logger
from src.config.env_config_provider import EnvConfigProvider
from src.config.user_preferences_provider import UserPreferencesProvider
from src.config.composite_config_provider import CompositeConfigProvider

# Obter o logger para este módulo
logger = get_logger(__name__)

def main():
    # Cria um provedor de configuração composto que combina múltiplas fontes
    composite_provider = CompositeConfigProvider()

    # Adiciona provedores na ordem de prioridade (primeiro tem precedência)
    composite_provider.add_provider(EnvConfigProvider())  # Primeiro tenta variáveis de ambiente
    composite_provider.add_provider(UserPreferencesProvider())  # Depois tenta user_preferences.json

    # Recupera as chaves de API do provedor de configuração composto
    assemblyai_api_key = composite_provider.get("assemblyai_api_key")
    openai_api_key = composite_provider.get("openai_api_key")

    if not assemblyai_api_key or not openai_api_key:
        logger.error("As chaves de API não foram encontradas. Verifique suas variáveis de ambiente ou o arquivo user_preferences.json.")
        return

    # Inicializa a aplicação usando as chaves obtidas
    factory = AutoMeetAIFactory()
    app = factory.create(
        assemblyai_api_key=assemblyai_api_key,  # AssemblyAI API key
        openai_api_key=openai_api_key           # OpenAI API key
    )

    # Processa um arquivo de vídeo
    video_file = "entrevista.mp4"  # Substitua pelo caminho do arquivo de vídeo
    logger.info("Processing video: %s", video_file)

    transcription = app.process_video(
        video_file=video_file,
        save_audio=True  # Salvar o arquivo de áudio intermediário
    )

    if not transcription:
        logger.error("Processing failed.")
        return

    logger.info("Transcription completed successfully.")
    logger.info("Number of utterances: %d", len(transcription.utterances))

    # Imprime as primeiras declarações
    logger.info("Sample of transcription:")
    for i, utterance in enumerate(transcription.utterances[:3]):
        logger.debug("%s: %s...", utterance.speaker, utterance.text[:100])
        if i >= 2:
            break

    # Analisa a transcrição
    logger.info("Analyzing transcription...")

    system_prompt = "You are a helpful assistant that analyzes meeting transcriptions."
    user_prompt_template = """
    Please analyze the following meeting transcription and provide:
    1. A brief summary (2-3 sentences)
    2. Key topics discussed
    3. Main speakers and their roles (if identifiable)
    4. Any action items or decisions made

    Transcription:
    {transcription}
    """

    analysis = app.analyze_transcription(
        transcription=transcription,
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template
    )

    if analysis:
        logger.info("Analysis completed successfully.")
        logger.info("Analysis preview:")
        preview = analysis[:500] + "..." if len(analysis) > 500 else analysis
        logger.info(preview)
    else:
        logger.error("Analysis failed.")

if __name__ == "__main__":
    main()

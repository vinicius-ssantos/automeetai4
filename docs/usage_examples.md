# Exemplos de Uso do AutoMeetAI

Este documento fornece exemplos práticos de como usar o AutoMeetAI para diferentes cenários comuns.

## Índice

1. [Transcrição Básica de um Vídeo](#transcrição-básica-de-um-vídeo)
2. [Processamento em Lote de Múltiplos Vídeos](#processamento-em-lote-de-múltiplos-vídeos)
3. [Análise de Transcrição com IA](#análise-de-transcrição-com-ia)
4. [Exportação em Diferentes Formatos](#exportação-em-diferentes-formatos)
5. [Transcrição em Tempo Real](#transcrição-em-tempo-real)
6. [Uso de Diferentes Serviços de Transcrição](#uso-de-diferentes-serviços-de-transcrição)
7. [Configuração Avançada](#configuração-avançada)
8. [Uso de Plugins](#uso-de-plugins)

## Transcrição Básica de um Vídeo

Este exemplo mostra como transcrever um único arquivo de vídeo:

```python
from src.factory import AutoMeetAIFactory

# Criar uma instância do AutoMeetAI
factory = AutoMeetAIFactory()
app = factory.create()

# Processar um vídeo
transcription = app.process_video("videos/entrevista.mp4")

# Salvar a transcrição em um arquivo de texto
if transcription:
    transcription.save_to_file("output/entrevista.txt")
    print("Transcrição salva com sucesso!")
else:
    print("Falha ao processar o vídeo.")
```

## Processamento em Lote de Múltiplos Vídeos

Este exemplo mostra como processar múltiplos vídeos em lote:

```python
from src.factory import AutoMeetAIFactory
import os

# Criar uma instância do AutoMeetAI
factory = AutoMeetAIFactory()
app = factory.create()

# Lista de vídeos para processar
videos = [
    "videos/reuniao1.mp4",
    "videos/reuniao2.mp4",
    "videos/entrevista.mp4"
]

# Processar os vídeos em lote
results = app.process_videos(
    video_files=videos,
    save_audio=True,  # Salvar os arquivos de áudio intermediários
    continue_on_error=True  # Continuar mesmo se um vídeo falhar
)

# Processar os resultados
for video_path, transcription in results:
    if transcription:
        # Criar nome de arquivo de saída baseado no nome do vídeo
        filename = os.path.splitext(os.path.basename(video_path))[0]
        output_path = f"output/{filename}.txt"
        
        # Salvar a transcrição
        transcription.save_to_file(output_path)
        print(f"Transcrição de {video_path} salva em {output_path}")
    else:
        print(f"Falha ao processar {video_path}")
```

## Análise de Transcrição com IA

Este exemplo mostra como analisar uma transcrição usando IA:

```python
from src.factory import AutoMeetAIFactory
import os

# Criar uma instância do AutoMeetAI com geração de texto habilitada
factory = AutoMeetAIFactory()
app = factory.create(include_text_generation=True)

# Processar um vídeo
video_path = "videos/reuniao.mp4"
transcription = app.process_video(video_path)

if transcription:
    # Definir prompts para análise
    system_prompt = "Você é um assistente especializado em analisar reuniões de negócios."
    user_prompt_template = """
    Por favor, analise a seguinte transcrição de reunião e forneça:
    1. Um resumo executivo (máximo 3 parágrafos)
    2. Pontos-chave discutidos
    3. Decisões tomadas
    4. Itens de ação com responsáveis (se mencionados)
    5. Próximos passos
    
    Transcrição:
    {transcription}
    """
    
    # Analisar a transcrição
    analysis = app.analyze_transcription(
        transcription=transcription,
        system_prompt=system_prompt,
        user_prompt_template=user_prompt_template
    )
    
    if analysis:
        # Salvar a análise em um arquivo
        filename = os.path.splitext(os.path.basename(video_path))[0]
        output_path = f"output/{filename}_analise.txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(analysis)
            
        print(f"Análise salva em {output_path}")
    else:
        print("Falha ao analisar a transcrição.")
else:
    print("Falha ao processar o vídeo.")
```

## Exportação em Diferentes Formatos

Este exemplo mostra como exportar uma transcrição em diferentes formatos:

```python
from src.factory import AutoMeetAIFactory

# Criar uma instância do AutoMeetAI
factory = AutoMeetAIFactory()
app = factory.create()

# Processar um vídeo e exportar em múltiplos formatos
video_path = "videos/palestra.mp4"
transcription = app.process_video(
    video_file=video_path,
    output_formats=["txt", "json", "html"]
)

if transcription:
    print("Transcrição concluída e salva em múltiplos formatos.")
    
    # Também podemos salvar manualmente em formatos específicos com opções personalizadas
    
    # Salvar em formato HTML com opções personalizadas
    html_options = {
        "title": "Transcrição da Palestra",
        "include_timestamps": True,
        "highlight_speakers": True,
        "css_class": "transcript-container"
    }
    
    transcription.save_to_file(
        output_file="output/palestra_personalizada.html",
        format_name="html",
        options=html_options
    )
    
    print("Versão HTML personalizada salva.")
else:
    print("Falha ao processar o vídeo.")
```

## Transcrição em Tempo Real

Este exemplo mostra como usar a transcrição em tempo real do microfone:

```python
from src.services.assemblyai_streaming_transcription_service import AssemblyAIStreamingTranscriptionService
from src.config.env_config_provider import EnvConfigProvider
import time

# Função de callback para processar resultados de transcrição
def process_result(result):
    if result.get("text"):
        if result.get("is_final"):
            print(f"\nFINAL: {result.get('text')}")
        else:
            print(f"\rPARCIAL: {result.get('text')}", end="")

# Criar provedor de configuração
config_provider = EnvConfigProvider()

# Criar serviço de transcrição em streaming
streaming_service = AssemblyAIStreamingTranscriptionService(config_provider=config_provider)

try:
    print("Iniciando transcrição em tempo real. Fale no microfone...")
    print("Pressione Ctrl+C para parar.")
    
    # Configuração para a transcrição
    config = {
        "language_code": "pt",
        "speaker_labels": True
    }
    
    # Iniciar streaming do microfone por 30 segundos
    streaming_service.stream_microphone(
        callback=process_result,
        duration=30,
        config=config
    )
    
    print("\nTranscrição finalizada.")
    
except KeyboardInterrupt:
    print("\nTranscrição interrompida pelo usuário.")
    
finally:
    # Garantir que o streaming seja finalizado
    if streaming_service.is_streaming():
        result = streaming_service.stop_streaming()
        if result:
            print("\nTranscrição final:")
            print(result.to_formatted_text())
```

## Uso de Diferentes Serviços de Transcrição

Este exemplo mostra como usar diferentes serviços de transcrição:

```python
from src.factory import AutoMeetAIFactory

# Criar uma instância do AutoMeetAI com o serviço AssemblyAI (padrão)
factory = AutoMeetAIFactory()
app_assemblyai = factory.create(transcription_service_type="assemblyai")

# Criar uma instância do AutoMeetAI com o serviço Whisper
app_whisper = factory.create(transcription_service_type="whisper")

# Criar uma instância do AutoMeetAI com o serviço Mock (para testes)
app_mock = factory.create(transcription_service_type="mock")

# Processar o mesmo vídeo com diferentes serviços
video_path = "videos/amostra.mp4"

print("Processando com AssemblyAI...")
result_assemblyai = app_assemblyai.process_video(video_path)

print("Processando com Whisper...")
result_whisper = app_whisper.process_video(video_path)

print("Processando com serviço Mock...")
result_mock = app_mock.process_video(video_path)

# Comparar os resultados
if result_assemblyai and result_whisper:
    print("\nComparação de resultados:")
    print(f"AssemblyAI: {len(result_assemblyai.text)} caracteres")
    print(f"Whisper: {len(result_whisper.text)} caracteres")
    
    # Salvar os resultados para comparação
    result_assemblyai.save_to_file("output/amostra_assemblyai.txt")
    result_whisper.save_to_file("output/amostra_whisper.txt")
    result_mock.save_to_file("output/amostra_mock.txt")
```

## Configuração Avançada

Este exemplo mostra como usar configurações avançadas:

```python
from src.factory import AutoMeetAIFactory
from src.config.env_config_provider import EnvConfigProvider

# Criar um provedor de configuração personalizado
config_provider = EnvConfigProvider()

# Definir configurações personalizadas
config_provider.set("assemblyai_api_key", "sua_chave_api_assemblyai")
config_provider.set("openai_api_key", "sua_chave_api_openai")
config_provider.set("default_language_code", "pt-br")
config_provider.set("default_speaker_labels", True)
config_provider.set("default_speakers_expected", 3)

# Criar uma instância do AutoMeetAI com configuração personalizada
factory = AutoMeetAIFactory()
app = factory.create(
    assemblyai_api_key=config_provider.get("assemblyai_api_key"),
    openai_api_key=config_provider.get("openai_api_key"),
    include_text_generation=True,
    use_cache=True,
    cache_dir="cache_personalizado"
)

# Configuração específica para a transcrição
transcription_config = {
    "language_code": "pt-br",
    "speaker_labels": True,
    "speakers_expected": 3,
    "punctuate": True,
    "format_text": True
}

# Processar um vídeo com configuração personalizada
transcription = app.process_video(
    video_file="videos/debate.mp4",
    transcription_config=transcription_config,
    save_audio=True,
    force_reprocess=True
)

if transcription:
    print("Transcrição concluída com configuração personalizada.")
    transcription.save_to_file("output/debate_config_personalizada.txt")
else:
    print("Falha ao processar o vídeo.")
```

## Uso de Plugins

Este exemplo mostra como usar plugins:

```python
from src.factory import AutoMeetAIFactory

# Criar uma instância do AutoMeetAI com suporte a plugins
factory = AutoMeetAIFactory()

# Carregar plugins do diretório padrão
factory.load_plugins()

# Obter informações sobre os plugins carregados
plugin_info = factory.get_plugin_info()
print("Plugins carregados:")
for plugin in plugin_info:
    print(f"- {plugin['name']} v{plugin['version']}: {plugin['description']}")
    print(f"  Pontos de extensão: {plugin['extension_points']}")

# Configurar preferências de plugins
plugin_preferences = {
    "audio_converter": "CustomAudioConverter",
    "transcription_service": "CustomTranscriptionService"
}

# Criar a aplicação com preferências de plugins
app = factory.create(
    use_plugins=True,
    plugin_preferences=plugin_preferences
)

# Processar um vídeo usando os plugins configurados
transcription = app.process_video("videos/exemplo.mp4")

if transcription:
    print("Transcrição concluída usando plugins personalizados.")
    transcription.save_to_file("output/exemplo_plugins.txt")
else:
    print("Falha ao processar o vídeo.")
```

Estes exemplos demonstram os cenários mais comuns de uso do AutoMeetAI. Para mais detalhes sobre cada funcionalidade, consulte a [Documentação da API](api_documentation.md).
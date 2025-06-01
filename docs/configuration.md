# Opções de Configuração do AutoMeetAI

Este documento descreve todas as opções de configuração disponíveis no AutoMeetAI, seus valores padrão e seus efeitos no comportamento da aplicação.

## Índice

1. [Visão Geral](#visão-geral)
2. [Configuração de API](#configuração-de-api)
3. [Configuração de Transcrição](#configuração-de-transcrição)
4. [Configuração de Arquivos](#configuração-de-arquivos)
5. [Configuração de Conversão de Áudio](#configuração-de-conversão-de-áudio)
6. [Configuração de Limitação de Taxa](#configuração-de-limitação-de-taxa)
7. [Configuração de Streaming](#configuração-de-streaming)
8. [Configuração de Cache](#configuração-de-cache)
9. [Configuração de Plugins](#configuração-de-plugins)
10. [Métodos de Configuração](#métodos-de-configuração)

## Visão Geral

O AutoMeetAI usa um sistema de configuração flexível que permite personalizar o comportamento da aplicação. As configurações podem ser definidas de várias maneiras:

1. **Variáveis de ambiente**: Defina variáveis de ambiente com o prefixo `AUTOMEETAI_`.
2. **Parâmetros de método**: Passe parâmetros diretamente para os métodos da API.
3. **Provedor de configuração personalizado**: Implemente a interface `ConfigProvider`.

As configurações são definidas em `src/config/default_config.py` e podem ser sobrescritas por qualquer um dos métodos acima.

## Configuração de API

### AssemblyAI API

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `ASSEMBLYAI_API_KEY` | `str` | `None` | Chave de API para o serviço AssemblyAI. Obrigatória para usar o serviço de transcrição AssemblyAI. | `AUTOMEETAI_ASSEMBLYAI_API_KEY` |

### OpenAI API

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `OPENAI_API_KEY` | `str` | `None` | Chave de API para o serviço OpenAI. Obrigatória para usar o serviço de geração de texto OpenAI e o serviço de transcrição Whisper. | `AUTOMEETAI_OPENAI_API_KEY` |
| `OPENAI_MODEL` | `str` | `"gpt-4o-2024-08-06"` | Modelo OpenAI a ser usado para geração de texto. | `AUTOMEETAI_OPENAI_MODEL` |

### Whisper API

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `WHISPER_MODEL` | `str` | `"whisper-1"` | Modelo Whisper a ser usado para transcrição. | `AUTOMEETAI_WHISPER_MODEL` |
| `WHISPER_LANGUAGE` | `str` | `"pt"` | Código de idioma para transcrição Whisper. | `AUTOMEETAI_WHISPER_LANGUAGE` |
| `WHISPER_TEMPERATURE` | `float` | `0` | Temperatura para transcrição Whisper (0-1). Valores mais baixos são mais determinísticos. | `AUTOMEETAI_WHISPER_TEMPERATURE` |
| `WHISPER_RESPONSE_FORMAT` | `str` | `"verbose_json"` | Formato de resposta para transcrição Whisper. | `AUTOMEETAI_WHISPER_RESPONSE_FORMAT` |

## Configuração de Transcrição

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `DEFAULT_LANGUAGE_CODE` | `str` | `"pt"` | Código de idioma padrão para transcrição. | `AUTOMEETAI_DEFAULT_LANGUAGE_CODE` |
| `DEFAULT_SPEAKER_LABELS` | `bool` | `True` | Se deve identificar falantes diferentes na transcrição. | `AUTOMEETAI_DEFAULT_SPEAKER_LABELS` |
| `DEFAULT_SPEAKERS_EXPECTED` | `int` | `2` | Número esperado de falantes na transcrição. | `AUTOMEETAI_DEFAULT_SPEAKERS_EXPECTED` |

## Configuração de Arquivos

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `DEFAULT_OUTPUT_DIRECTORY` | `str` | `"output"` | Diretório padrão para salvar arquivos de saída. | `AUTOMEETAI_DEFAULT_OUTPUT_DIRECTORY` |

## Configuração de Conversão de Áudio

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `DEFAULT_ALLOWED_INPUT_EXTENSIONS` | `List[str]` | `["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "mp3", "wav", "ogg", "flac", "m4v", "3gp", "mpg", "mpeg", "ts", "m2ts", "vob", "ogv", "divx", "aac", "m4a", "wma", "aiff", "ac3", "amr"]` | Lista de extensões de arquivo de entrada permitidas. | `AUTOMEETAI_DEFAULT_ALLOWED_INPUT_EXTENSIONS` (separadas por vírgula) |
| `DEFAULT_ALLOWED_OUTPUT_EXTENSIONS` | `List[str]` | `["mp3", "wav", "ogg", "flac", "aac", "m4a", "wma", "aiff", "ac3"]` | Lista de extensões de arquivo de saída permitidas. | `AUTOMEETAI_DEFAULT_ALLOWED_OUTPUT_EXTENSIONS` (separadas por vírgula) |
| `DEFAULT_AUDIO_BITRATE` | `str` | `"128k"` | Taxa de bits padrão para conversão de áudio. | `AUTOMEETAI_DEFAULT_AUDIO_BITRATE` |
| `DEFAULT_AUDIO_FPS` | `int` | `44100` | Taxa de amostragem padrão para conversão de áudio (Hz). | `AUTOMEETAI_DEFAULT_AUDIO_FPS` |

## Configuração de Limitação de Taxa

### AssemblyAI

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `ASSEMBLYAI_RATE_LIMIT` | `float` | `0.167` | Limite de taxa para chamadas à API AssemblyAI (requisições por segundo). | `AUTOMEETAI_ASSEMBLYAI_RATE_LIMIT` |
| `ASSEMBLYAI_RATE_LIMIT_PER` | `float` | `1.0` | Período para o limite de taxa AssemblyAI (segundos). | `AUTOMEETAI_ASSEMBLYAI_RATE_LIMIT_PER` |
| `ASSEMBLYAI_RATE_LIMIT_BURST` | `int` | `5` | Número máximo de requisições em rajada para a API AssemblyAI. | `AUTOMEETAI_ASSEMBLYAI_RATE_LIMIT_BURST` |

### OpenAI

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `OPENAI_RATE_LIMIT` | `float` | `0.05` | Limite de taxa para chamadas à API OpenAI (requisições por segundo). | `AUTOMEETAI_OPENAI_RATE_LIMIT` |
| `OPENAI_RATE_LIMIT_PER` | `float` | `1.0` | Período para o limite de taxa OpenAI (segundos). | `AUTOMEETAI_OPENAI_RATE_LIMIT_PER` |
| `OPENAI_RATE_LIMIT_BURST` | `int` | `3` | Número máximo de requisições em rajada para a API OpenAI. | `AUTOMEETAI_OPENAI_RATE_LIMIT_BURST` |

## Configuração de Streaming

### AssemblyAI Streaming

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `ASSEMBLYAI_STREAMING_RATE` | `int` | `16000` | Taxa de amostragem para streaming de áudio (Hz). | `AUTOMEETAI_ASSEMBLYAI_STREAMING_RATE` |
| `ASSEMBLYAI_STREAMING_CHANNELS` | `int` | `1` | Número de canais para streaming de áudio. | `AUTOMEETAI_ASSEMBLYAI_STREAMING_CHANNELS` |
| `ASSEMBLYAI_STREAMING_CHUNK` | `int` | `1024` | Tamanho do fragmento de áudio para streaming (bytes). | `AUTOMEETAI_ASSEMBLYAI_STREAMING_CHUNK` |

## Configuração de Cache

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `CACHE_ENABLED` | `bool` | `True` | Se o cache de transcrição está habilitado. | `AUTOMEETAI_CACHE_ENABLED` |
| `CACHE_DIRECTORY` | `str` | `"cache"` | Diretório para armazenar arquivos de cache. | `AUTOMEETAI_CACHE_DIRECTORY` |
| `CACHE_EXPIRATION` | `int` | `86400` | Tempo de expiração do cache em segundos (padrão: 24 horas). | `AUTOMEETAI_CACHE_EXPIRATION` |

## Configuração de Plugins

| Opção | Tipo | Padrão | Descrição | Variável de Ambiente |
|-------|------|--------|-----------|----------------------|
| `PLUGINS_ENABLED` | `bool` | `True` | Se os plugins estão habilitados. | `AUTOMEETAI_PLUGINS_ENABLED` |
| `PLUGINS_DIRECTORY` | `str` | `"plugins"` | Diretório para carregar plugins. | `AUTOMEETAI_PLUGINS_DIRECTORY` |

## Métodos de Configuração

### Variáveis de Ambiente

Você pode definir variáveis de ambiente para configurar o AutoMeetAI. Todas as variáveis de ambiente devem ter o prefixo `AUTOMEETAI_`.

Exemplo:

```bash
# Windows PowerShell
$env:AUTOMEETAI_ASSEMBLYAI_API_KEY = "sua_chave_api_assemblyai"
$env:AUTOMEETAI_OPENAI_API_KEY = "sua_chave_api_openai"
$env:AUTOMEETAI_DEFAULT_LANGUAGE_CODE = "pt-br"

# Windows Command Prompt
set AUTOMEETAI_ASSEMBLYAI_API_KEY=sua_chave_api_assemblyai
set AUTOMEETAI_OPENAI_API_KEY=sua_chave_api_openai
set AUTOMEETAI_DEFAULT_LANGUAGE_CODE=pt-br
```

### Parâmetros de Método

Você pode passar parâmetros diretamente para os métodos da API para sobrescrever as configurações padrão.

Exemplo:

```python
from src.factory import AutoMeetAIFactory

# Criar uma instância do AutoMeetAI com configurações personalizadas
factory = AutoMeetAIFactory()
app = factory.create(
    assemblyai_api_key="sua_chave_api_assemblyai",
    openai_api_key="sua_chave_api_openai",
    include_text_generation=True,
    use_cache=True,
    cache_dir="cache_personalizado",
    transcription_service_type="whisper"
)

# Processar um vídeo com configurações personalizadas
transcription_config = {
    "language_code": "pt-br",
    "speaker_labels": True,
    "speakers_expected": 3
}

transcription = app.process_video(
    video_file="videos/reuniao.mp4",
    transcription_config=transcription_config,
    save_audio=True,
    force_reprocess=True,
    output_format="json"
)
```

### Provedor de Configuração Personalizado

Você pode implementar a interface `ConfigProvider` para fornecer configurações personalizadas.

Exemplo:

```python
from src.interfaces.config_provider import ConfigProvider

class MeuProvedorConfiguracao(ConfigProvider):
    def __init__(self):
        self.config = {
            "assemblyai_api_key": "sua_chave_api_assemblyai",
            "openai_api_key": "sua_chave_api_openai",
            "default_language_code": "pt-br",
            "default_speaker_labels": True,
            "default_speakers_expected": 3
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.config[key] = value

# Usar o provedor de configuração personalizado
from src.factory import AutoMeetAIFactory

factory = AutoMeetAIFactory()
config_provider = MeuProvedorConfiguracao()
app = factory.create(config_provider=config_provider)
```

### Arquivo de Configuração

Você também pode criar um arquivo de configuração personalizado e carregá-lo em tempo de execução.

Exemplo:

```python
import json
from src.interfaces.config_provider import ConfigProvider

class FileConfigProvider(ConfigProvider):
    def __init__(self, config_file: str):
        self.config = {}
        self.load_config(config_file)
    
    def load_config(self, config_file: str) -> None:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar arquivo de configuração: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.config[key] = value

# Usar o provedor de configuração de arquivo
from src.factory import AutoMeetAIFactory

factory = AutoMeetAIFactory()
config_provider = FileConfigProvider("config.json")
app = factory.create(config_provider=config_provider)
```

Exemplo de arquivo `config.json`:

```json
{
    "assemblyai_api_key": "sua_chave_api_assemblyai",
    "openai_api_key": "sua_chave_api_openai",
    "default_language_code": "pt-br",
    "default_speaker_labels": true,
    "default_speakers_expected": 3,
    "default_output_directory": "output_personalizado",
    "cache_enabled": true,
    "cache_directory": "cache_personalizado",
    "plugins_enabled": true,
    "plugins_directory": "plugins_personalizados"
}
```

Este documento fornece uma referência completa para todas as opções de configuração disponíveis no AutoMeetAI. Para mais informações sobre como usar essas configurações, consulte os [Exemplos de Uso](usage_examples.md) e o [Guia do Desenvolvedor](developer_guide.md).
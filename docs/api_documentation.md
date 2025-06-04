# Documentação da API do AutoMeetAI

Esta documentação fornece informações detalhadas sobre as classes e métodos disponíveis na API do AutoMeetAI.

## Índice

1. [Classe Principal](#classe-principal)
2. [Serviços de Transcrição](#serviços-de-transcrição)
3. [Serviços de Geração de Texto](#serviços-de-geração-de-texto)
4. [Conversores de Áudio](#conversores-de-áudio)
5. [Modelos de Dados](#modelos-de-dados)
6. [Formatadores de Saída](#formatadores-de-saída)
7. [Utilitários](#utilitários)
8. [Interfaces](#interfaces)

## Classe Principal

### AutoMeetAI

A classe principal que coordena o processamento de vídeos, transcrição e análise.

```python
from src.factory import AutoMeetAIFactory

# Criar uma instância do AutoMeetAI
factory = AutoMeetAIFactory()
app = factory.create()

# Processar um vídeo
transcription = app.process_video("caminho/para/video.mp4")

# Analisar a transcrição
analysis = app.analyze_transcription(
    transcription=transcription,
    system_prompt="Você é um assistente que analisa transcrições de reuniões.",
    user_prompt_template="Por favor, analise a seguinte transcrição e forneça um resumo, pontos-chave e itens de ação:\n\n{transcription}"
)
```

#### Métodos

##### `process_video`

```python
def process_video(
    self, 
    video_file: str, 
    transcription_config: Optional[Dict[str, Any]] = None,
    save_audio: bool = False,
    allowed_video_extensions: Optional[List[str]] = None,
    force_reprocess: bool = False,
    output_format: str = "txt",
    output_formats: Optional[List[str]] = None,
    format_options: Optional[Dict[str, Dict[str, Any]]] = None,
    progress_callback: Optional[Callable[[str, Union[int, float], Union[int, float]], None]] = None
) -> Union[TranscriptionResult, None]
```

Processa um arquivo de vídeo, convertendo-o para áudio e transcrevendo-o.

**Parâmetros:**
- `video_file`: Caminho para o arquivo de vídeo a ser processado
- `transcription_config`: Configuração opcional para o serviço de transcrição
- `save_audio`: Se True, salva o arquivo de áudio intermediário
- `allowed_video_extensions`: Lista opcional de extensões de vídeo permitidas
- `force_reprocess`: Se True, força o reprocessamento mesmo se existir um resultado em cache
- `output_format`: Formato de saída padrão (txt, json, html)
- `output_formats`: Lista opcional de formatos de saída para gerar
- `format_options`: Opções específicas para cada formato de saída
- `progress_callback`: Função de callback para reportar progresso

**Retorna:**
- `TranscriptionResult`: O resultado da transcrição, ou None se falhou

##### `process_videos`

```python
def process_videos(
    self, 
    video_files: List[str],
    transcription_config: Optional[Dict[str, Any]] = None,
    save_audio: bool = False,
    allowed_video_extensions: Optional[List[str]] = None,
    force_reprocess: bool = False,
    output_format: str = "txt",
    output_formats: Optional[List[str]] = None,
    format_options: Optional[Dict[str, Dict[str, Any]]] = None,
    continue_on_error: bool = True,
    progress_callback: Optional[Callable[[str, Union[int, float], Union[int, float]], None]] = None
) -> List[Tuple[str, Optional[TranscriptionResult]]]
```

Processa múltiplos arquivos de vídeo em lote.

**Parâmetros:**
- `video_files`: Lista de caminhos para os arquivos de vídeo a serem processados
- `transcription_config`: Configuração opcional para o serviço de transcrição
- `save_audio`: Se True, salva os arquivos de áudio intermediários
- `allowed_video_extensions`: Lista opcional de extensões de vídeo permitidas
- `force_reprocess`: Se True, força o reprocessamento mesmo se existir um resultado em cache
- `output_format`: Formato de saída padrão (txt, json, html)
- `output_formats`: Lista opcional de formatos de saída para gerar
- `format_options`: Opções específicas para cada formato de saída
- `continue_on_error`: Se True, continua processando mesmo se ocorrer um erro em um arquivo
- `progress_callback`: Função de callback para reportar progresso

**Retorna:**
- `List[Tuple[str, Optional[TranscriptionResult]]]`: Lista de tuplas contendo o caminho do arquivo e o resultado da transcrição (ou None se falhou)

##### `analyze_transcription`

```python
def analyze_transcription(
    self, 
    transcription: TranscriptionResult,
    system_prompt: str,
    user_prompt_template: str,
    generation_options: Optional[Dict[str, Any]] = None
) -> Optional[str]
```

Analisa uma transcrição usando um serviço de geração de texto.

**Parâmetros:**
- `transcription`: O resultado da transcrição a ser analisado
- `system_prompt`: O prompt do sistema para o modelo de geração de texto
- `user_prompt_template`: O template do prompt do usuário, com {transcription} como placeholder
- `generation_options`: Opções adicionais para o serviço de geração de texto

**Retorna:**
- `str`: O texto da análise gerada, ou None se falhou

## Serviços de Transcrição

### TranscriptionService (Interface)

Interface para serviços de transcrição de áudio.

#### Métodos

##### `transcribe`

```python
@abstractmethod
def transcribe(
    self, 
    audio_file: str, 
    config: Optional[Dict[str, Any]] = None,
    allowed_audio_extensions: Optional[List[str]] = None
) -> Union[TranscriptionResult, None]
```

Transcreve um arquivo de áudio para texto.

**Parâmetros:**
- `audio_file`: Caminho para o arquivo de áudio a ser transcrito
- `config`: Parâmetros de configuração opcionais para a transcrição
- `allowed_audio_extensions`: Lista opcional de extensões de arquivo de áudio permitidas

**Retorna:**
- `TranscriptionResult`: O resultado da transcrição, ou None se falhou

### AssemblyAITranscriptionService

Implementação do serviço de transcrição usando AssemblyAI.

### WhisperTranscriptionService

Implementação do serviço de transcrição usando OpenAI Whisper.

### MockTranscriptionService

Implementação de demonstração do serviço de transcrição que não requer API externa.

## Serviços de Transcrição em Streaming

### StreamingTranscriptionService (Interface)

Interface para serviços de transcrição de áudio em tempo real.

#### Métodos

##### `start_streaming`

```python
@abstractmethod
def start_streaming(self, config: Optional[Dict[str, Any]] = None) -> bool
```

Inicia uma sessão de transcrição em streaming.

**Parâmetros:**
- `config`: Parâmetros de configuração opcionais para a transcrição

**Retorna:**
- `bool`: True se a sessão foi iniciada com sucesso, False caso contrário

##### `transcribe_chunk`

```python
@abstractmethod
def transcribe_chunk(self, audio_chunk: bytes) -> Optional[Dict[str, Any]]
```

Transcreve um fragmento de áudio em tempo real.

**Parâmetros:**
- `audio_chunk`: Fragmento de áudio em bytes para transcrever

**Retorna:**
- `Optional[Dict[str, Any]]`: Resultado parcial da transcrição, ou None se falhou

##### `stop_streaming`

```python
@abstractmethod
def stop_streaming(self) -> Optional[TranscriptionResult]
```

Finaliza a sessão de transcrição em streaming e retorna o resultado completo.

**Retorna:**
- `Optional[TranscriptionResult]`: O resultado completo da transcrição, ou None se falhou

##### `is_streaming`

```python
@abstractmethod
def is_streaming(self) -> bool
```

Verifica se uma sessão de streaming está ativa.

**Retorna:**
- `bool`: True se uma sessão de streaming está ativa, False caso contrário

##### `stream_microphone`

```python
@abstractmethod
def stream_microphone(
    self, 
    callback: Callable[[Dict[str, Any]], None],
    duration: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None
) -> Optional[TranscriptionResult]
```

Captura áudio do microfone e transcreve em tempo real.

**Parâmetros:**
- `callback`: Função de callback chamada com cada resultado parcial
- `duration`: Duração máxima da captura em segundos, ou None para continuar até ser interrompido
- `config`: Parâmetros de configuração opcionais para a transcrição

**Retorna:**
- `Optional[TranscriptionResult]`: O resultado completo da transcrição, ou None se falhou

### AssemblyAIStreamingTranscriptionService

Implementação do serviço de transcrição em streaming usando AssemblyAI.

## Serviços de Geração de Texto

### TextGenerationService (Interface)

Interface para serviços de geração de texto.

#### Métodos

##### `generate`

```python
@abstractmethod
def generate(
    self, 
    system_prompt: str,
    user_prompt: str,
    options: Optional[Dict[str, Any]] = None
) -> Optional[str]
```

Gera texto com base em prompts do sistema e do usuário.

**Parâmetros:**
- `system_prompt`: O prompt do sistema para o modelo
- `user_prompt`: O prompt do usuário para o modelo
- `options`: Opções adicionais para a geração de texto

**Retorna:**
- `str`: O texto gerado, ou None se falhou

### OpenAITextGenerationService

Implementação do serviço de geração de texto usando OpenAI.

### NullTextGenerationService

Implementação do serviço de geração de texto que não faz nada (para quando a análise não é necessária).

## Conversores de Áudio

### AudioConverter (Interface)

Interface para conversores de áudio.

#### Métodos

##### `convert_to_audio`

```python
@abstractmethod
def convert_to_audio(
    self, 
    video_file: str,
    output_file: Optional[str] = None,
    allowed_input_extensions: Optional[List[str]] = None,
    allowed_output_extensions: Optional[List[str]] = None,
    **kwargs
) -> Optional[str]
```

Converte um arquivo de vídeo para áudio.

**Parâmetros:**
- `video_file`: Caminho para o arquivo de vídeo a ser convertido
- `output_file`: Caminho opcional para o arquivo de áudio de saída
- `allowed_input_extensions`: Lista opcional de extensões de entrada permitidas
- `allowed_output_extensions`: Lista opcional de extensões de saída permitidas
- `**kwargs`: Argumentos adicionais para o conversor

**Retorna:**
- `str`: Caminho para o arquivo de áudio gerado, ou None se falhou

### MoviePyAudioConverter

Implementação do conversor de áudio usando MoviePy.

## Modelos de Dados

### TranscriptionResult

Representa o resultado de uma transcrição.

#### Atributos

- `utterances`: Lista de falas na transcrição
- `text`: Texto completo da transcrição
- `audio_file`: Caminho para o arquivo de áudio transcrito

#### Métodos

##### `to_formatted_text`

```python
def to_formatted_text(self) -> str
```

Converte o resultado da transcrição para um texto formatado.

**Retorna:**
- `str`: O texto formatado da transcrição

##### `format`

```python
def format(self, format_name: str, options: Optional[Dict[str, Any]] = None) -> str
```

Formata o resultado da transcrição no formato especificado.

**Parâmetros:**
- `format_name`: Nome do formato (text, json, html, etc.)
- `options`: Opções de formatação específicas para o formatador

**Retorna:**
- `str`: O resultado formatado

##### `save_to_file`

```python
def save_to_file(
    self, 
    output_file: str, 
    format_name: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> bool
```

Salva o resultado da transcrição em um arquivo.

**Parâmetros:**
- `output_file`: Caminho onde a transcrição deve ser salva
- `format_name`: Nome do formato (text, json, html, etc.). Se None, será inferido da extensão do arquivo
- `options`: Opções de formatação específicas para o formatador

**Retorna:**
- `bool`: True se o arquivo foi salvo com sucesso, False caso contrário

### Utterance

Representa uma única fala em uma transcrição.

#### Atributos

- `speaker`: Identificador do falante
- `text`: Texto da fala
- `start`: Tempo de início da fala em segundos (opcional)
- `end`: Tempo de fim da fala em segundos (opcional)

### StreamingTranscriptionResult

Representa o resultado parcial de uma transcrição em streaming.

#### Atributos

- `text`: Texto da transcrição parcial
- `is_final`: Indica se o resultado é final ou intermediário
- `confidence`: Nível de confiança da transcrição
- `speaker`: Identificador do falante (opcional)
- `start_time`: Tempo de início em segundos (opcional)
- `end_time`: Tempo de fim em segundos (opcional)

### StreamingSession

Representa uma sessão de transcrição em streaming.

#### Métodos

##### `add_result`

```python
def add_result(self, result: StreamingTranscriptionResult) -> None
```

Adiciona um resultado parcial à sessão.

**Parâmetros:**
- `result`: O resultado parcial a ser adicionado

##### `get_current_text`

```python
def get_current_text(self) -> str
```

Obtém o texto atual da transcrição, combinando resultados finais e o último parcial.

**Retorna:**
- `str`: O texto atual da transcrição

##### `to_transcription_result`

```python
def to_transcription_result(self, audio_file: str = "") -> TranscriptionResult
```

Converte a sessão de streaming em um TranscriptionResult.

**Parâmetros:**
- `audio_file`: O caminho para o arquivo de áudio (opcional)

**Retorna:**
- `TranscriptionResult`: O resultado da transcrição

## Formatadores de Saída

### OutputFormatter (Interface)

Interface para formatadores de saída.

#### Métodos

##### `format`

```python
@abstractmethod
def format(
    self, 
    transcription_result: TranscriptionResult,
    options: Optional[Dict[str, Any]] = None
) -> str
```

Formata um resultado de transcrição.

**Parâmetros:**
- `transcription_result`: O resultado da transcrição a ser formatado
- `options`: Opções de formatação específicas

**Retorna:**
- `str`: O resultado formatado

##### `get_file_extension`

```python
@abstractmethod
def get_file_extension(self) -> str
```

Obtém a extensão de arquivo padrão para este formatador.

**Retorna:**
- `str`: A extensão de arquivo padrão (sem o ponto)

### TextFormatter

Formatador para saída em texto simples.

### JSONFormatter

Formatador para saída em JSON.

### HTMLFormatter

Formatador para saída em HTML.

## Utilitários

### TranscriptionCache

Gerencia o cache de resultados de transcrição.

#### Métodos

##### `get`

```python
def get(self, key: str) -> Optional[TranscriptionResult]
```

Obtém um resultado de transcrição do cache.

**Parâmetros:**
- `key`: A chave do cache (geralmente o caminho do arquivo de áudio)

**Retorna:**
- `TranscriptionResult`: O resultado da transcrição, ou None se não estiver no cache

##### `set`

```python
def set(self, key: str, result: TranscriptionResult) -> None
```

Armazena um resultado de transcrição no cache.

**Parâmetros:**
- `key`: A chave do cache (geralmente o caminho do arquivo de áudio)
- `result`: O resultado da transcrição a ser armazenado

### RateLimiter

Limita a taxa de chamadas a APIs externas.

#### Métodos

##### `consume`

```python
def consume(self, tokens: int = 1, wait: bool = False) -> bool
```

Consome tokens do limitador de taxa.

**Parâmetros:**
- `tokens`: Número de tokens a consumir
- `wait`: Se True, aguarda até que os tokens estejam disponíveis

**Retorna:**
- `bool`: True se os tokens foram consumidos, False caso contrário

## Interfaces

### ConfigProvider (Interface)

Interface para provedores de configuração.

#### Métodos

##### `get`

```python
@abstractmethod
def get(self, key: str, default: Any = None) -> Any
```

Obtém um valor de configuração.

**Parâmetros:**
- `key`: A chave da configuração
- `default`: Valor padrão se a chave não existir

**Retorna:**
- O valor da configuração, ou o valor padrão se a chave não existir

##### `set`

```python
@abstractmethod
def set(self, key: str, value: Any) -> None
```

Define um valor de configuração.

**Parâmetros:**
- `key`: A chave da configuração
- `value`: O valor a ser definido

### Plugin (Interface)

Interface para plugins.

#### Métodos

##### `get_name`

```python
@abstractmethod
def get_name(self) -> str
```

Obtém o nome do plugin.

**Retorna:**
- `str`: O nome do plugin

##### `get_version`

```python
@abstractmethod
def get_version(self) -> str
```

Obtém a versão do plugin.

**Retorna:**
- `str`: A versão do plugin

##### `get_description`

```python
@abstractmethod
def get_description(self) -> str
```

Obtém a descrição do plugin.

**Retorna:**
- `str`: A descrição do plugin

##### `get_extension_points`

```python
@abstractmethod
def get_extension_points(self) -> List[str]
```

Obtém os pontos de extensão suportados pelo plugin.

**Retorna:**
- `List[str]`: Lista de pontos de extensão suportados

##### `get_implementation`

```python
@abstractmethod
def get_implementation(self, extension_point: str) -> Any
```

Obtém a implementação para um ponto de extensão.

**Parâmetros:**
- `extension_point`: O ponto de extensão

**Retorna:**
- A implementação para o ponto de extensão, ou None se não suportado

## REST API

O AutoMeetAI também disponibiliza uma API REST simples implementada com
[FastAPI](https://fastapi.tiangolo.com/). Essa API permite processar arquivos de
vídeo remotamente e solicitar análises de transcrições.

### Endpoints

| Método | Caminho            | Descrição                                   |
|-------:|--------------------|---------------------------------------------|
| `GET`  | `/health`          | Verifica se o serviço está no ar            |
| `POST` | `/transcriptions`  | Envia um vídeo e retorna a transcrição      |
| `POST` | `/analysis`        | Analisa um texto de transcrição e retorna o resultado |

### Exemplo de uso

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/transcriptions \
     -F "file=@reuniao.mp4" -H "accept: application/json"

curl -X POST http://localhost:8000/analysis \
     -H "Content-Type: application/json" \
     -d '{"text": "Olá mundo"}'
```

Consulte `api.py` para ver a implementação completa da API.

# Guia de Solução de Problemas - AutoMeetAI

Este guia fornece soluções para problemas comuns que você pode encontrar ao usar o AutoMeetAI.

## Índice

1. [Problemas de Instalação](#problemas-de-instalação)
2. [Problemas de Configuração](#problemas-de-configuração)
3. [Problemas de API](#problemas-de-api)
4. [Problemas de Conversão de Áudio](#problemas-de-conversão-de-áudio)
5. [Problemas de Transcrição](#problemas-de-transcrição)
6. [Problemas de Streaming](#problemas-de-streaming)
7. [Problemas de Análise de Texto](#problemas-de-análise-de-texto)
8. [Problemas de Cache](#problemas-de-cache)
9. [Problemas de Plugins](#problemas-de-plugins)
10. [Problemas de CLI](#problemas-de-cli)
11. [Mensagens de Erro Comuns](#mensagens-de-erro-comuns)

## Problemas de Instalação

### Erro ao instalar dependências

**Problema**: Erros ao instalar as dependências do projeto com pip.

**Solução**:
1. Verifique se você está usando Python 3.8 ou superior:
   ```bash
   python --version
   ```

2. Tente instalar as dependências uma por uma:
   ```bash
   pip install moviepy
   pip install assemblyai
   pip install openai
   ```

3. Se você estiver tendo problemas com o MoviePy, pode ser necessário instalar o FFmpeg:
   - Windows: Baixe o FFmpeg de [ffmpeg.org](https://ffmpeg.org/download.html) e adicione-o ao PATH.
   - Ou use: `pip install imageio-ffmpeg`

4. Se você estiver em um ambiente virtual, certifique-se de que ele está ativado:
   ```bash
   # Windows
   .venv\Scripts\activate
   ```

### Erro ao importar módulos

**Problema**: Erros de importação ao executar o código.

**Solução**:
1. Verifique se você está executando o código a partir do diretório raiz do projeto.
2. Verifique se todas as dependências estão instaladas:
   ```bash
   pip install -r requirements.txt
   ```
3. Se você estiver usando um IDE, configure o diretório raiz do projeto como o diretório de trabalho.

## Problemas de Configuração

### Chaves de API não encontradas

**Problema**: Erros indicando que as chaves de API não foram encontradas.

**Solução**:
1. Verifique se você definiu as variáveis de ambiente corretamente:
   ```bash
   # Windows PowerShell
   $env:AUTOMEETAI_ASSEMBLYAI_API_KEY = "sua_chave_api_assemblyai"
   $env:AUTOMEETAI_OPENAI_API_KEY = "sua_chave_api_openai"
   
   # Windows Command Prompt
   set AUTOMEETAI_ASSEMBLYAI_API_KEY=sua_chave_api_assemblyai
   set AUTOMEETAI_OPENAI_API_KEY=sua_chave_api_openai
   ```

2. Ou passe as chaves diretamente ao criar a instância do AutoMeetAI:
   ```python
   from src.factory import AutoMeetAIFactory
   
   factory = AutoMeetAIFactory()
   app = factory.create(
       assemblyai_api_key="sua_chave_api_assemblyai",
       openai_api_key="sua_chave_api_openai"
   )
   ```

3. Verifique se as chaves são válidas acessando os respectivos dashboards:
   - [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard)
   - [OpenAI Dashboard](https://platform.openai.com/account/api-keys)

### Configurações personalizadas não aplicadas

**Problema**: As configurações personalizadas não estão sendo aplicadas.

**Solução**:
1. Verifique se você está passando as configurações no nível correto:
   - Configurações globais: Passe para o método `create()` da fábrica.
   - Configurações de transcrição: Passe para o parâmetro `transcription_config` do método `process_video()`.

2. Verifique se as chaves de configuração estão corretas. Consulte a [documentação de configuração](configuration.md).

3. Se você estiver usando um provedor de configuração personalizado, verifique se o método `get()` está implementado corretamente.

## Problemas de API

### Erros de autenticação da API

**Problema**: Erros de autenticação ao chamar APIs externas.

**Solução**:
1. Verifique se as chaves de API estão corretas e não expiradas.
2. Verifique se você tem saldo suficiente na sua conta (para APIs pagas).
3. Verifique se você está usando o endpoint correto da API.
4. Verifique se a API está disponível (consulte o status da API).

### Erros de limite de taxa (Rate Limit)

**Problema**: Erros indicando que você excedeu o limite de taxa da API.

**Solução**:
1. Reduza a frequência das chamadas à API.
2. Aumente os valores de configuração de limitação de taxa:
   ```python
   # Em src/config/default_config.py
   ASSEMBLYAI_RATE_LIMIT = 0.1  # Reduzir para menos requisições por segundo
   ASSEMBLYAI_RATE_LIMIT_BURST = 3  # Reduzir o número de rajadas permitidas
   ```
3. Implemente um mecanismo de retry com backoff exponencial.
4. Considere atualizar seu plano de API para obter limites mais altos.

### Erros de rede

**Problema**: Erros de conexão ou timeout ao chamar APIs externas.

**Solução**:
1. Verifique sua conexão com a internet.
2. Verifique se você está atrás de um proxy ou firewall que pode estar bloqueando as chamadas.
3. Aumente o timeout das chamadas à API.
4. Implemente um mecanismo de retry para lidar com falhas temporárias de rede.

## Problemas de Conversão de Áudio

### Erro ao converter vídeo para áudio

**Problema**: Erros ao converter arquivos de vídeo para áudio.

**Solução**:
1. Verifique se o FFmpeg está instalado e acessível no PATH:
   ```bash
   ffmpeg -version
   ```

2. Verifique se o arquivo de vídeo existe e não está corrompido:
   ```python
   import os
   if os.path.exists("video.mp4") and os.path.getsize("video.mp4") > 0:
       print("O arquivo existe e não está vazio")
   ```

3. Tente converter o vídeo manualmente com FFmpeg:
   ```bash
   ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3
   ```

4. Verifique se o formato do vídeo é suportado. Consulte a lista de formatos suportados em `DEFAULT_ALLOWED_INPUT_EXTENSIONS`.

### Qualidade de áudio ruim

**Problema**: A qualidade do áudio convertido é ruim, afetando a transcrição.

**Solução**:
1. Aumente a taxa de bits do áudio:
   ```python
   # Em src/config/default_config.py
   DEFAULT_AUDIO_BITRATE = "192k"  # Aumentar a taxa de bits
   ```

2. Aumente a taxa de amostragem:
   ```python
   # Em src/config/default_config.py
   DEFAULT_AUDIO_FPS = 48000  # Aumentar a taxa de amostragem
   ```

3. Use um formato de áudio sem perdas como WAV em vez de MP3:
   ```python
   from src.factory import AutoMeetAIFactory
   
   factory = AutoMeetAIFactory()
   app = factory.create()
   
   # Especificar formato de saída WAV
   transcription = app.process_video(
       video_file="video.mp4",
       transcription_config={"audio_format": "wav"}
   )
   ```

4. Pré-processe o áudio para reduzir ruído antes da transcrição.

## Problemas de Transcrição

### Transcrição com baixa precisão

**Problema**: A transcrição não está precisa, com muitas palavras incorretas.

**Solução**:
1. Verifique se o idioma correto está configurado:
   ```python
   transcription_config = {
       "language_code": "pt-br"  # Ou o idioma correto do áudio
   }
   ```

2. Melhore a qualidade do áudio (veja a seção anterior).

3. Tente um serviço de transcrição diferente:
   ```python
   from src.factory import AutoMeetAIFactory
   
   factory = AutoMeetAIFactory()
   app = factory.create(transcription_service_type="whisper")  # Usar Whisper em vez de AssemblyAI
   ```

4. Para áudios com sotaques ou terminologia específica, considere treinar um modelo personalizado (se o serviço suportar).

### Falantes não identificados corretamente

**Problema**: Os falantes não estão sendo identificados corretamente na transcrição.

**Solução**:
1. Verifique se a detecção de falantes está habilitada:
   ```python
   transcription_config = {
       "speaker_labels": True
   }
   ```

2. Especifique o número esperado de falantes:
   ```python
   transcription_config = {
       "speaker_labels": True,
       "speakers_expected": 3  # Ajuste para o número correto de falantes
   }
   ```

3. Melhore a qualidade do áudio, especialmente se houver muito ruído de fundo.

4. Certifique-se de que os falantes estão claramente audíveis e não falam ao mesmo tempo.

### Transcrição incompleta

**Problema**: A transcrição está incompleta, faltando partes do áudio.

**Solução**:
1. Verifique se o arquivo de áudio não está corrompido.
2. Verifique se o arquivo de áudio não é muito grande (alguns serviços têm limites).
3. Divida arquivos grandes em partes menores e processe-os separadamente.
4. Verifique se não há limites de tempo ou tamanho no serviço de transcrição que você está usando.

## Problemas de Streaming

### Erro ao iniciar streaming

**Problema**: Erros ao iniciar a transcrição em streaming.

**Solução**:
1. Verifique se o microfone está conectado e funcionando:
   ```python
   import pyaudio
   
   p = pyaudio.PyAudio()
   info = p.get_host_api_info_by_index(0)
   num_devices = info.get('deviceCount')
   
   for i in range(num_devices):
       if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
           print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
   ```

2. Verifique se você tem as permissões necessárias para acessar o microfone.

3. Verifique se o PyAudio está instalado corretamente:
   ```bash
   pip install pyaudio
   ```

4. Em Windows, pode ser necessário instalar o Microsoft Visual C++ Redistributable.

### Transcrição em streaming lenta ou com atrasos

**Problema**: A transcrição em streaming está lenta ou com atrasos significativos.

**Solução**:
1. Verifique sua conexão com a internet.
2. Reduza a qualidade do áudio para diminuir o tamanho dos dados:
   ```python
   config = {
       "sample_rate": 8000,  # Reduzir a taxa de amostragem
       "channels": 1  # Usar mono em vez de estéreo
   }
   ```

3. Aumente o tamanho do fragmento de áudio:
   ```python
   # Em src/services/assemblyai_streaming_transcription_service.py
   CHUNK = 2048  # Aumentar o tamanho do fragmento
   ```

4. Verifique se não há outros processos consumindo muita largura de banda.

## Problemas de Análise de Texto

### Análise de texto falha

**Problema**: A análise de texto com OpenAI falha.

**Solução**:
1. Verifique se a chave de API do OpenAI é válida.
2. Verifique se você tem créditos suficientes na sua conta OpenAI.
3. Verifique se o modelo especificado existe e está disponível:
   ```python
   # Em src/config/default_config.py
   OPENAI_MODEL = "gpt-4o-2024-08-06"  # Verifique se este modelo está disponível
   ```

4. Reduza o tamanho do texto se estiver excedendo o limite de tokens do modelo.

### Análise de texto de baixa qualidade

**Problema**: A análise de texto não está fornecendo resultados úteis.

**Solução**:
1. Melhore o prompt do sistema:
   ```python
   system_prompt = """
   Você é um assistente especializado em analisar transcrições de reuniões de negócios.
   Sua tarefa é extrair informações importantes, incluindo:
   1. Um resumo executivo (máximo 3 parágrafos)
   2. Pontos-chave discutidos
   3. Decisões tomadas
   4. Itens de ação com responsáveis
   5. Próximos passos
   
   Seja conciso e focado nos aspectos mais importantes da reunião.
   """
   ```

2. Melhore o prompt do usuário:
   ```python
   user_prompt_template = """
   Por favor, analise a seguinte transcrição de reunião:
   
   {transcription}
   
   Forneça sua análise no seguinte formato:
   
   ## Resumo Executivo
   
   ## Pontos-Chave
   
   ## Decisões Tomadas
   
   ## Itens de Ação
   
   ## Próximos Passos
   """
   ```

3. Experimente um modelo diferente ou com mais capacidade.

## Problemas de Cache

### Cache não funciona

**Problema**: O cache de transcrição não está funcionando, resultando em reprocessamento desnecessário.

**Solução**:
1. Verifique se o cache está habilitado:
   ```python
   from src.factory import AutoMeetAIFactory
   
   factory = AutoMeetAIFactory()
   app = factory.create(use_cache=True)
   ```

2. Verifique se o diretório de cache existe e tem permissões de escrita:
   ```python
   import os
   
   cache_dir = "cache"
   if not os.path.exists(cache_dir):
       os.makedirs(cache_dir)
   ```

3. Verifique se você não está usando `force_reprocess=True`:
   ```python
   # Não use force_reprocess a menos que necessário
   transcription = app.process_video(
       video_file="video.mp4",
       force_reprocess=False
   )
   ```

4. Verifique se o cache não está corrompido. Tente limpar o diretório de cache.

### Cache ocupa muito espaço

**Problema**: O cache está ocupando muito espaço em disco.

**Solução**:
1. Limpe o cache periodicamente:
   ```python
   import os
   import shutil
   
   cache_dir = "cache"
   if os.path.exists(cache_dir):
       shutil.rmtree(cache_dir)
       os.makedirs(cache_dir)
   ```

2. Implemente uma política de expiração de cache:
   ```python
   import os
   import time
   
   cache_dir = "cache"
   max_age = 7 * 24 * 60 * 60  # 7 dias em segundos
   
   for file in os.listdir(cache_dir):
       file_path = os.path.join(cache_dir, file)
       if os.path.isfile(file_path):
           file_age = time.time() - os.path.getmtime(file_path)
           if file_age > max_age:
               os.remove(file_path)
   ```

3. Use um formato de cache mais eficiente em termos de espaço.

## Problemas de Plugins

### Plugins não carregados

**Problema**: Os plugins não estão sendo carregados.

**Solução**:
1. Verifique se os plugins estão no diretório correto:
   ```python
   from src.factory import AutoMeetAIFactory
   
   factory = AutoMeetAIFactory()
   factory.load_plugins(plugin_dir="plugins")  # Especifique o diretório correto
   ```

2. Verifique se os plugins implementam a interface `Plugin` corretamente.

3. Verifique se não há erros de sintaxe nos arquivos de plugin.

4. Habilite o logging detalhado para ver mensagens de erro durante o carregamento de plugins:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Plugins causam erros

**Problema**: Os plugins estão causando erros durante a execução.

**Solução**:
1. Desabilite os plugins para verificar se o problema persiste:
   ```python
   from src.factory import AutoMeetAIFactory
   
   factory = AutoMeetAIFactory()
   app = factory.create(use_plugins=False)
   ```

2. Verifique os logs de erro para identificar qual plugin está causando o problema.

3. Atualize ou corrija o plugin problemático.

4. Se necessário, entre em contato com o desenvolvedor do plugin.

## Problemas de CLI

### Argumentos de linha de comando não reconhecidos

**Problema**: Argumentos de linha de comando não estão sendo reconhecidos.

**Solução**:
1. Verifique a sintaxe dos argumentos:
   ```bash
   python main.py --help
   ```

2. Certifique-se de que está usando os argumentos corretos conforme documentado.

3. Verifique se não há conflitos entre argumentos.

4. Se você estiver usando um shell personalizado, verifique se os argumentos estão sendo passados corretamente.

### Erro ao processar múltiplos arquivos

**Problema**: Erros ao processar múltiplos arquivos em lote.

**Solução**:
1. Use a opção `--continue-on-error` para continuar processando mesmo se um arquivo falhar:
   ```bash
   python main.py --batch *.mp4 --continue-on-error
   ```

2. Verifique se todos os arquivos existem e são válidos.

3. Processe os arquivos em grupos menores se houver muitos.

4. Verifique se há memória suficiente para processar todos os arquivos.

## Mensagens de Erro Comuns

### "AssemblyAI API key is required"

**Problema**: A chave de API do AssemblyAI não foi fornecida.

**Solução**:
1. Defina a variável de ambiente:
   ```bash
   # Windows PowerShell
   $env:AUTOMEETAI_ASSEMBLYAI_API_KEY = "sua_chave_api_assemblyai"
   
   # Windows Command Prompt
   set AUTOMEETAI_ASSEMBLYAI_API_KEY=sua_chave_api_assemblyai
   ```

2. Ou passe a chave diretamente:
   ```python
   from src.factory import AutoMeetAIFactory
   
   factory = AutoMeetAIFactory()
   app = factory.create(assemblyai_api_key="sua_chave_api_assemblyai")
   ```

### "OpenAI API key is required"

**Problema**: A chave de API do OpenAI não foi fornecida.

**Solução**:
1. Defina a variável de ambiente:
   ```bash
   # Windows PowerShell
   $env:AUTOMEETAI_OPENAI_API_KEY = "sua_chave_api_openai"
   
   # Windows Command Prompt
   set AUTOMEETAI_OPENAI_API_KEY=sua_chave_api_openai
   ```

2. Ou passe a chave diretamente:
   ```python
   from src.factory import AutoMeetAIFactory
   
   factory = AutoMeetAIFactory()
   app = factory.create(openai_api_key="sua_chave_api_openai")
   ```

3. Se você não precisa de análise de texto, desabilite o serviço de geração de texto:
   ```python
   from src.factory import AutoMeetAIFactory
   
   factory = AutoMeetAIFactory()
   app = factory.create(include_text_generation=False)
   ```

### "File not found" ou "Invalid file path"

**Problema**: O arquivo especificado não foi encontrado ou o caminho é inválido.

**Solução**:
1. Verifique se o arquivo existe:
   ```python
   import os
   
   file_path = "video.mp4"
   if not os.path.exists(file_path):
       print(f"O arquivo {file_path} não existe")
   ```

2. Use caminhos absolutos em vez de relativos:
   ```python
   import os
   
   file_path = os.path.abspath("video.mp4")
   print(f"Caminho absoluto: {file_path}")
   ```

3. Verifique se o nome do arquivo não contém caracteres especiais ou espaços.

4. Verifique as permissões do arquivo.

### "Unsupported file format"

**Problema**: O formato do arquivo não é suportado.

**Solução**:
1. Verifique se a extensão do arquivo está na lista de extensões permitidas:
   ```python
   # Em src/config/default_config.py
   DEFAULT_ALLOWED_INPUT_EXTENSIONS = ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "mp3", "wav", "ogg", "flac", "m4v", "3gp", "mpg", "mpeg", "ts", "m2ts", "vob", "ogv", "divx", "aac", "m4a", "wma", "aiff", "ac3", "amr"]
   ```

2. Converta o arquivo para um formato suportado:
   ```bash
   ffmpeg -i video.unsupported -c:v libx264 -c:a aac video.mp4
   ```

3. Especifique manualmente as extensões permitidas:
   ```python
   transcription = app.process_video(
       video_file="video.custom",
       allowed_video_extensions=["custom", "mp4", "avi"]
   )
   ```

### "Rate limit exceeded"

**Problema**: O limite de taxa da API foi excedido.

**Solução**:
1. Aguarde um pouco antes de tentar novamente.
2. Reduza a frequência das chamadas à API.
3. Aumente os valores de configuração de limitação de taxa (veja a seção "Erros de limite de taxa").
4. Considere atualizar seu plano de API para obter limites mais altos.

### "No microphone found" ou "Error accessing microphone"

**Problema**: Não foi possível acessar o microfone para streaming.

**Solução**:
1. Verifique se o microfone está conectado e funcionando.
2. Verifique se você tem as permissões necessárias para acessar o microfone.
3. Tente usar um dispositivo de microfone diferente:
   ```python
   import pyaudio
   
   p = pyaudio.PyAudio()
   stream = p.open(
       format=pyaudio.paInt16,
       channels=1,
       rate=16000,
       input=True,
       input_device_index=1  # Especifique o índice do dispositivo
   )
   ```

4. Reinicie o computador para liberar recursos de áudio.

Se você continuar enfrentando problemas após tentar estas soluções, consulte a [documentação da API](api_documentation.md) e os [exemplos de uso](usage_examples.md) para mais informações. Se o problema persistir, entre em contato com o suporte ou abra uma issue no repositório do projeto.
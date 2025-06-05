# Guia do Desenvolvedor - AutoMeetAI

Este guia fornece instruções detalhadas para desenvolvedores que desejam estender ou modificar o AutoMeetAI.

## Índice

1. [Arquitetura do Sistema](#arquitetura-do-sistema)
2. [Princípios de Design](#princípios-de-design)
3. [Adicionando um Novo Serviço de Transcrição](#adicionando-um-novo-serviço-de-transcrição)
4. [Adicionando um Novo Conversor de Áudio](#adicionando-um-novo-conversor-de-áudio)
5. [Adicionando um Novo Serviço de Geração de Texto](#adicionando-um-novo-serviço-de-geração-de-texto)
6. [Adicionando um Novo Formatador de Saída](#adicionando-um-novo-formatador-de-saída)
7. [Criando um Plugin](#criando-um-plugin)
8. [Estendendo o CLI](#estendendo-o-cli)
9. [Melhores Práticas](#melhores-práticas)
10. [Arquitetura de Microsserviços](#arquitetura-de-microsservicos)

## Arquitetura do Sistema

O AutoMeetAI segue uma arquitetura modular baseada em interfaces e injeção de dependência. Os principais componentes são:

1. **AutoMeetAI**: A classe principal que coordena o fluxo de trabalho.
2. **Serviços de Transcrição**: Implementações da interface `TranscriptionService` que convertem áudio em texto.
3. **Conversores de Áudio**: Implementações da interface `AudioConverter` que convertem vídeo em áudio.
4. **Serviços de Geração de Texto**: Implementações da interface `TextGenerationService` que analisam transcrições.
5. **Formatadores de Saída**: Implementações da interface `OutputFormatter` que formatam os resultados.
6. **Provedores de Configuração**: Implementações da interface `ConfigProvider` que fornecem configurações.
7. **Plugins**: Implementações da interface `Plugin` que estendem a funcionalidade.

O diagrama abaixo ilustra a arquitetura de alto nível:

```
+----------------+     +----------------------+     +------------------------+
|                |     |                      |     |                        |
| AutoMeetAI     |---->| AudioConverter      |---->| TranscriptionService   |
|                |     |                      |     |                        |
+----------------+     +----------------------+     +------------------------+
        |                                                     |
        |                                                     |
        v                                                     v
+----------------+     +----------------------+     +------------------------+
|                |     |                      |     |                        |
| ConfigProvider |     | TextGenerationService|<----| TranscriptionResult   |
|                |     |                      |     |                        |
+----------------+     +----------------------+     +------------------------+
                                |
                                |
                                v
                       +----------------------+
                       |                      |
                       | OutputFormatter      |
                       |                      |
                       +----------------------+
```

## Princípios de Design

O AutoMeetAI segue os princípios SOLID:

1. **Princípio da Responsabilidade Única (SRP)**: Cada classe tem uma única responsabilidade.
2. **Princípio Aberto/Fechado (OCP)**: As classes são abertas para extensão, mas fechadas para modificação.
3. **Princípio da Substituição de Liskov (LSP)**: As implementações de interfaces podem ser substituídas sem afetar o comportamento.
4. **Princípio da Segregação de Interface (ISP)**: As interfaces são específicas para os clientes.
5. **Princípio da Inversão de Dependência (DIP)**: Dependa de abstrações, não de implementações concretas.

Ao estender o AutoMeetAI, siga esses princípios para manter a qualidade e a manutenibilidade do código.

## Adicionando um Novo Serviço de Transcrição

Para adicionar um novo serviço de transcrição, siga estes passos:

1. Crie uma nova classe que implemente a interface `TranscriptionService`:

```python
from typing import Optional, Dict, Any, List, Union
from src.interfaces.transcription_service import TranscriptionService
from src.interfaces.config_provider import ConfigProvider
from src.models.transcription_result import TranscriptionResult
from src.utils.logging import get_logger

class MeuServicoTranscricao(TranscriptionService):
    """
    Implementação do serviço de transcrição usando Meu Serviço.
    """
    
    # Inicializa o logger para esta classe
    logger = get_logger(__name__)
    
    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """
        Inicializa o serviço de transcrição.
        
        Args:
            config_provider: Provedor de configuração opcional
        """
        self.config_provider = config_provider
        # Inicialize aqui quaisquer recursos necessários
        
    def transcribe(self, audio_file: str, config: Optional[Dict[str, Any]] = None,
                 allowed_audio_extensions: Optional[List[str]] = None) -> Union[TranscriptionResult, None]:
        """
        Transcreve um arquivo de áudio para texto.
        
        Args:
            audio_file: Caminho para o arquivo de áudio a ser transcrito
            config: Parâmetros de configuração opcionais para a transcrição
            allowed_audio_extensions: Lista opcional de extensões de arquivo de áudio permitidas
            
        Returns:
            TranscriptionResult: O resultado da transcrição, ou None se falhou
        """
        try:
            # Implemente a lógica de transcrição aqui
            # ...
            
            # Crie e retorne um objeto TranscriptionResult
            return TranscriptionResult(
                utterances=[...],  # Lista de objetos Utterance
                text="Texto completo da transcrição",
                audio_file=audio_file
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao transcrever arquivo: {e}")
            return None
```

2. Se necessário, crie um adaptador para converter o formato de saída do seu serviço para o formato `TranscriptionResult`:

```python
from typing import Any
from src.models.transcription_result import TranscriptionResult, Utterance

class MeuServicoAdapter:
    """
    Adaptador para converter transcrições do Meu Serviço para o modelo TranscriptionResult.
    """
    
    @staticmethod
    def convert(resultado_meu_servico: Any, audio_file: str) -> TranscriptionResult:
        """
        Converte um resultado do Meu Serviço para o modelo TranscriptionResult.
        
        Args:
            resultado_meu_servico: O objeto de resultado do Meu Serviço
            audio_file: O caminho para o arquivo de áudio que foi transcrito
            
        Returns:
            TranscriptionResult: Uma nova instância de TranscriptionResult
        """
        # Implemente a lógica de conversão aqui
        # ...
        
        return TranscriptionResult(
            utterances=[...],  # Lista de objetos Utterance convertidos
            text="Texto completo da transcrição",
            audio_file=audio_file
        )
```

3. Atualize a fábrica para suportar o novo serviço:

```python
# Em src/factory.py

from src.services.meu_servico_transcricao import MeuServicoTranscricao

# Na classe AutoMeetAIFactory, método create:
if transcription_service_type.lower() == "meu_servico":
    transcription_service_class = MeuServicoTranscricao
```

4. Atualize a configuração padrão para incluir opções para o seu serviço:

```python
# Em src/config/default_config.py

# Configuração do Meu Serviço
MEU_SERVICO_API_KEY = None  # Deve ser definido via variável de ambiente AUTOMEETAI_MEU_SERVICO_API_KEY
MEU_SERVICO_OPCAO1 = "valor_padrao"
MEU_SERVICO_OPCAO2 = True
```

5. Adicione testes para o novo serviço:

```python
# Em tests/test_meu_servico_transcricao.py

import unittest
from unittest.mock import Mock, patch
from src.services.meu_servico_transcricao import MeuServicoTranscricao

class TestMeuServicoTranscricao(unittest.TestCase):
    def setUp(self):
        self.config_provider = Mock()
        self.service = MeuServicoTranscricao(config_provider=self.config_provider)
        
    def test_transcribe_success(self):
        # Teste para o caso de sucesso
        # ...
        
    def test_transcribe_failure(self):
        # Teste para o caso de falha
        # ...
```

## Adicionando um Novo Conversor de Áudio

Para adicionar um novo conversor de áudio, siga estes passos:

1. Crie uma nova classe que implemente a interface `AudioConverter`:

```python
from typing import Optional, List
from src.interfaces.audio_converter import AudioConverter
from src.interfaces.config_provider import ConfigProvider
from src.utils.logging import get_logger

class MeuConversorAudio(AudioConverter):
    """
    Implementação do conversor de áudio usando Minha Biblioteca.
    """
    
    # Inicializa o logger para esta classe
    logger = get_logger(__name__)
    
    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """
        Inicializa o conversor de áudio.
        
        Args:
            config_provider: Provedor de configuração opcional
        """
        self.config_provider = config_provider
        # Inicialize aqui quaisquer recursos necessários
        
    def convert_to_audio(self, video_file: str, output_file: Optional[str] = None,
                        allowed_input_extensions: Optional[List[str]] = None,
                        allowed_output_extensions: Optional[List[str]] = None,
                        **kwargs) -> Optional[str]:
        """
        Converte um arquivo de vídeo para áudio.
        
        Args:
            video_file: Caminho para o arquivo de vídeo a ser convertido
            output_file: Caminho opcional para o arquivo de áudio de saída
            allowed_input_extensions: Lista opcional de extensões de entrada permitidas
            allowed_output_extensions: Lista opcional de extensões de saída permitidas
            **kwargs: Argumentos adicionais para o conversor
            
        Returns:
            str: Caminho para o arquivo de áudio gerado, ou None se falhou
        """
        try:
            # Implemente a lógica de conversão aqui
            # ...
            
            return output_file  # Retorne o caminho para o arquivo de áudio gerado
            
        except Exception as e:
            self.logger.error(f"Erro ao converter vídeo para áudio: {e}")
            return None
```

2. Atualize a fábrica para suportar o novo conversor:

```python
# Em src/factory.py

from src.services.meu_conversor_audio import MeuConversorAudio

# Na classe AutoMeetAIFactory, método create:
# Você pode adicionar uma opção para selecionar o conversor de áudio
if audio_converter_type.lower() == "meu_conversor":
    self.container.register("audio_converter", MeuConversorAudio)
```

3. Adicione testes para o novo conversor:

```python
# Em tests/test_meu_conversor_audio.py

import unittest
from unittest.mock import Mock, patch
from src.services.meu_conversor_audio import MeuConversorAudio

class TestMeuConversorAudio(unittest.TestCase):
    def setUp(self):
        self.config_provider = Mock()
        self.converter = MeuConversorAudio(config_provider=self.config_provider)
        
    def test_convert_to_audio_success(self):
        # Teste para o caso de sucesso
        # ...
        
    def test_convert_to_audio_failure(self):
        # Teste para o caso de falha
        # ...
```

## Adicionando um Novo Serviço de Geração de Texto

Para adicionar um novo serviço de geração de texto, siga estes passos:

1. Crie uma nova classe que implemente a interface `TextGenerationService`:

```python
from typing import Optional, Dict, Any
from src.interfaces.text_generation_service import TextGenerationService
from src.interfaces.config_provider import ConfigProvider
from src.utils.logging import get_logger

class MeuServicoGeracaoTexto(TextGenerationService):
    """
    Implementação do serviço de geração de texto usando Meu Serviço.
    """
    
    # Inicializa o logger para esta classe
    logger = get_logger(__name__)
    
    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """
        Inicializa o serviço de geração de texto.
        
        Args:
            config_provider: Provedor de configuração opcional
        """
        self.config_provider = config_provider
        # Inicialize aqui quaisquer recursos necessários
        
    def generate(self, system_prompt: str, user_prompt: str,
                options: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Gera texto com base em prompts do sistema e do usuário.
        
        Args:
            system_prompt: O prompt do sistema para o modelo
            user_prompt: O prompt do usuário para o modelo
            options: Opções adicionais para a geração de texto
            
        Returns:
            str: O texto gerado, ou None se falhou
        """
        try:
            # Implemente a lógica de geração de texto aqui
            # ...
            
            return "Texto gerado pelo modelo"
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar texto: {e}")
            return None
```

2. Atualize a fábrica para suportar o novo serviço:

```python
# Em src/factory.py

from src.services.meu_servico_geracao_texto import MeuServicoGeracaoTexto

# Na classe AutoMeetAIFactory, método create:
if text_generation_service_type.lower() == "meu_servico":
    self.container.register("text_generation_service", MeuServicoGeracaoTexto)
```

3. Adicione testes para o novo serviço:

```python
# Em tests/test_meu_servico_geracao_texto.py

import unittest
from unittest.mock import Mock, patch
from src.services.meu_servico_geracao_texto import MeuServicoGeracaoTexto

class TestMeuServicoGeracaoTexto(unittest.TestCase):
    def setUp(self):
        self.config_provider = Mock()
        self.service = MeuServicoGeracaoTexto(config_provider=self.config_provider)
        
    def test_generate_success(self):
        # Teste para o caso de sucesso
        # ...
        
    def test_generate_failure(self):
        # Teste para o caso de falha
        # ...
```

## Adicionando um Novo Formatador de Saída

Para adicionar um novo formatador de saída, siga estes passos:

1. Crie uma nova classe que implemente a interface `OutputFormatter`:

```python
from typing import Optional, Dict, Any
from src.interfaces.output_formatter import OutputFormatter
from src.models.transcription_result import TranscriptionResult
from src.utils.logging import get_logger

class MeuFormatador(OutputFormatter):
    """
    Formatador para saída em Meu Formato.
    """
    
    # Inicializa o logger para esta classe
    logger = get_logger(__name__)
    
    def format(self, transcription_result: TranscriptionResult,
              options: Optional[Dict[str, Any]] = None) -> str:
        """
        Formata um resultado de transcrição em Meu Formato.
        
        Args:
            transcription_result: O resultado da transcrição a ser formatado
            options: Opções de formatação específicas
            
        Returns:
            str: O resultado formatado
        """
        try:
            # Implemente a lógica de formatação aqui
            # ...
            
            return "Resultado formatado em Meu Formato"
            
        except Exception as e:
            self.logger.error(f"Erro ao formatar transcrição: {e}")
            raise
    
    def get_file_extension(self) -> str:
        """
        Obtém a extensão de arquivo padrão para este formatador.
        
        Returns:
            str: A extensão de arquivo padrão (sem o ponto)
        """
        return "meuformato"
```

2. Atualize a fábrica de formatadores para suportar o novo formatador:

```python
# Em src/formatters/formatter_factory.py

from src.formatters.meu_formatador import MeuFormatador

# Na classe FormatterFactory, método get_formatter:
if format_name.lower() == "meuformato":
    return MeuFormatador()
```

3. Adicione testes para o novo formatador:

```python
# Em tests/test_meu_formatador.py

import unittest
from src.formatters.meu_formatador import MeuFormatador
from src.models.transcription_result import TranscriptionResult, Utterance

class TestMeuFormatador(unittest.TestCase):
    def setUp(self):
        self.formatter = MeuFormatador()
        self.transcription = TranscriptionResult(
            utterances=[
                Utterance(speaker="Speaker 1", text="Olá, como vai?"),
                Utterance(speaker="Speaker 2", text="Estou bem, obrigado.")
            ],
            text="Olá, como vai? Estou bem, obrigado.",
            audio_file="test.mp3"
        )
        
    def test_format(self):
        # Teste para o método format
        # ...
        
    def test_get_file_extension(self):
        # Teste para o método get_file_extension
        # ...
```

## Criando um Plugin

O AutoMeetAI suporta plugins para estender sua funcionalidade. Para criar um plugin, siga estes passos:

1. Crie uma nova classe que implemente a interface `Plugin`:

```python
from typing import List, Any, Optional
from src.interfaces.plugin import Plugin
from src.interfaces.audio_converter import AudioConverter
from src.interfaces.config_provider import ConfigProvider
from src.utils.logging import get_logger

class MeuPlugin(Plugin):
    """
    Plugin que adiciona funcionalidades personalizadas ao AutoMeetAI.
    """
    
    # Inicializa o logger para esta classe
    logger = get_logger(__name__)
    
    def __init__(self):
        """
        Inicializa o plugin.
        """
        self.initialized = False
        
    def initialize(self, config: Optional[dict] = None) -> bool:
        """
        Inicializa o plugin com a configuração fornecida.
        
        Args:
            config: Configuração opcional para o plugin
            
        Returns:
            bool: True se a inicialização foi bem-sucedida, False caso contrário
        """
        try:
            # Implemente a lógica de inicialização aqui
            # ...
            
            self.initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar plugin: {e}")
            return False
    
    def get_name(self) -> str:
        """
        Obtém o nome do plugin.
        
        Returns:
            str: O nome do plugin
        """
        return "MeuPlugin"
    
    def get_version(self) -> str:
        """
        Obtém a versão do plugin.
        
        Returns:
            str: A versão do plugin
        """
        return "1.0.0"
    
    def get_description(self) -> str:
        """
        Obtém a descrição do plugin.
        
        Returns:
            str: A descrição do plugin
        """
        return "Plugin que adiciona funcionalidades personalizadas ao AutoMeetAI."
    
    def get_extension_points(self) -> List[str]:
        """
        Obtém os pontos de extensão suportados pelo plugin.
        
        Returns:
            List[str]: Lista de pontos de extensão suportados
        """
        return ["audio_converter", "transcription_service"]
    
    def get_implementation(self, extension_point: str) -> Any:
        """
        Obtém a implementação para um ponto de extensão.
        
        Args:
            extension_point: O ponto de extensão
            
        Returns:
            Any: A implementação para o ponto de extensão, ou None se não suportado
        """
        if not self.initialized:
            self.logger.warning("Plugin não inicializado.")
            return None
            
        if extension_point == "audio_converter":
            return MeuConversorAudio()
        elif extension_point == "transcription_service":
            return MeuServicoTranscricao()
        else:
            return None

# Implementações dos serviços fornecidos pelo plugin
class MeuConversorAudio(AudioConverter):
    # Implementação do conversor de áudio
    # ...

class MeuServicoTranscricao(TranscriptionService):
    # Implementação do serviço de transcrição
    # ...
```

2. Salve o arquivo do plugin no diretório `plugins`:

```
plugins/meu_plugin.py
```

3. O plugin será carregado automaticamente quando a aplicação for iniciada com suporte a plugins:

```python
from src.factory import AutoMeetAIFactory

# Criar uma instância do AutoMeetAI com suporte a plugins
factory = AutoMeetAIFactory()
factory.load_plugins()

# Verificar se o plugin foi carregado
plugin_info = factory.get_plugin_info()
print(plugin_info)

# Criar a aplicação com preferência pelo plugin
app = factory.create(
    use_plugins=True,
    plugin_preferences={
        "audio_converter": "MeuPlugin",
        "transcription_service": "MeuPlugin"
    }
)
```

## Estendendo o CLI

Para estender a interface de linha de comando (CLI), siga estes passos:

1. Abra o arquivo `main.py` e adicione novos argumentos:

```python
# Em main.py

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AutoMeetAI - Automated Meeting Transcription and Analysis")
    
    # Argumentos existentes
    # ...
    
    # Adicionar novos argumentos
    parser.add_argument("--meu-argumento", help="Descrição do meu argumento")
    parser.add_argument("--minha-opcao", choices=["opcao1", "opcao2"], default="opcao1",
                        help="Minha opção personalizada")
    
    args = parser.parse_args()
    
    # Usar os novos argumentos
    if args.meu_argumento:
        # Fazer algo com o argumento
        pass
        
    if args.minha_opcao == "opcao1":
        # Fazer algo com a opção 1
        pass
    elif args.minha_opcao == "opcao2":
        # Fazer algo com a opção 2
        pass
```

2. Se necessário, crie um novo script CLI para uma funcionalidade específica:

```python
#!/usr/bin/env python
"""
AutoMeetAI - Minha Funcionalidade Personalizada

Este script demonstra como usar o AutoMeetAI para minha funcionalidade personalizada.

Usage:
    python meu_script.py [options]

Examples:
    python meu_script.py --minha-opcao valor
"""

import argparse
import os
import sys

from src.factory import AutoMeetAIFactory
from src.utils.logging import get_logger, configure_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Configure the root logger
configure_logger()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AutoMeetAI - Minha Funcionalidade Personalizada")
    
    # Adicionar argumentos
    parser.add_argument("--minha-opcao", required=True, help="Minha opção personalizada")
    
    args = parser.parse_args()
    
    try:
        # Criar uma instância do AutoMeetAI
        factory = AutoMeetAIFactory()
        app = factory.create()
        
        # Implementar a funcionalidade personalizada
        # ...
        
        logger.info("Funcionalidade personalizada concluída com sucesso.")
        
    except Exception as e:
        logger.error(f"Ocorreu um erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Melhores Práticas

Ao estender o AutoMeetAI, siga estas melhores práticas:

1. **Documente seu código**: Adicione docstrings em português para todas as classes e métodos.

2. **Adicione testes**: Crie testes unitários para todas as novas funcionalidades.

3. **Siga os princípios SOLID**: Mantenha as classes coesas e com baixo acoplamento.

4. **Trate erros adequadamente**: Use blocos try/except e registre erros com o logger.

5. **Mantenha a compatibilidade**: Garanta que suas extensões sejam compatíveis com o restante do sistema.

6. **Use injeção de dependência**: Aceite dependências como parâmetros em vez de criá-las internamente.

7. **Respeite as interfaces**: Implemente todos os métodos abstratos das interfaces.

8. **Mantenha a consistência de estilo**: Siga o estilo de código existente.

9. **Documente as configurações**: Documente todas as opções de configuração que você adicionar.

10. **Atualize a documentação**: Atualize a documentação da API e os exemplos de uso quando adicionar novas funcionalidades.

Seguindo este guia, você poderá estender o AutoMeetAI de forma eficaz e manter a qualidade do código.

## Arquitetura de Microsservicos

Consulte o documento [Arquitetura de Microsserviços](microservices_architecture.md) para entender como o projeto foi dividido em serviços independentes.

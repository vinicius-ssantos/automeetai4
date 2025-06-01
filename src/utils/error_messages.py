"""
Utilitário para mensagens de erro amigáveis para o usuário.

Este módulo fornece funções para gerar mensagens de erro amigáveis para o usuário
com base nos tipos de exceção e contextos específicos.
"""

from typing import Optional, Dict, Any, Union, Type
import os
import re
from src.exceptions import (
    AutoMeetAIError, FileError, ServiceError, TranscriptionError, 
    FormattingError, ConfigError, APIKeyError
)


def get_user_friendly_message(
    error: Union[Exception, str],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Gera uma mensagem de erro amigável para o usuário.
    
    Args:
        error: A exceção ou mensagem de erro
        context: Contexto adicional para personalizar a mensagem
        
    Returns:
        str: Mensagem de erro amigável para o usuário
    """
    # Inicializa o contexto se não fornecido
    if context is None:
        context = {}
        
    # Se for uma string, cria uma mensagem diretamente
    if isinstance(error, str):
        return _format_error_message(error, context)
        
    # Obtém o tipo de exceção
    error_type = type(error)
    error_message = str(error)
    
    # Trata diferentes tipos de exceção
    if isinstance(error, FileError):
        return _get_file_error_message(error, error_message, context)
    elif isinstance(error, ServiceError):
        return _get_service_error_message(error, error_message, context)
    elif isinstance(error, TranscriptionError):
        return _get_transcription_error_message(error, error_message, context)
    elif isinstance(error, FormattingError):
        return _get_formatting_error_message(error, error_message, context)
    elif isinstance(error, ConfigError):
        return _get_config_error_message(error, error_message, context)
    elif isinstance(error, AutoMeetAIError):
        return _get_generic_automeetai_error_message(error, error_message, context)
    else:
        return _get_generic_error_message(error, error_message, context)


def _format_error_message(message: str, context: Dict[str, Any]) -> str:
    """
    Formata uma mensagem de erro com o contexto fornecido.
    
    Args:
        message: A mensagem de erro
        context: Contexto para formatação
        
    Returns:
        str: Mensagem formatada
    """
    try:
        return message.format(**context)
    except KeyError:
        # Se faltar alguma chave no contexto, retorna a mensagem original
        return message
    except Exception:
        # Para qualquer outro erro de formatação, retorna a mensagem original
        return message


def _get_file_error_message(error: FileError, error_message: str, context: Dict[str, Any]) -> str:
    """
    Gera uma mensagem amigável para erros de arquivo.
    
    Args:
        error: A exceção
        error_message: A mensagem de erro original
        context: Contexto adicional
        
    Returns:
        str: Mensagem de erro amigável
    """
    # Extrai o nome do arquivo do contexto ou da mensagem de erro
    file_path = context.get('file_path', None)
    if not file_path:
        # Tenta extrair o caminho do arquivo da mensagem de erro
        file_match = re.search(r'[\'"]([^\'"]*)[\'"]\s*:', error_message)
        if file_match:
            file_path = file_match.group(1)
            
    # Se tiver o caminho do arquivo, usa apenas o nome do arquivo para a mensagem
    file_name = os.path.basename(file_path) if file_path else "arquivo"
    
    # Mensagens específicas para diferentes cenários de erro de arquivo
    if "Invalid video file" in error_message:
        return f"O arquivo '{file_name}' não é um formato de vídeo válido. Por favor, use um dos formatos suportados (como MP4, AVI, MOV)."
    elif "Failed to generate output filename" in error_message:
        return f"Não foi possível gerar um nome de arquivo para a saída. Verifique se o diretório de saída existe e se você tem permissão para escrever nele."
    elif "Failed to save" in error_message:
        return f"Não foi possível salvar o arquivo '{file_name}'. Verifique se você tem permissão para escrever no diretório de saída e se há espaço em disco suficiente."
    elif "not found" in error_message.lower():
        return f"O arquivo '{file_name}' não foi encontrado. Verifique se o caminho está correto e se o arquivo existe."
    elif "permission" in error_message.lower():
        return f"Sem permissão para acessar o arquivo '{file_name}'. Verifique as permissões do arquivo ou execute o programa com privilégios adequados."
    else:
        return f"Ocorreu um problema com o arquivo '{file_name}': {error_message}"


def _get_service_error_message(error: ServiceError, error_message: str, context: Dict[str, Any]) -> str:
    """
    Gera uma mensagem amigável para erros de serviço.
    
    Args:
        error: A exceção
        error_message: A mensagem de erro original
        context: Contexto adicional
        
    Returns:
        str: Mensagem de erro amigável
    """
    service_name = context.get('service_name', 'serviço externo')
    
    # Mensagens específicas para diferentes cenários de erro de serviço
    if "Audio conversion failed" in error_message:
        return f"A conversão de áudio falhou. Verifique se o arquivo de vídeo não está corrompido e se o ffmpeg está instalado corretamente."
    elif "Error during audio conversion" in error_message:
        return f"Ocorreu um erro durante a conversão de áudio. Verifique se o arquivo de vídeo é válido e se você tem espaço em disco suficiente."
    elif "Text generation service returned empty result" in error_message:
        return f"O serviço de geração de texto não retornou nenhum resultado. Verifique sua chave de API e conexão com a internet."
    elif "Failed to format user prompt" in error_message:
        return f"Não foi possível formatar o prompt do usuário. Verifique se o template do prompt é válido."
    elif "Error during text generation" in error_message:
        return f"Ocorreu um erro durante a geração de texto. Verifique sua chave de API, conexão com a internet e se o serviço está disponível."
    elif "API key" in error_message.lower():
        return f"Chave de API inválida ou ausente para o serviço {service_name}. Verifique se você configurou corretamente a chave de API nas variáveis de ambiente."
    elif "rate limit" in error_message.lower():
        return f"Limite de taxa excedido para o serviço {service_name}. Por favor, aguarde um momento e tente novamente mais tarde."
    elif "network" in error_message.lower() or "connection" in error_message.lower():
        return f"Erro de conexão ao acessar o serviço {service_name}. Verifique sua conexão com a internet e tente novamente."
    else:
        return f"Ocorreu um problema ao acessar o serviço {service_name}: {error_message}"


def _get_transcription_error_message(error: TranscriptionError, error_message: str, context: Dict[str, Any]) -> str:
    """
    Gera uma mensagem amigável para erros de transcrição.
    
    Args:
        error: A exceção
        error_message: A mensagem de erro original
        context: Contexto adicional
        
    Returns:
        str: Mensagem de erro amigável
    """
    # Mensagens específicas para diferentes cenários de erro de transcrição
    if "Transcription service returned empty result" in error_message:
        return "O serviço de transcrição não retornou nenhum resultado. O áudio pode estar vazio ou ter qualidade muito baixa."
    elif "Error during transcription" in error_message:
        return "Ocorreu um erro durante a transcrição. Verifique se o arquivo de áudio é válido e se sua chave de API está correta."
    elif "Failed to convert transcription result" in error_message:
        return "Não foi possível processar o resultado da transcrição. O formato da resposta do serviço pode ter mudado."
    else:
        return f"Ocorreu um problema durante a transcrição: {error_message}"


def _get_formatting_error_message(error: FormattingError, error_message: str, context: Dict[str, Any]) -> str:
    """
    Gera uma mensagem amigável para erros de formatação.
    
    Args:
        error: A exceção
        error_message: A mensagem de erro original
        context: Contexto adicional
        
    Returns:
        str: Mensagem de erro amigável
    """
    format_name = context.get('format_name', 'formato solicitado')
    
    # Mensagens específicas para diferentes cenários de erro de formatação
    if "Unsupported format" in error_message:
        return f"O formato '{format_name}' não é suportado. Formatos suportados incluem: txt, json, html."
    elif "Failed to save" in error_message:
        return f"Não foi possível salvar no formato '{format_name}'. Verifique as permissões do diretório de saída."
    else:
        return f"Ocorreu um problema ao formatar a saída para '{format_name}': {error_message}"


def _get_config_error_message(error: ConfigError, error_message: str, context: Dict[str, Any]) -> str:
    """
    Gera uma mensagem amigável para erros de configuração.
    
    Args:
        error: A exceção
        error_message: A mensagem de erro original
        context: Contexto adicional
        
    Returns:
        str: Mensagem de erro amigável
    """
    # Mensagens específicas para diferentes cenários de erro de configuração
    if isinstance(error, APIKeyError):
        service = "API" if "API" in error_message else "serviço"
        if "AssemblyAI" in error_message:
            return "Chave de API da AssemblyAI não configurada. Configure a variável de ambiente AUTOMEETAI_ASSEMBLYAI_API_KEY."
        elif "OpenAI" in error_message:
            return "Chave de API da OpenAI não configurada. Configure a variável de ambiente AUTOMEETAI_OPENAI_API_KEY."
        else:
            return f"Chave de API não configurada para o {service}. Verifique a documentação para instruções de configuração."
    elif "Invalid configuration value" in error_message:
        return f"Valor de configuração inválido: {error_message}. Verifique a documentação para os valores permitidos."
    else:
        return f"Erro de configuração: {error_message}. Verifique as configurações do aplicativo."


def _get_generic_automeetai_error_message(error: AutoMeetAIError, error_message: str, context: Dict[str, Any]) -> str:
    """
    Gera uma mensagem amigável para erros genéricos do AutoMeetAI.
    
    Args:
        error: A exceção
        error_message: A mensagem de erro original
        context: Contexto adicional
        
    Returns:
        str: Mensagem de erro amigável
    """
    return f"Ocorreu um erro no AutoMeetAI: {error_message}. Se o problema persistir, consulte a documentação ou entre em contato com o suporte."


def _get_generic_error_message(error: Exception, error_message: str, context: Dict[str, Any]) -> str:
    """
    Gera uma mensagem amigável para erros genéricos.
    
    Args:
        error: A exceção
        error_message: A mensagem de erro original
        context: Contexto adicional
        
    Returns:
        str: Mensagem de erro amigável
    """
    return f"Ocorreu um erro inesperado: {error_message}. Se o problema persistir, consulte a documentação ou entre em contato com o suporte."
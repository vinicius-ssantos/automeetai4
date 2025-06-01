import logging
import os
import sys
from typing import Optional

# Configuração padrão do logger
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Singleton para garantir que o logger seja configurado apenas uma vez
_logger_configured = False

def configure_logger(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_LOG_DATE_FORMAT,
    log_file: Optional[str] = None
) -> None:
    """
    Configura o logger global.
    
    Args:
        log_level: Nível de log (default: logging.INFO)
        log_format: Formato do log (default: "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        date_format: Formato da data (default: "%Y-%m-%d %H:%M:%S")
        log_file: Caminho para o arquivo de log (opcional)
    """
    global _logger_configured
    
    if _logger_configured:
        return
        
    # Configurar o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Criar um handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)
    
    # Adicionar um handler para arquivo se especificado
    if log_file:
        # Garantir que o diretório do arquivo de log exista
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        root_logger.addHandler(file_handler)
    
    _logger_configured = True
    
def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger configurado para o módulo especificado.
    
    Args:
        name: Nome do módulo (geralmente __name__)
        
    Returns:
        logging.Logger: O logger configurado
    """
    # Garantir que o logger esteja configurado
    if not _logger_configured:
        configure_logger()
        
    return logging.getLogger(name)
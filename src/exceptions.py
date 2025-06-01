"""
Exceções personalizadas para o AutoMeetAI.

Este módulo define uma hierarquia de exceções personalizadas para o AutoMeetAI,
seguindo as melhores práticas de tratamento de erros em Python.
"""

class AutoMeetAIError(Exception):
    """
    Exceção base para todas as exceções do AutoMeetAI.

    Todas as exceções personalizadas do AutoMeetAI herdam desta classe,
    permitindo que o código cliente capture todas as exceções do AutoMeetAI
    com um único bloco except.

    Attributes:
        user_friendly_message: Mensagem de erro amigável para o usuário final
    """
    def __init__(self, message, user_friendly_message=None):
        """
        Inicializa a exceção com uma mensagem e opcionalmente uma mensagem amigável.

        Args:
            message: Mensagem técnica de erro
            user_friendly_message: Mensagem amigável para o usuário final
        """
        super().__init__(message)
        self.user_friendly_message = user_friendly_message

    def get_user_message(self):
        """
        Retorna a mensagem amigável para o usuário, ou a mensagem técnica se não houver.

        Returns:
            str: Mensagem amigável para o usuário
        """
        return self.user_friendly_message if self.user_friendly_message else str(self)


class ConfigError(AutoMeetAIError):
    """
    Exceção lançada quando há um problema com a configuração.
    """
    pass


class APIKeyError(ConfigError):
    """
    Exceção lançada quando uma chave de API está ausente ou é inválida.
    """
    pass


class ConfigValueError(ConfigError):
    """
    Exceção lançada quando um valor de configuração é inválido.
    """
    pass


class FileError(AutoMeetAIError):
    """
    Exceção base para erros relacionados a arquivos.
    """
    pass


class FileNotFoundError(FileError):
    """
    Exceção lançada quando um arquivo não é encontrado.
    """
    pass


class InvalidFileFormatError(FileError):
    """
    Exceção lançada quando um arquivo tem um formato inválido.
    """
    pass


class FilePermissionError(FileError):
    """
    Exceção lançada quando há um problema de permissão ao acessar um arquivo.
    """
    pass


class ServiceError(AutoMeetAIError):
    """
    Exceção base para erros relacionados a serviços externos.
    """
    pass


class APIError(ServiceError):
    """
    Exceção lançada quando há um erro na comunicação com uma API externa.
    """
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NetworkError(ServiceError):
    """
    Exceção lançada quando há um problema de rede.
    """
    pass


class RateLimitError(ServiceError):
    """
    Exceção lançada quando um limite de taxa é atingido.
    """
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class TranscriptionError(AutoMeetAIError):
    """
    Exceção base para erros relacionados à transcrição.
    """
    pass


class TranscriptionFailedError(TranscriptionError):
    """
    Exceção lançada quando a transcrição falha.
    """
    pass


class InvalidTranscriptionFormatError(TranscriptionError):
    """
    Exceção lançada quando o formato da transcrição é inválido.
    """
    pass


class FormattingError(AutoMeetAIError):
    """
    Exceção base para erros relacionados à formatação.
    """
    pass


class UnsupportedFormatError(FormattingError):
    """
    Exceção lançada quando um formato solicitado não é suportado.
    """
    pass


class FormattingFailedError(FormattingError):
    """
    Exceção lançada quando a formatação falha.
    """
    pass

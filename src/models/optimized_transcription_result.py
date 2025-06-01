from typing import List, Optional, Dict, Any, Iterator, Union, Callable
from dataclasses import dataclass
import os
import json
import tempfile
from src.utils.logging import get_logger
from src.exceptions import UnsupportedFormatError, FormattingFailedError, FileError
from src.models.transcription_result import Utterance, TranscriptionResult

# Initialize logger for this module
logger = get_logger(__name__)


class UtteranceIterator:
    """
    Iterador otimizado para percorrer grandes quantidades de utterances.
    Carrega os utterances em chunks para reduzir o uso de memória.
    """
    
    def __init__(self, utterances_file: str, chunk_size: int = 100):
        """
        Inicializa o iterador de utterances.
        
        Args:
            utterances_file: Caminho para o arquivo contendo os utterances
            chunk_size: Número de utterances a serem carregados por vez
        """
        self.utterances_file = utterances_file
        self.chunk_size = chunk_size
        self.current_index = 0
        self.total_count = 0
        
        # Conta o número total de utterances no arquivo
        with open(self.utterances_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():  # Ignora linhas vazias
                    self.total_count += 1
    
    def __iter__(self):
        """
        Retorna o próprio iterador.
        """
        self.current_index = 0
        return self
    
    def __next__(self) -> Utterance:
        """
        Retorna o próximo utterance.
        
        Returns:
            Utterance: O próximo utterance
            
        Raises:
            StopIteration: Quando não há mais utterances
        """
        if self.current_index >= self.total_count:
            raise StopIteration
            
        # Abre o arquivo e avança até o índice atual
        with open(self.utterances_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == self.current_index:
                    self.current_index += 1
                    if not line.strip():  # Ignora linhas vazias
                        continue
                    
                    # Converte a linha JSON em um objeto Utterance
                    utterance_data = json.loads(line)
                    return Utterance(
                        speaker=utterance_data.get('speaker', ''),
                        text=utterance_data.get('text', ''),
                        start=utterance_data.get('start'),
                        end=utterance_data.get('end')
                    )
        
        # Não deveria chegar aqui, mas por segurança
        raise StopIteration
    
    def __len__(self) -> int:
        """
        Retorna o número total de utterances.
        
        Returns:
            int: O número total de utterances
        """
        return self.total_count
    
    def get_chunk(self, start_index: int, chunk_size: Optional[int] = None) -> List[Utterance]:
        """
        Retorna um chunk de utterances.
        
        Args:
            start_index: Índice inicial do chunk
            chunk_size: Tamanho do chunk (se None, usa o tamanho padrão)
            
        Returns:
            List[Utterance]: Lista de utterances no chunk
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
            
        result = []
        count = 0
        
        with open(self.utterances_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if not line.strip():  # Ignora linhas vazias
                    continue
                    
                if i >= start_index and count < chunk_size:
                    # Converte a linha JSON em um objeto Utterance
                    utterance_data = json.loads(line)
                    utterance = Utterance(
                        speaker=utterance_data.get('speaker', ''),
                        text=utterance_data.get('text', ''),
                        start=utterance_data.get('start'),
                        end=utterance_data.get('end')
                    )
                    result.append(utterance)
                    count += 1
                    
                if count >= chunk_size:
                    break
                    
        return result


class OptimizedTranscriptionResult:
    """
    Versão otimizada do TranscriptionResult para grandes transcrições.
    Usa carregamento preguiçoso e paginação para reduzir o uso de memória.
    """
    
    def __init__(self, utterances: Union[List[Utterance], str], text: str, audio_file: str):
        """
        Inicializa o resultado da transcrição otimizado.
        
        Args:
            utterances: Lista de utterances ou caminho para o arquivo de utterances
            text: Texto completo da transcrição
            audio_file: Caminho para o arquivo de áudio
        """
        self.text = text
        self.audio_file = audio_file
        self._utterances_loaded = False
        self._utterances_file = None
        self._utterances_iterator = None
        
        # Se utterances for uma string, assume que é um caminho para o arquivo
        if isinstance(utterances, str):
            self._utterances_file = utterances
        else:
            # Se utterances for uma lista, salva em um arquivo temporário
            self._utterances_file = self._save_utterances_to_file(utterances)
            
        # Cria o iterador de utterances
        self._utterances_iterator = UtteranceIterator(self._utterances_file)
    
    def _save_utterances_to_file(self, utterances: List[Utterance]) -> str:
        """
        Salva os utterances em um arquivo temporário.
        
        Args:
            utterances: Lista de utterances
            
        Returns:
            str: Caminho para o arquivo temporário
        """
        # Cria um arquivo temporário
        fd, temp_file = tempfile.mkstemp(suffix='.jsonl', prefix='utterances_')
        os.close(fd)
        
        # Salva os utterances no arquivo
        with open(temp_file, 'w', encoding='utf-8') as f:
            for utterance in utterances:
                utterance_data = {
                    'speaker': utterance.speaker,
                    'text': utterance.text,
                    'start': utterance.start,
                    'end': utterance.end
                }
                f.write(json.dumps(utterance_data) + '\n')
                
        return temp_file
    
    def __del__(self):
        """
        Limpa os recursos quando o objeto é destruído.
        """
        # Remove o arquivo temporário se foi criado
        if self._utterances_file and self._utterances_file.startswith(tempfile.gettempdir()):
            try:
                os.remove(self._utterances_file)
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário {self._utterances_file}: {e}")
    
    @property
    def utterances(self) -> Iterator[Utterance]:
        """
        Retorna um iterador para os utterances.
        
        Returns:
            Iterator[Utterance]: Iterador para os utterances
        """
        return iter(self._utterances_iterator)
    
    def get_utterances_chunk(self, start_index: int, chunk_size: int) -> List[Utterance]:
        """
        Retorna um chunk de utterances.
        
        Args:
            start_index: Índice inicial do chunk
            chunk_size: Tamanho do chunk
            
        Returns:
            List[Utterance]: Lista de utterances no chunk
        """
        return self._utterances_iterator.get_chunk(start_index, chunk_size)
    
    def get_utterance_count(self) -> int:
        """
        Retorna o número total de utterances.
        
        Returns:
            int: O número total de utterances
        """
        return len(self._utterances_iterator)
    
    def to_formatted_text(self) -> str:
        """
        Converte o resultado da transcrição para um texto formatado.
        
        Returns:
            str: O texto formatado da transcrição
        """
        result = []
        for utterance in self.utterances:
            result.append(f"{utterance.speaker}: {utterance.text}")
            
        return "\n".join(result)
    
    def format(self, format_name: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Formata o resultado da transcrição no formato especificado.
        
        Args:
            format_name: Nome do formato (text, json, html, etc.)
            options: Opções de formatação específicas para o formatador
            
        Returns:
            str: O resultado formatado
            
        Raises:
            UnsupportedFormatError: Se o formato não for suportado
            FormattingFailedError: Se ocorrer um erro durante a formatação
        """
        # Importar aqui para evitar importação circular
        from src.formatters.formatter_factory import FormatterFactory
        
        try:
            # Converte para TranscriptionResult padrão para compatibilidade com formatadores existentes
            # Isso é ineficiente para grandes transcrições, mas é necessário para compatibilidade
            # Futuramente, os formatadores devem ser atualizados para suportar OptimizedTranscriptionResult
            standard_result = self.to_standard_result()
            
            # O método get_formatter agora lança UnsupportedFormatError se o formato não for suportado
            formatter = FormatterFactory.get_formatter(format_name)
            return formatter.format(standard_result, options)
        except UnsupportedFormatError:
            # Repassar a exceção UnsupportedFormatError
            logger.error(f"Formato não suportado: {format_name}")
            raise
        except Exception as e:
            # Converter outras exceções em FormattingFailedError
            logger.error(f"Erro ao formatar transcrição como {format_name}: {e}")
            raise FormattingFailedError(f"Erro ao formatar transcrição como {format_name}: {e}") from e
    
    def save_to_file(self, output_file: str, format_name: Optional[str] = None, 
                   options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Salva o resultado da transcrição em um arquivo.
        
        Args:
            output_file: Caminho onde a transcrição deve ser salva
            format_name: Nome do formato (text, json, html, etc.). Se None, será inferido da extensão do arquivo
            options: Opções de formatação específicas para o formatador
            
        Returns:
            bool: True se o arquivo foi salvo com sucesso, False caso contrário
            
        Raises:
            UnsupportedFormatError: Se o formato não for suportado
            FormattingFailedError: Se ocorrer um erro durante a formatação
            FileError: Se ocorrer um erro ao salvar o arquivo
        """
        try:
            # Se o formato não foi especificado, inferir da extensão do arquivo
            if not format_name:
                _, ext = os.path.splitext(output_file)
                if ext:
                    format_name = ext[1:]  # Remover o ponto
                else:
                    format_name = "txt"  # Formato padrão
                    
            # Formatar o conteúdo - pode lançar UnsupportedFormatError ou FormattingFailedError
            content = self.format(format_name, options)
            
            # Salvar no arquivo
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except PermissionError as e:
                raise FileError(f"Erro de permissão ao salvar arquivo {output_file}: {e}") from e
            except OSError as e:
                raise FileError(f"Erro ao salvar arquivo {output_file}: {e}") from e
                
            logger.info(f"Transcrição salva em {output_file}")
            return True
            
        except (UnsupportedFormatError, FormattingFailedError, FileError):
            # Repassar exceções personalizadas
            raise
        except Exception as e:
            # Converter outras exceções em FileError
            logger.error(f"Erro inesperado ao salvar transcrição no arquivo: {e}")
            raise FileError(f"Erro inesperado ao salvar transcrição no arquivo: {e}") from e
    
    def save_as_multiple_formats(self, base_output_file: str, formats: List[str], 
                              options: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, bool]:
        """
        Salva o resultado da transcrição em múltiplos formatos.
        
        Args:
            base_output_file: Caminho base para os arquivos de saída (sem extensão)
            formats: Lista de formatos para salvar
            options: Dicionário mapeando formatos para suas opções específicas
            
        Returns:
            Dict[str, bool]: Dicionário mapeando formatos para status de sucesso
        """
        results = {}
        
        for format_name in formats:
            try:
                # Importar aqui para evitar importação circular
                from src.formatters.formatter_factory import FormatterFactory
                
                # Obter o formatador - pode lançar UnsupportedFormatError
                formatter = FormatterFactory.get_formatter(format_name)
                
                # Obter a extensão do arquivo para este formato
                extension = formatter.get_file_extension()
                output_file = f"{base_output_file}.{extension}"
                
                # Obter opções específicas para este formato, se fornecidas
                format_options = None
                if options and format_name in options:
                    format_options = options[format_name]
                    
                # Salvar no formato - pode lançar várias exceções
                try:
                    self.save_to_file(output_file, format_name, format_options)
                    results[format_name] = True
                except Exception as e:
                    logger.error(f"Erro ao salvar no formato {format_name}: {e}")
                    results[format_name] = False
                    
            except Exception as e:
                logger.error(f"Erro ao processar formato {format_name}: {e}")
                results[format_name] = False
                
        return results
    
    def to_standard_result(self) -> TranscriptionResult:
        """
        Converte para o modelo TranscriptionResult padrão.
        
        Returns:
            TranscriptionResult: O resultado da transcrição no formato padrão
        """
        # Carrega todos os utterances em memória
        utterances = list(self.utterances)
        
        # Cria um TranscriptionResult padrão
        return TranscriptionResult(
            utterances=utterances,
            text=self.text,
            audio_file=self.audio_file
        )
    
    @classmethod
    def from_standard_result(cls, result: TranscriptionResult) -> 'OptimizedTranscriptionResult':
        """
        Cria um OptimizedTranscriptionResult a partir de um TranscriptionResult padrão.
        
        Args:
            result: O TranscriptionResult padrão
            
        Returns:
            OptimizedTranscriptionResult: O resultado da transcrição otimizado
        """
        return cls(
            utterances=result.utterances,
            text=result.text,
            audio_file=result.audio_file
        )
from typing import Optional, List, Iterator, Callable, Dict, Any, Union
import os
from src.models.transcription_result import TranscriptionResult
from src.models.optimized_transcription_result import OptimizedTranscriptionResult
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class LazyTextProcessor:
    """
    Processador de texto preguiçoso para operações intensivas em recursos.
    
    Esta classe implementa o padrão de carregamento preguiçoso (lazy loading) para
    processamento de grandes volumes de texto, como transcrições longas. Em vez de
    carregar todo o texto na memória de uma vez, ele processa o texto em chunks,
    reduzindo o uso de memória e melhorando o desempenho para arquivos grandes.
    """
    
    def __init__(self, chunk_size: int = 1000):
        """
        Inicializa o processador de texto preguiçoso.
        
        Args:
            chunk_size: Tamanho do chunk para processamento de texto
        """
        self.chunk_size = chunk_size
        
    def process_transcription_in_chunks(
        self, 
        transcription: Union[TranscriptionResult, OptimizedTranscriptionResult],
        processor_func: Callable[[str], str],
        max_chunks: Optional[int] = None
    ) -> str:
        """
        Processa uma transcrição em chunks, aplicando a função de processamento a cada chunk.
        
        Args:
            transcription: O resultado da transcrição a ser processado
            processor_func: Função que processa cada chunk de texto
            max_chunks: Número máximo de chunks a processar (None para processar todos)
            
        Returns:
            str: O resultado combinado do processamento
        """
        logger.info(f"Processando transcrição em chunks de tamanho {self.chunk_size}")
        
        # Verifica se é uma transcrição otimizada
        is_optimized = isinstance(transcription, OptimizedTranscriptionResult)
        
        if is_optimized:
            return self._process_optimized_transcription(transcription, processor_func, max_chunks)
        else:
            return self._process_standard_transcription(transcription, processor_func, max_chunks)
    
    def _process_standard_transcription(
        self,
        transcription: TranscriptionResult,
        processor_func: Callable[[str], str],
        max_chunks: Optional[int] = None
    ) -> str:
        """
        Processa uma transcrição padrão em chunks.
        
        Args:
            transcription: O resultado da transcrição padrão
            processor_func: Função que processa cada chunk de texto
            max_chunks: Número máximo de chunks a processar
            
        Returns:
            str: O resultado combinado do processamento
        """
        # Converte a transcrição para texto formatado
        formatted_text = transcription.to_formatted_text()
        
        # Divide o texto em chunks
        text_chunks = self._split_text_into_chunks(formatted_text)
        
        # Limita o número de chunks se necessário
        if max_chunks is not None and max_chunks > 0:
            text_chunks = text_chunks[:max_chunks]
            
        # Processa cada chunk
        processed_chunks = []
        for i, chunk in enumerate(text_chunks):
            logger.info(f"Processando chunk {i+1}/{len(text_chunks)}")
            processed_chunk = processor_func(chunk)
            processed_chunks.append(processed_chunk)
            
        # Combina os resultados
        return "\n".join(processed_chunks)
    
    def _process_optimized_transcription(
        self,
        transcription: OptimizedTranscriptionResult,
        processor_func: Callable[[str], str],
        max_chunks: Optional[int] = None
    ) -> str:
        """
        Processa uma transcrição otimizada em chunks.
        
        Args:
            transcription: O resultado da transcrição otimizada
            processor_func: Função que processa cada chunk de texto
            max_chunks: Número máximo de chunks a processar
            
        Returns:
            str: O resultado combinado do processamento
        """
        # Obtém o número total de utterances
        total_utterances = transcription.get_utterance_count()
        
        # Calcula o número de chunks
        chunk_size = min(self.chunk_size, 100)  # Limita o tamanho do chunk para evitar problemas de memória
        num_chunks = (total_utterances + chunk_size - 1) // chunk_size
        
        # Limita o número de chunks se necessário
        if max_chunks is not None and max_chunks > 0:
            num_chunks = min(num_chunks, max_chunks)
            
        # Processa cada chunk
        processed_chunks = []
        for i in range(num_chunks):
            logger.info(f"Processando chunk {i+1}/{num_chunks}")
            
            # Obtém o chunk de utterances
            start_index = i * chunk_size
            utterances = transcription.get_utterances_chunk(start_index, chunk_size)
            
            # Formata o chunk de utterances
            chunk_text = "\n".join([f"{u.speaker}: {u.text}" for u in utterances])
            
            # Processa o chunk
            processed_chunk = processor_func(chunk_text)
            processed_chunks.append(processed_chunk)
            
        # Combina os resultados
        return "\n".join(processed_chunks)
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Divide um texto em chunks de tamanho aproximadamente igual.
        
        Args:
            text: O texto a ser dividido
            
        Returns:
            List[str]: Lista de chunks de texto
        """
        # Divide o texto em linhas
        lines = text.split("\n")
        
        # Inicializa variáveis
        chunks = []
        current_chunk = []
        current_size = 0
        
        # Processa cada linha
        for line in lines:
            line_size = len(line)
            
            # Se adicionar esta linha exceder o tamanho do chunk, inicia um novo chunk
            if current_size + line_size > self.chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0
                
            # Adiciona a linha ao chunk atual
            current_chunk.append(line)
            current_size += line_size
            
        # Adiciona o último chunk se não estiver vazio
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        return chunks
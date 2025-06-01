import os
import json
import hashlib
from typing import Optional, Dict, Any
from dataclasses import asdict
import pickle

from src.models.transcription_result import TranscriptionResult, Utterance
from src.utils.logging import get_logger
from src.utils.file_utils import ensure_directory_exists

# Initialize logger for this module
logger = get_logger(__name__)


class TranscriptionCache:
    """
    Classe para gerenciar o cache de resultados de transcrição.
    Implementa um mecanismo de cache para evitar o reprocessamento de vídeos
    que já foram transcritos anteriormente.
    """

    def __init__(self, cache_dir: str = "cache"):
        """
        Inicializa o cache de transcrição.

        Args:
            cache_dir: Diretório onde os arquivos de cache serão armazenados
        """
        self.cache_dir = cache_dir
        ensure_directory_exists(cache_dir)
        logger.info(f"Transcription cache initialized at {cache_dir}")

    def _generate_cache_key(self, video_file: str) -> str:
        """
        Gera uma chave de cache única para um arquivo de vídeo.
        A chave é baseada no caminho absoluto do arquivo e em seu tamanho e data de modificação.

        Args:
            video_file: Caminho para o arquivo de vídeo

        Returns:
            str: Chave de cache única para o arquivo
        """
        # Get absolute path to ensure uniqueness
        abs_path = os.path.abspath(video_file)
        
        # Get file stats for additional uniqueness
        try:
            stats = os.stat(abs_path)
            file_size = stats.st_size
            file_mtime = stats.st_mtime
        except OSError:
            logger.warning(f"Could not get stats for {abs_path}, using path only for cache key")
            file_size = 0
            file_mtime = 0
        
        # Create a unique key based on path and file stats
        key_data = f"{abs_path}:{file_size}:{file_mtime}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cache_file_path(self, cache_key: str) -> str:
        """
        Obtém o caminho para o arquivo de cache com base na chave de cache.

        Args:
            cache_key: Chave de cache

        Returns:
            str: Caminho para o arquivo de cache
        """
        return os.path.join(self.cache_dir, f"{cache_key}.pickle")

    def get(self, video_file: str) -> Optional[TranscriptionResult]:
        """
        Obtém um resultado de transcrição do cache, se disponível.

        Args:
            video_file: Caminho para o arquivo de vídeo

        Returns:
            Optional[TranscriptionResult]: O resultado da transcrição, ou None se não estiver no cache
        """
        cache_key = self._generate_cache_key(video_file)
        cache_file = self._get_cache_file_path(cache_key)
        
        if not os.path.exists(cache_file):
            logger.debug(f"Cache miss for {video_file}")
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
            # Reconstruct TranscriptionResult from cached data
            utterances = [
                Utterance(
                    speaker=u['speaker'],
                    text=u['text'],
                    start=u.get('start'),
                    end=u.get('end')
                ) for u in cached_data['utterances']
            ]
            
            result = TranscriptionResult(
                utterances=utterances,
                text=cached_data['text'],
                audio_file=cached_data['audio_file']
            )
            
            logger.info(f"Cache hit for {video_file}")
            return result
            
        except Exception as e:
            logger.error(f"Error loading cache for {video_file}: {e}")
            # If there's an error loading the cache, remove the corrupt cache file
            try:
                os.remove(cache_file)
            except OSError:
                pass
            return None

    def set(self, video_file: str, result: TranscriptionResult) -> bool:
        """
        Armazena um resultado de transcrição no cache.

        Args:
            video_file: Caminho para o arquivo de vídeo
            result: Resultado da transcrição a ser armazenado

        Returns:
            bool: True se o cache foi atualizado com sucesso, False caso contrário
        """
        cache_key = self._generate_cache_key(video_file)
        cache_file = self._get_cache_file_path(cache_key)
        
        try:
            # Convert TranscriptionResult to a serializable format
            serializable_data = {
                'utterances': [asdict(u) for u in result.utterances],
                'text': result.text,
                'audio_file': result.audio_file
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(serializable_data, f)
                
            logger.info(f"Cached transcription for {video_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching transcription for {video_file}: {e}")
            return False

    def invalidate(self, video_file: str) -> bool:
        """
        Invalida o cache para um arquivo de vídeo específico.

        Args:
            video_file: Caminho para o arquivo de vídeo

        Returns:
            bool: True se o cache foi invalidado com sucesso, False caso contrário
        """
        cache_key = self._generate_cache_key(video_file)
        cache_file = self._get_cache_file_path(cache_key)
        
        if not os.path.exists(cache_file):
            return True
        
        try:
            os.remove(cache_file)
            logger.info(f"Invalidated cache for {video_file}")
            return True
        except OSError as e:
            logger.error(f"Error invalidating cache for {video_file}: {e}")
            return False

    def clear(self) -> bool:
        """
        Limpa todo o cache de transcrição.

        Returns:
            bool: True se o cache foi limpo com sucesso, False caso contrário
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pickle'):
                    os.remove(os.path.join(self.cache_dir, filename))
            logger.info("Cleared transcription cache")
            return True
        except Exception as e:
            logger.error(f"Error clearing transcription cache: {e}")
            return False
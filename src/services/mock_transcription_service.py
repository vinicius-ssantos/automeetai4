from typing import Optional, Dict, Any, List, Union
import os
import random
import time
from src.interfaces.transcription_service import TranscriptionService
from src.interfaces.config_provider import ConfigProvider
from src.utils.file_utils import validate_file_path
from src.utils.logging import get_logger
from src.models.transcription_result import TranscriptionResult, Speaker, Utterance

class MockTranscriptionService(TranscriptionService):
    """
    Implementação de demonstração do serviço de transcrição que não requer API externa.
    
    Este serviço gera transcrições fictícias para fins de demonstração e teste.
    Seguindo o Princípio da Responsabilidade Única, esta classe é responsável apenas
    por gerar transcrições simuladas de arquivos de áudio.
    """
    
    # Inicializa o logger para esta classe
    logger = get_logger(__name__)
    
    # Frases de exemplo para gerar transcrições fictícias
    SAMPLE_PHRASES = [
        "Olá, como vai você?",
        "Estamos testando o sistema de transcrição.",
        "Este é um exemplo de transcrição gerada automaticamente.",
        "O sistema de plugins permite adicionar novos serviços de transcrição.",
        "A implementação de múltiplos serviços de transcrição aumenta a flexibilidade.",
        "Podemos escolher diferentes serviços com base nas necessidades.",
        "Esta é uma demonstração do serviço de transcrição simulado.",
        "Não é necessário uma API externa para testar o sistema.",
        "A arquitetura do sistema permite fácil extensão.",
        "Obrigado por testar este serviço de transcrição."
    ]
    
    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """
        Inicializa o serviço de transcrição simulado.
        
        Args:
            config_provider: Provedor de configuração opcional
        """
        self.config_provider = config_provider
        self.logger.info("Inicializando serviço de transcrição simulado")
    
    def transcribe(self, audio_file: str, config: Optional[Dict[str, Any]] = None,
                 allowed_audio_extensions: Optional[List[str]] = None) -> Union[TranscriptionResult, None]:
        """
        Simula a transcrição de um arquivo de áudio gerando texto fictício.
        
        Args:
            audio_file: Caminho para o arquivo de áudio a ser transcrito
            config: Parâmetros de configuração opcionais para a transcrição
            allowed_audio_extensions: Lista opcional de extensões de arquivo de áudio permitidas
            
        Returns:
            TranscriptionResult: O resultado da transcrição, ou None se a transcrição falhar
        """
        try:
            # Define extensões permitidas padrão se não fornecidas
            if allowed_audio_extensions is None:
                allowed_audio_extensions = ["mp3", "wav", "ogg", "flac", "m4a", "aac", "wma", "aiff"]
            
            # Valida o caminho do arquivo de áudio
            validate_file_path(audio_file, allowed_extensions=allowed_audio_extensions)
            
            # Verifica se o arquivo existe
            if not os.path.exists(audio_file):
                self.logger.error(f"O arquivo de áudio '{audio_file}' não foi encontrado.")
                return None
            
            # Obtém o tamanho do arquivo para simular a duração
            file_size = os.path.getsize(audio_file)
            duration_seconds = max(30, file_size / 50000)  # Simula duração com base no tamanho
            
            # Define configuração padrão
            transcription_config = {
                "speaker_labels": True,
                "speakers_expected": 2,
                "simulation_delay": 1.0  # Atraso em segundos para simular processamento
            }
            
            # Sobrescreve com a configuração fornecida, se houver
            if config:
                transcription_config.update(config)
            
            # Simula o tempo de processamento
            self.logger.info(f"Simulando transcrição de {audio_file}...")
            time.sleep(transcription_config["simulation_delay"])
            
            # Gera uma transcrição simulada
            return self._generate_mock_transcription(
                audio_file, 
                duration_seconds,
                transcription_config["speaker_labels"],
                transcription_config["speakers_expected"]
            )
            
        except ValueError as e:
            error_msg = f"Arquivo de áudio ou configuração inválida: {e}"
            self.logger.error(error_msg)
            return None
            
        except Exception as e:
            error_msg = f"Ocorreu um erro durante a transcrição simulada: {e}"
            self.logger.error(error_msg)
            return None
    
    def _generate_mock_transcription(
        self, 
        audio_file: str, 
        duration_seconds: float,
        use_speaker_labels: bool,
        speakers_count: int
    ) -> TranscriptionResult:
        """
        Gera uma transcrição simulada com base nos parâmetros fornecidos.
        
        Args:
            audio_file: Caminho para o arquivo de áudio
            duration_seconds: Duração simulada do áudio em segundos
            use_speaker_labels: Se deve incluir rótulos de falantes
            speakers_count: Número de falantes a incluir
            
        Returns:
            TranscriptionResult: Resultado da transcrição simulada
        """
        # Cria uma lista de falantes
        speakers = []
        for i in range(speakers_count):
            speakers.append(Speaker(id=f"speaker_{i+1}", name=f"Falante {i+1}"))
        
        # Determina quantas frases gerar com base na duração
        phrases_count = max(3, int(duration_seconds / 10))
        
        # Gera as falas
        utterances = []
        current_time = 0.0
        
        for i in range(phrases_count):
            # Seleciona uma frase aleatória
            phrase = random.choice(self.SAMPLE_PHRASES)
            
            # Calcula a duração da frase (aproximadamente 0.1s por caractere)
            phrase_duration = len(phrase) * 0.1
            
            # Seleciona um falante aleatório
            speaker = random.choice(speakers) if use_speaker_labels else None
            
            # Cria a fala
            utterance = Utterance(
                text=phrase,
                start=current_time,
                end=current_time + phrase_duration,
                speaker=speaker.id if speaker else None,
                confidence=random.uniform(0.75, 0.98)
            )
            
            utterances.append(utterance)
            current_time += phrase_duration + random.uniform(0.5, 2.0)  # Adiciona pausa entre falas
        
        # Cria o resultado da transcrição
        result = TranscriptionResult(
            id=f"mock_{int(time.time())}",
            audio_file=audio_file,
            text=" ".join([u.text for u in utterances]),
            utterances=utterances,
            speakers=speakers if use_speaker_labels else [],
            language="pt"
        )
        
        self.logger.info(f"Transcrição simulada gerada com {len(utterances)} falas e {len(speakers)} falantes")
        return result
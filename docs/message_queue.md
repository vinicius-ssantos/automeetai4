# Sistema de Fila de Mensagens

Este documento descreve a fila de mensagens em memória utilizada para processar grandes lotes de forma assíncrona.

A fila `InMemoryMessageQueue` permite publicar tarefas que serão processadas por workers em segundo plano. Ela é útil quando há muitos arquivos a serem transcritos ou analisados.

## Uso Básico

```python
from src.services.in_memory_message_queue import InMemoryMessageQueue

resultados = []

def handler(mensagem):
    resultados.append(mensagem)

fila = InMemoryMessageQueue(handler)
fila.iniciar(num_workers=2)

fila.publicar("arquivo1.mp4")
fila.publicar("arquivo2.mp4")

# ... realizar outras tarefas ...

fila.parar()
```

Cada mensagem publicada é entregue ao `handler` para processamento.

## Integração com o AutoMeetAI

O `AutoMeetAIFactory` pode inicializar a fila automaticamente. Basta passar o
parâmetro `use_message_queue=True` ao criar a aplicação:

```python
from src.factory import AutoMeetAIFactory

factory = AutoMeetAIFactory()
app = factory.create(use_message_queue=True, queue_workers=2)

# Enfileira vídeos para processamento
app.enfileirar_video("reuniao1.mp4")
app.enfileirar_video("reuniao2.mp4")
```

A fila será iniciada com a quantidade de *workers* especificada e processará os
vídeos em segundo plano.

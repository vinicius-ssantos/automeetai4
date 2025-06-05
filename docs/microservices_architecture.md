# Arquitetura de Microsserviços

Este documento descreve a nova abordagem de microsserviços adotada pelo AutoMeetAI.

## Visão Geral

A aplicação foi dividida em dois microsserviços principais para melhorar a escalabilidade e a separação de responsabilidades:

- **Transcription Service**: responsável por receber arquivos de vídeo e retornar a transcrição processada.
- **Analysis Service**: realiza a análise de transcrições utilizando serviços de geração de texto.

Cada microsserviço é exposto através de uma API separada com autenticação por chave. Ambos utilizam o `AutoMeetAIFactory` para construir suas dependências.

## Fila de Mensagens

Para processar grandes lotes de forma assíncrona, foi adicionada a fila `InMemoryMessageQueue`. Ela permite que arquivos sejam enfileirados e processados por workers em segundo plano.
O `AutoMeetAIFactory` oferece o parâmetro `use_message_queue` para iniciar essa fila automaticamente.

## Como Executar

Utilize o `docker-compose.yml` para iniciar os serviços:

```bash
docker compose up --build
```

Os serviços ficam disponíveis em:

- `http://localhost:8001` – Transcription Service
- `http://localhost:8002` – Analysis Service

Configure a variável `AUTOMEETAI_API_AUTH_TOKEN` para proteger as APIs.

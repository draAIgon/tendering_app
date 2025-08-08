# Hackiathon 2025 - Team draAIgon
## Reto 1 - Optimización Inteligente de Procesos de Licitación en Construcción

## Stack Tecnológico
* Python 3.10+
* FastAPI
* LangChain
* OpenAI GPT-4.1
* PyMuPDF
* DSPy

## Arquitectura

```mermaid
architecture-beta
    group frontend(cloud)[Frontend]

    service front_end_app(server)[App] in frontend

    group backend(cloud)[Backend]


    service api(server)[API] in backend
    service db(database)[ChromaDB] in backend
    service server(server)[RAG System] in backend

    api:L -- R:server
    db:R -- L:server

```

## Guia de ejecución

* Iniciar el API Gateway

```
fastapi dev backend/api.py --host 0.0.0.0
```

* Iniciar el frontend

```
python3 -m http.server 8888 --directory frontend
```

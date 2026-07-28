# PVA Expert AI Agent

Интеллектуальный AI-ассистент для компании **PVA Expert**, построенный на базе **FastAPI + RAG + GigaChat + Bitrix24**.

Проект позволяет отвечать на вопросы клиентов по базе знаний компании, использовать Retrieval-Augmented Generation (RAG), интегрироваться с Bitrix24 и масштабироваться как отдельный AI-сервис.

---

# Возможности

- FastAPI REST API
- Retrieval-Augmented Generation (RAG)
- Sentence Transformers
- GigaChat API
- Bitrix24 Webhook
- Поиск по базе знаний
- Эмбеддинги с кэшированием
- Docker
- Swagger UI
- OpenAPI
- Логирование
- Готовность к продакшену

---



---

# Структура проекта

```
ai_agent/

│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── logger.py
│   ├── rag_engine.py
│   ├── gigachat_client.py
│   ├── bitrix.py
│   │
│   ├── models/
│   │
│   ├── services/
│   │     ai_service.py
│   │
│   └── schemas/
│
├── cache/
│
├── data/
│    knowledge_base.txt
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

# Как работает RAG

```
                 Вопрос пользователя
                        │
                        ▼
             SentenceTransformer
                        │
                        ▼
               Вектор вопроса
                        │
                        ▼
          Поиск похожих эмбеддингов
                        │
                        ▼
           Top-K наиболее похожих
                        │
                        ▼
          Формирование контекста
                        │
                        ▼
                GigaChat API
                        │
                        ▼
               Финальный ответ
```

---

# API

## Проверка работоспособности

```
GET /health
```

Ответ

```json
{
    "status":"ok",
    "version":"1.0.0"
}
```

---

## Вопрос AI

```
POST /api/v1/ask
```

Запрос

```json
{
    "question":"Какие бывают анкерные болты?"
}
```

Ответ

```json
{
    "answer":"Анкерные болты бывают клиновые, распорные и химические.",
    "confidence":0.52,
    "sources":[
        {
            "text":"...",
            "similarity":0.78
        }
    ],
    "elapsed":1.43
}
```

---

## Статистика RAG

```
GET /rag/stats
```

Ответ

```json
{
    "chunks":42,
    "indexed":true,
    "knowledge_file":"data/knowledge_base.txt",
    "cache":"cache/embeddings.pkl"
}
```

---

## Bitrix24 Webhook

```
POST /api/v1/bitrix_webhook
```

После получения webhook агент:

- извлекает вопрос
- ищет информацию в RAG
- отправляет запрос в GigaChat
- публикует ответ в задачу
- обновляет лид

---

# Используемые технологии

Backend

- Python 3.13
- FastAPI
- Uvicorn
- Pydantic
- AsyncIO

AI

- GigaChat API
- Sentence Transformers
- MiniLM-L12-v2
- Scikit-learn
- NumPy

Интеграции

- Bitrix24 REST API
- HTTPX

DevOps

- Docker
- Docker Compose

---

# Запуск

## Локально

```
python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt

python -m uvicorn app.main:app --reload
```

---

## Docker

```
docker compose up --build
```

После запуска

```
http://localhost:8000/docs
```

---

# Конфигурация

Пример `.env`

```
HOST=0.0.0.0

PORT=8000

DEBUG=True

GIGACHAT_CREDENTIALS=...

GIGACHAT_SCOPE=GIGACHAT_API_PERS

GIGACHAT_MODEL=GigaChat-2-Max

VERIFY_SSL=False

BITRIX_WEBHOOK_URL=https://company.bitrix24.ru/rest/1/...

BITRIX_USER_ID=1

LOG_LEVEL=INFO
```

---

# Логирование

Все основные события логируются:

- запуск приложения
- загрузка модели
- индексация RAG
- поиск документов
- обращения к GigaChat
- обработка Bitrix24
- ошибки

---

# Производительность

Используется:

- кэш эмбеддингов
- cosine similarity
- нормализованные вектора
- повторное использование индекса
- асинхронная обработка запросов

---

# Возможности дальнейшего развития

- PostgreSQL
- Redis Cache
- Celery
- Prometheus
- Grafana
- Kubernetes
- LangChain
- OpenTelemetry
- Streaming ответов
- История диалогов
- Авторизация пользователей
- Админ-панель

---

# Автор

**Егор Сухарев**

Backend Developer (.NET / Python / AI)

2026

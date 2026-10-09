from __future__ import annotations

from app.logger import logger
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.rag_engine import rag_engine

from app.history import history_service

from app import __version__
from app.logger import logger
from app.models import (
    AskRequest,
    BitrixWebhookRequest,
    BitrixWebhookResponse,
    HealthResponse,
)
from app.services.ai_service import ai_service
from app.bitrix_integration import bitrix


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / Shutdown приложения.
    """

    logger.info("=" * 60)
    logger.info("Запуск PVA Expert AI Agent")
    logger.info("=" * 60)

    await ai_service.initialize()

    logger.info("Приложение успешно запущено.")

    yield

    logger.info("Остановка приложения...")

    await ai_service.shutdown()

    logger.info("Приложение остановлено.")


app = FastAPI(
    title="PVA Expert AI Agent API",
    description="""
## AI-помощник для компании PVA Expert

### Возможности

- Ответы на вопросы через GigaChat
- RAG-поиск по внутренней базе знаний
- Поиск релевантных документов
- История запросов
- Статистика индекса
- Переиндексация базы знаний
- Интеграция с Bitrix24

---

Разработано на:

- FastAPI
- Sentence Transformers
- GigaChat
- Docker
- Bitrix24 REST API
""",
    version="1.0.0",
    contact={
        "name": "Egor Sukharev",
        "url": "https://github.com/xXEgor4EXx",
    },
    license_info={
        "name": "MIT",
    },
)


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(exc)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Внутренняя ошибка сервера."
        },
    )

@app.get(
    "/api/v1/history",
    tags=["History"],
    summary="История запросов",
    description="""
Возвращает последние запросы пользователей.

Для каждого запроса отображаются:

- дата;
- вопрос;
- ответ AI;
- confidence поиска.
""",
)
async def history():

    return history_service.get_all()

@app.delete("/api/v1/history")
async def clear_history():

    history_service.clear()

    return {
        "status": "ok"
    }

@app.get(
    "/health",
    tags=["System"],
    summary="Проверка работоспособности",
    description="""
Проверяет, что сервис успешно запущен.

Используется Docker, Kubernetes и балансировщиками
для проверки состояния приложения.
""",
    response_model=HealthResponse,
)
async def health():

    stats = ai_service.__dict__

    return HealthResponse(
        status="ok",
        version=__version__,
    )

@app.get(
    "/api/v1/rag/stats",
    tags=["RAG"],
    summary="Статистика индекса",
    description="""
Возвращает информацию о текущем RAG-индексе.

Содержит:

- количество чанков;
- состояние индексации;
- путь к базе знаний;
- путь к кэшу эмбеддингов.
""",
)
async def rag_stats():

    return rag_engine.stats()

@app.post(
    "/api/v1/rag/reload",
    tags=["RAG"],
    summary="Переиндексация базы знаний",
    description="""
Удаляет текущий индекс RAG и строит его заново.

Используется после изменения файла knowledge_base.txt.
""",
)
async def reload_rag():

    await rag_engine.reload()

    return {
        "status": "ok",
        "message": "База знаний переиндексирована."
    }

@app.post(
    "/api/v1/ask",
    tags=["AI"],
    summary="Задать вопрос AI",
    description="""
Основной endpoint AI-агента.

Этапы обработки запроса:

1. Выполняется поиск наиболее релевантных документов в базе знаний (RAG).
2. Формируется контекст из найденных источников.
3. Контекст отправляется в GigaChat.
4. Возвращается ответ модели, уровень уверенности поиска и найденные источники.

Используется веб-интерфейсом, мобильным приложением и Bitrix24.
""",
)
async def ask(
    request: AskRequest,
):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вопрос пустой.",
        )

    started = time.perf_counter()

    response = await ai_service.ask(question)

    elapsed = round(
        time.perf_counter() - started,
        3,
    )

    logger.info(
        "POST /ask | %.2f ms | confidence=%.3f",
        elapsed * 1000,
        response.confidence,
    )

    response.elapsed_ms = round(elapsed * 1000, 2)

    return response


@app.post(
    "/api/v1/bitrix_webhook",
    tags=["Bitrix24"],
    summary="Обработка webhook Bitrix24",
    description="""
Принимает webhook от Bitrix24.

Алгоритм работы:

1. Получение события.
2. Извлечение текста вопроса.
3. Поиск информации через RAG.
4. Генерация ответа GigaChat.
5. Добавление комментария к задаче или обновление лида.

Endpoint предназначен исключительно для интеграции с Bitrix24.
""",
    response_model=BitrixWebhookResponse,
)
async def bitrix_webhook(
    request: BitrixWebhookRequest,
) -> BitrixWebhookResponse:

    payload = bitrix.parse_bitrix_webhook(
        request.model_dump()
    )

    question = payload["question"]

    if not question:

        raise HTTPException(
            status_code=400,
            detail="В webhook отсутствует текст вопроса.",
        )

    response = await ai_service.ask(
        question
    )

    sent = await bitrix.send_to_bitrix(
        task_id=(
            int(payload["task_id"])
            if payload["task_id"] is not None
            else None
        ),
        lead_id=(
            int(payload["lead_id"])
            if payload["lead_id"] is not None
            else None
        ),
        answer=response.answer,
    )

    if not sent:

        logger.warning(
            "Ответ сгенерирован, но не удалось отправить его в Bitrix24."
        )

    return BitrixWebhookResponse(
        success=True,
        message="Webhook успешно обработан.",
    )


@app.get("/")
async def root():

    return {
        "service": "PVA Expert AI Agent",
        "version": "1.0.0",
        "swagger": "/docs",
        "health": "/api/v1/health",
        "rag": "/api/v1/rag/stats",
    }

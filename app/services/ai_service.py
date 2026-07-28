from __future__ import annotations

import time

from app.history import history_service
from app.gigachat_client import gigachat
from app.logger import logger
from app.models import (
    AskResponse,
    SourceChunk,
)
from app.rag_engine import rag_engine


class AIService:
    """
    Основная бизнес-логика AI-агента.

    Последовательность работы:

    Запрос
        ↓
    RAG
        ↓
    GigaChat
        ↓
    Ответ
    """

    async def initialize(self) -> None:
        """
        Инициализация сервисов.
        """

        logger.info("Инициализация AIService...")

        await rag_engine.initialize()

        await gigachat.initialize()

        logger.info("AIService готов.")

    async def ask(
        self,
        question: str,
    ) -> AskResponse:
        """
        Получить ответ AI.
        """

        started = time.perf_counter()

        context, confidence, sources = await rag_engine.build_context(
            question
        )

        answer = await gigachat.ask(
            question=question,
            context=context,
        )

        elapsed = round(
            time.perf_counter() - started,
            3,
        )

        logger.info(
            "Вопрос: %s",
            question,
        )

        logger.info(
            "Время обработки: %.3f сек",
            elapsed,
        )

        logger.info(
            "Уверенность: %.3f",
            confidence,
        )

        logger.info(
            "Ответ: %s",
            answer.replace("\n", " "),
        )

        history_service.add(
        question=question,
        answer=answer,
        confidence=confidence,
        )
        return AskResponse(
            answer=answer,
            confidence=confidence,
            sources=[
                SourceChunk(
                    text=item["text"],
                    similarity=item["similarity"],
                )
                for item in sources
            ],
        )

    async def shutdown(self) -> None:
        """
        Корректное завершение работы.
        """

        logger.info(
            "Остановка AIService..."
        )

        await gigachat.close()

        logger.info(
            "AIService остановлен."
        )


ai_service = AIService()
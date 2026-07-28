from __future__ import annotations

import asyncio
from typing import Optional

from gigachat import GigaChat
from gigachat.models import Chat, Messages
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.logger import logger


SYSTEM_PROMPT = """
Ты AI-консультант компании PVA EXPERT.

Компания занимается продажей крепежа и строительного инструмента.

Правила:

1. Отвечай только на основании предоставленного контекста.
2. Не придумывай характеристики товаров.
3. Если информации недостаточно — честно скажи об этом.
4. Отвечай кратко, профессионально и на русском языке.
"""


class GigaChatClient:
    """
    Клиент GigaChat.

    Потокобезопасный singleton.
    """

    def __init__(self) -> None:

        self._client: Optional[GigaChat] = None

        self._lock = asyncio.Lock()

    async def initialize(self) -> None:

        if self._client is not None:
            return

        async with self._lock:

            if self._client is not None:
                return

            logger.info("Инициализация GigaChat...")

            self._client = GigaChat(
                credentials=settings.GIGACHAT_CREDENTIALS,
                scope=settings.GIGACHAT_SCOPE,
                verify_ssl_certs=settings.VERIFY_SSL,
            )

            logger.info("GigaChat готов.")

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1),
    )
    async def ask(
        self,
        question: str,
        context: str,
    ) -> str:

        await self.initialize()

        prompt = f"""
Контекст:

{context}

Вопрос:

{question}
"""

        logger.info(
            "Отправка вопроса в GigaChat."
        )

        response = await asyncio.to_thread(
            self._client.chat,
            Chat(
                model=settings.GIGACHAT_MODEL,
                temperature=0.3,
                messages=[
                    Messages(
                        role="system",
                        content=SYSTEM_PROMPT,
                    ),
                    Messages(
                        role="user",
                        content=prompt,
                    ),
                ],
            ),
        )

        answer = response.choices[0].message.content

        logger.info("Ответ получен.")

        return answer.strip()

    async def close(self) -> None:

        if self._client is None:
            return

        logger.info(
            "Закрытие клиента GigaChat."
        )

        try:
            self._client.close()
        except Exception as ex:
            logger.error(ex)

        self._client = None


gigachat = GigaChatClient()
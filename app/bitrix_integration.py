from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.logger import logger


class BitrixIntegration:
    """
    Интеграция с Bitrix24 REST API.
    """

    def __init__(self) -> None:
        self.base_url = settings.BITRIX_WEBHOOK_URL.rstrip("/")

    async def _post(
        self,
        method: str,
        body: dict[str, Any],
    ) -> bool:
        """
        Универсальный POST запрос в Bitrix24.
        """

        if not self.base_url:

            logger.warning(
                "BITRIX_WEBHOOK_URL не настроен."
            )

            return False

        url = f"{self.base_url}/{method}.json"

        try:

            async with httpx.AsyncClient(
                timeout=20,
            ) as client:

                response = await client.post(
                    url,
                    json=body,
                )

            if response.is_success:

                logger.info(
                    "Bitrix %s выполнен успешно.",
                    method,
                )

                return True

            logger.error(
                "Bitrix %s (%s): %s",
                method,
                response.status_code,
                response.text,
            )

            return False

        except Exception:

            logger.exception(
                "Ошибка обращения к Bitrix."
            )

            return False

    def parse_bitrix_webhook(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:

        logger.info(
            "Получен webhook Bitrix24."
        )

        payload = data.get(
            "data",
            {},
        )

        return {

            "event":
                data.get("event"),

            "payload":
                payload,

            "task_id":
                payload.get("TASK_ID"),

            "lead_id":
                payload.get("ID"),

            "question":
                payload.get("COMMENT")
                or payload.get("DESCRIPTION")
                or payload.get("TITLE")
                or "",
        }
    async def add_task_comment(
        self,
        task_id: int,
        comment: str,
    ) -> bool:
        """
        Добавляет комментарий к задаче Bitrix24.
        """

        return await self._post(
            "task.commentitem.add",
            {
                "TASKID": task_id,
                "FIELDS": {
                    "POST_MESSAGE": comment,
                },
            },
        )

    async def update_lead(
        self,
        lead_id: int,
        fields: dict[str, Any],
    ) -> bool:
        """
        Обновляет поля лида.
        """

        return await self._post(
            "crm.lead.update",
            {
                "id": lead_id,
                "fields": fields,
            },
        )

    async def send_to_bitrix(
        self,
        *,
        task_id: int | None = None,
        lead_id: int | None = None,
        answer: str,
    ) -> bool:
        """
        Универсальная отправка ответа в Bitrix24.

        Если указан task_id — создаётся комментарий.

        Если указан lead_id — обновляется поле COMMENTS.
        """

        success = True

        if task_id is not None:

            success &= await self.add_task_comment(
                task_id=task_id,
                comment=answer,
            )

        if lead_id is not None:

            success &= await self.update_lead(
                lead_id=lead_id,
                fields={
                    "COMMENTS": answer,
                },
            )

        return success


bitrix = BitrixIntegration()
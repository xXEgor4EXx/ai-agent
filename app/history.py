from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


HISTORY_FILE = Path("data/history.json")


class HistoryService:

    def __init__(self) -> None:

        HISTORY_FILE.parent.mkdir(exist_ok=True)

        if not HISTORY_FILE.exists():
            HISTORY_FILE.write_text(
                "[]",
                encoding="utf-8",
            )

    def add(
        self,
        question: str,
        answer: str,
        confidence: float,
    ) -> None:

        history = self.get_all()

        history.insert(
            0,
            {
                "datetime": datetime.now().isoformat(),
                "question": question,
                "answer": answer,
                "confidence": confidence,
            },
        )

        history = history[:100]

        HISTORY_FILE.write_text(
            json.dumps(
                history,
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )

    def get_all(self):

        return json.loads(
            HISTORY_FILE.read_text(
                encoding="utf-8",
            )
        )

    def clear(self):

        HISTORY_FILE.write_text(
            "[]",
            encoding="utf-8",
        )


history_service = HistoryService()
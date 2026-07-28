from __future__ import annotations

import hashlib
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.logger import logger


CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CACHE_FILE = CACHE_DIR / "embeddings.pkl"


@dataclass
class Chunk:
    text: str
    embedding: np.ndarray | None = None


class RAGEngine:
    """
    RAG-движок.

    Возможности:

    - загрузка базы знаний;
    - чанкинг текста;
    - построение эмбеддингов;
    - кэширование;
    - поиск похожих документов.
    """

    def __init__(self) -> None:

        self.model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )

        self.chunks: list[Chunk] = []

        self.embeddings: np.ndarray | None = None

        self.knowledge_path = Path(settings.KNOWLEDGE_FILE)

        self.file_hash = ""

    async def initialize(self) -> None:
        """
        Полная инициализация индекса.
        """

        logger.info("Инициализация RAG...")

        text = self._load_file()

        self.file_hash = self._calculate_hash(text)

        if self._load_cache():
            logger.info("Используется кэш эмбеддингов.")
            return

        self.chunks = self._split_into_chunks(text)

        await self._build_embeddings()

        self._save_cache()

        logger.info(
            "Индекс успешно построен. Чанков: %d",
            len(self.chunks),
        )

    def _load_file(self) -> str:

        if not self.knowledge_path.exists():
            raise FileNotFoundError(
                f"{self.knowledge_path} не найден."
            )

        return self.knowledge_path.read_text(
            encoding="utf-8"
        )

    def _calculate_hash(self, text: str) -> str:

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

    def _split_into_chunks(
        self,
        text: str,
    ) -> list[Chunk]:

        chunks: list[Chunk] = []

        size = settings.CHUNK_SIZE

        overlap = settings.CHUNK_OVERLAP

        step = size - overlap

        for start in range(0, len(text), step):

            part = text[start:start + size].strip()

            if len(part) < 30:
                continue

            chunks.append(
                Chunk(text=part)
            )

        return chunks

    async def _build_embeddings(self) -> None:

        logger.info(
            "Создание эмбеддингов..."
        )

        texts = [
            chunk.text
            for chunk in self.chunks
        ]

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        self.embeddings = vectors

        for chunk, vector in zip(
            self.chunks,
            vectors,
        ):
            chunk.embedding = vector

    def _save_cache(self) -> None:

        with open(
            CACHE_FILE,
            "wb",
        ) as file:

            pickle.dump(
                {
                    "hash": self.file_hash,
                    "chunks": self.chunks,
                    "embeddings": self.embeddings,
                },
                file,
            )

        logger.info(
            "Кэш сохранён."
        )

    def _load_cache(self) -> bool:

        if not CACHE_FILE.exists():
            return False

        try:

            with open(
                CACHE_FILE,
                "rb",
            ) as file:

                cache = pickle.load(file)

            if cache["hash"] != self.file_hash:
                return False

            self.chunks = cache["chunks"]

            self.embeddings = cache["embeddings"]

            return True

        except Exception as ex:

            logger.error(
                "Ошибка чтения кэша: %s",
                ex,
            )

            return False

    async def search(
        self,
        question: str,
        top_k: int | None = None,
        ) -> list[dict]:
        """
        Выполняет поиск наиболее релевантных чанков.

        Возвращает список:

        [
            {
                "text": "...",
                "similarity": 0.84
            }
        ]
        """

        if self.embeddings is None:
            raise RuntimeError(
               "RAG индекс не построен."
            )

        if top_k is None:
            top_k = settings.TOP_K

        logger.info(
            "Поиск по вопросу: %s",
            question,
        )

        query_vector = self.model.encode(
            question,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        similarities = cosine_similarity(
            [query_vector],
            self.embeddings,
        )[0]

        # Индекс + коэффициент похожести
        pairs = list(enumerate(similarities))

        # Сортировка по убыванию
        pairs.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        # Удаляем нерелевантные результаты
        filtered = [
            pair
            for pair in pairs
            if pair[1] >= settings.MIN_SIMILARITY
        ]

        # Ограничиваем количество
        filtered = filtered[:top_k]

        results: list[dict] = []

        for index, similarity in filtered:

            results.append(
                {
                    "text": self.chunks[index].text,
                    "similarity": round(
                    float(similarity),
                    4,
                ),
            }
        )

        return results

    async def build_context(
        self,
        question: str,
    ) -> tuple[str, float, list[dict]]:
        """
        Формирует контекст для LLM.

        Возвращает:

        (
            context,
            confidence,
            sources
        )
        """

        sources = await self.search(question)

        if not sources:

            logger.warning(
                "По запросу '%s' релевантные документы не найдены.",
                question,
            )

            return (
                "",
                0.0,
                [],
            )

        context = "\n\n".join(
        source["text"]
        for source in sources
        )

        # Ограничиваем размер контекста для LLM
        if len(context) > settings.MAX_CONTEXT_LENGTH:
            context = context[: settings.MAX_CONTEXT_LENGTH]

        # Уверенность = лучшая найденная похожесть
        confidence = max(
            source["similarity"]
            for source in sources
        )

        return (
            context,
            round(confidence, 4),
            sources,
        )

    async def reload(self) -> None:
        """
        Полная переиндексация.
        """

        logger.info(
            "Переиндексация базы знаний..."
        )

        self.chunks.clear()

        self.embeddings = None

        if CACHE_FILE.exists():
            CACHE_FILE.unlink()

        await self.initialize()

    def stats(self) -> dict:
        """
        Информация об индексе.
        """

        return {
            "chunks": len(self.chunks),
            "indexed": self.embeddings is not None,
            "knowledge_file": str(
                self.knowledge_path
            ),
            "cache": str(
                CACHE_FILE
            ),
        }


rag_engine = RAGEngine()
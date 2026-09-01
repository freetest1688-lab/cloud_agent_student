"""Milvus vector-database-backed long-term memory.

User preferences and key facts are stored as dense vector embeddings.
Retrieval uses cosine-similarity search filtered by user_id, keeping each
user's memories isolated.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

COLLECTION_NAME = "long_term_memory"
EMBEDDING_DIM = 1536  


class LongTermMemory:
    """Milvus-based long-term memory for user preferences and facts.

    Features:
    - Dense vector search via Milvus (cosine similarity)
    - Scalar filtering on ``user_id`` for per-user isolation
    - Preference helper: ``save_preference(user_id, type, value)``
    - Graceful degradation: operations become no-ops when Milvus is unavailable

    Usage::

        mem = LongTermMemory(embedding_api_key="sk-...")
        await mem.initialize()

        await mem.save_preference("user1", "language", "Chinese")
        results = await mem.retrieve_relevant("user1", "preferred language")
        await mem.close()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        api_key: str | None = None,
        embedding_api_key: str | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._api_key = api_key
        self._embedding_api_key = embedding_api_key
        self._client: Any = None
        self._embeddings: Any = None
        self._available: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Connect to Milvus and ensure collection exists.

        Sets _available=False on failure (no exception raised).
        """
        try:
            from pymilvus import MilvusClient  # type: ignore[import]
            from langchain_openai import OpenAIEmbeddings  # type: ignore[import]

            uri = f"http://{self._host}:{self._port}"
            connect_kwargs: dict[str, Any] = {"uri": uri}
            if self._api_key:
                connect_kwargs["token"] = self._api_key

            self._client = MilvusClient(**connect_kwargs)
            self._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=self._embedding_api_key,
            )
            self._ensure_collection()
            self._available = True
            logger.info("LongTermMemory: Milvus connected at %s:%s", self._host, self._port)
        except Exception as exc:
            logger.warning(
                "LongTermMemory: Milvus unavailable (%s) – long-term memory disabled.", exc
            )
            self._available = False

    async def close(self) -> None:
        """Close Milvus client."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def save_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "general",
    ) -> None:
        """Embed and store a memory entry.

        Args:
            user_id: Owner of this memory.
            content: Text to embed and store.
            memory_type: Category label (e.g. "preference", "fact").
        """
        if not self._available:
            return
        try:
            # ================== TODO 18 - Embed + store ==================
            # GOAL : Embed the text and insert one row into Milvus.
            # WHY  : Long-term memory is a vector row: the embedding is the index, not the payload.
            # STEPS:
            #   1. embedding = await self._embeddings.aembed_query(content).
            #   2. self._client.insert(collection_name=COLLECTION_NAME, data=[{...}]).
            #   3. The dict needs user_id, content, memory_type and embedding.
            #   4. Log at debug (truncate content to ~60 chars).
            # HINT : data= takes a LIST of dicts even for a single row.
            # CHECK: After a chat, check the collection is non-empty via pymilvus.
            # SIZE : ~8 lines
            raise NotImplementedError("TODO 18: embed and insert into Milvus")
            # ======================================================
        except Exception as exc:
            logger.error("LongTermMemory.save_memory failed: %s", exc)

    async def save_preference(
        self, user_id: str, preference_type: str, value: str
    ) -> None:
        """Convenience wrapper for storing a user preference.

        Args:
            user_id: Owner of this preference.
            preference_type: Short label (e.g. "language", "city").
            value: Preference value (e.g. "Chinese", "Beijing").
        """
        content = f"User preference – {preference_type}: {value}"
        await self.save_memory(user_id, content, memory_type="preference")

    async def retrieve_relevant(
        self, user_id: str, query: str, top_k: int = 5
    ) -> list[str]:
        """Return the top-k most relevant memory entries for a query.

        Args:
            user_id: Filter results to this user only.
            query: Natural-language query text.
            top_k: Maximum number of results to return.

        Returns:
            List of content strings ordered by relevance.
        """
        if not self._available:
            return []
        try:
            # ================== TODO 19 - Vector search ==================
            # GOAL : Retrieve the top-k memories for this user only.
            # WHY  : The filter is a security control: without it you retrieve other users' memories.
            # STEPS:
            #   1. Embed the query with aembed_query.
            #   2. self._client.search(collection_name=..., data=[query_embedding], filter=f'user_id == "{user_id}"', limit=top_k, output_fields=['content','memory_type']).
            #   3. Results are nested: iterate hits, then hit['entity']['content'].
            #   4. Return a flat list of content strings.
            # HINT : data=[embedding] is a list of query vectors - search supports batching.
            # CHECK: Save a preference as user A, then query as user B - B must get nothing.
            # SIZE : ~10 lines
            raise NotImplementedError("TODO 19: run the filtered vector search")
            # ======================================================
        except Exception as exc:
            logger.error("LongTermMemory.retrieve_relevant failed: %s", exc)
            return []

    @property
    def available(self) -> bool:
        """True if Milvus is reachable."""
        return self._available

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_collection(self) -> None:
        """Create the Milvus collection and index if they do not exist."""
        from pymilvus import DataType  # type: ignore[import]

        if self._client.has_collection(COLLECTION_NAME):
            return

        schema = self._client.create_schema()
        schema.add_field("id", DataType.INT64, is_primary=True, auto_id=True)
        schema.add_field("user_id", DataType.VARCHAR, max_length=128)
        schema.add_field("content", DataType.VARCHAR, max_length=2048)
        schema.add_field("memory_type", DataType.VARCHAR, max_length=64)
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)

        index_params = self._client.prepare_index_params()
        index_params.add_index(
            "embedding",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 128},
        )

        self._client.create_collection(
            collection_name=COLLECTION_NAME,
            schema=schema,
            index_params=index_params,
        )
        logger.info("LongTermMemory: created Milvus collection '%s'", COLLECTION_NAME)

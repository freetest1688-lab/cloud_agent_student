"""Redis-backed short-term conversation memory.

Messages are stored per user/session and expire based on TTL.
When the message count exceeds COMPRESSION_THRESHOLD, older messages
are automatically trimmed to retain only the most recent ones.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

COMPRESSION_THRESHOLD = 10  # trim when messages exceed this count
DEFAULT_TTL = 1800          # 30 minutes in seconds


class ShortTermMemory:
    """Redis-backed short-term conversation memory.

    Features:
    - Key isolation per user/session (``memory:short:{user_id}:{session_id}``)
    - Automatic TTL-based expiry (default 30 minutes, configurable)
    - Automatic message trimming when COMPRESSION_THRESHOLD is exceeded
    - Graceful degradation: operations become no-ops when Redis is unavailable

    Usage::

        mem = ShortTermMemory()
        await mem.initialize()

        await mem.save_messages("user1", "s1", messages)
        msgs = await mem.get_messages("user1", "s1")
        await mem.close()
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = DEFAULT_TTL) -> None:
        self._redis_url = redis_url
        self._ttl = ttl
        self._client: Any = None
        self._available: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Connect to Redis; sets _available=False on failure (no exception raised)."""
        try:
            import redis.asyncio as aioredis  # type: ignore[import]

            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                health_check_interval=30,
                retry_on_timeout=True,
            )
            await self._client.ping()
            self._available = True
            logger.info("ShortTermMemory: Redis connected at %s", self._redis_url)
        except Exception as exc:
            logger.warning(
                "ShortTermMemory: Redis unavailable (%s) – short-term memory disabled.", exc
            )
            self._available = False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_messages(self, user_id: str, session_id: str) -> list[dict[str, Any]]:
        """Return stored messages for the given user/session.

        Returns an empty list when Redis is unavailable or the key is missing.
        """
        if not self._available:
            return []
        try:
            data = await self._client.get(self._key(user_id, session_id))
            return json.loads(data) if data else []
        except Exception as exc:
            logger.warning("ShortTermMemory.get_messages failed: %s", exc)
            self._available = False
            return []

    async def save_messages(
        self, user_id: str, session_id: str, messages: list[dict[str, Any]]
    ) -> None:
        """Persist messages to Redis, applying compression when needed.

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.
            messages: List of message dicts with ``role`` and ``content`` keys.
        """
        if not self._available:
            return
        try:
            # ================== TODO 16 - Save with TTL + trim ==================
            # GOAL : Persist messages, trimming when the history grows too long.
            # WHY  : Short-term memory must forget: unbounded history blows up cost and latency.
            # STEPS:
            #   1. If len(messages) > COMPRESSION_THRESHOLD, replace with self._trim(messages).
            #   2. json.dumps(messages, ensure_ascii=False) - ensure_ascii=False keeps CJK readable.
            #   3. await self._client.set(self._key(...), <json>, ex=self._ttl) - ex sets the TTL.
            #   4. Log at debug level how many were saved.
            # HINT : Forgetting ex=self._ttl is the classic bug: keys live forever and Redis fills up.
            # CHECK: redis-cli TTL <key> -> should count down from 1800, not return -1.
            # SIZE : ~9 lines
            raise NotImplementedError("TODO 16: serialize and SET with TTL")
            # ======================================================
        except Exception as exc:
            logger.warning("ShortTermMemory.save_messages failed: %s", exc)
            self._available = False

    async def append_message(
        self, user_id: str, session_id: str, role: str, content: str
    ) -> None:
        """Append a single message and re-persist."""
        messages = await self.get_messages(user_id, session_id)
        messages.append({"role": role, "content": content})
        await self.save_messages(user_id, session_id, messages)

    async def clear(self, user_id: str, session_id: str) -> None:
        """Delete all messages for a user/session."""
        if not self._available:
            return
        try:
            await self._client.delete(self._key(user_id, session_id))
        except Exception as exc:
            logger.error("ShortTermMemory.clear failed: %s", exc)

    @property
    def available(self) -> bool:
        """True if Redis is reachable."""
        return self._available

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _key(user_id: str, session_id: str) -> str:
        # ================== TODO 15 - Redis key scheme ==================
        # GOAL : Build the per-user, per-session Redis key.
        # WHY  : Key design IS the isolation boundary - a flat key leaks chats between users.
        # STEPS:
        #   1. Return an f-string: memory:short:{user_id}:{session_id}
        # HINT : Namespacing with ':' lets you SCAN 'memory:short:*' to wipe only this app's keys.
        # CHECK: redis-cli KEYS 'memory:short:*' after one chat turn.
        # SIZE : ~1 lines
        raise NotImplementedError("TODO 15: return the namespaced key")
        # ======================================================

    @staticmethod
    def _trim(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Keep system messages + the 6 most recent non-system messages."""
        # ================== TODO 17 - Trim policy ==================
        # GOAL : Keep all system messages plus the 6 most recent others.
        # WHY  : Naive truncation drops the system prompt and the agent forgets who it is.
        # STEPS:
        #   1. Split messages into system (role == 'system') and everything else.
        #   2. Return system messages + the last 6 non-system messages.
        # HINT : Order matters: system first, then recent turns.
        # CHECK: Send 15 turns, then confirm the stored list is shorter but still has system.
        # SIZE : ~4 lines
        raise NotImplementedError("TODO 17: return system msgs + last 6")
        # ======================================================

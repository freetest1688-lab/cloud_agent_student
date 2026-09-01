"""LLM-based user preference extractor for long-term memory.

Responsibilities:
- Analyze conversations with an LLM and extract structured preferences
- Deduplicate against already-stored preferences before returning new items
- Remain stateless: the caller is responsible for persistence

This module is intentionally decoupled from BaseAgent and MemoryManager
so it can be tested independently or swapped for a different extractor.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Extraction prompt – intentionally concise to minimize token usage.
_PROMPT_TEMPLATE = """\
Analyze the following conversation and extract the user's preferences, habits, and personal information.
Output each item on its own line in the format "category: value".
Include only concrete, actionable information about the user.
If there is no relevant information, output: NONE

Extraction examples:
  city: Shanghai
  language: Chinese
  habit: checks the weather every morning
  preference: concise answers
  dislikes: long-winded explanations
  personality: friendly and approachable

Conversation:
{conversation}

Extracted preferences (or "NONE"):"""


class PreferenceExtractor:
    """Extracts user preferences from conversation text using an LLM.

    Args:
        llm: Any LangChain-compatible chat model (``ainvoke`` required).
        max_conversation_chars: Truncate conversation input to this length
            before sending to the LLM. Keeps token usage bounded.

    Example::

        extractor = PreferenceExtractor(llm=chat_model)
        new_prefs = await extractor.extract(
            conversation_text="user: I live in Beijing...",
            existing=["city: Shanghai"],
        )
        # new_prefs -> ["city: Beijing"]
    """

    def __init__(self, llm: Any, max_conversation_chars: int = 3000) -> None:
        self._llm = llm
        self._max_chars = max_conversation_chars

    async def extract(
        self,
        conversation_text: str,
        existing: list[str] | None = None,
    ) -> list[str]:
        """Extract new preferences from conversation text.

        Args:
            conversation_text: Raw conversation (role: content lines).
            existing: Already-stored preferences for deduplication.
                      Duplicates are silently dropped.

        Returns:
            List of new preference strings in ``"category: value"`` format.
            Empty list if nothing found or on extraction failure.
        """
        truncated = conversation_text[: self._max_chars]
        logger.debug(
            "[EXTRACTOR] Input conversation (%d chars, truncated to %d):\n%s",
            len(conversation_text), len(truncated), truncated[:400],
        )
        prompt = _PROMPT_TEMPLATE.format(conversation=truncated)

        try:
            response = await self._llm.ainvoke([{"role": "user", "content": prompt}])
            raw = response.content.strip()
            logger.debug("[EXTRACTOR] LLM raw response: %s", raw)
        except Exception as exc:
            logger.warning("PreferenceExtractor LLM call failed: %s", exc)
            return []

        if not raw or raw.strip() in ("NONE", "none", "No relevant information"):
            logger.info("[EXTRACTOR] LLM found no preferences")
            return []

        # Parse lines that look like "category: value"
        candidates = [line.strip() for line in raw.split("\n") if ":" in line]
        logger.debug("[EXTRACTOR] Parsed %d candidates: %s", len(candidates), candidates)
        if not candidates:
            return []

        if not existing:
            logger.info("[EXTRACTOR] No existing prefs, keeping all %d candidates", len(candidates))
            return candidates

        # Deduplicate: skip items whose text substantially overlaps existing
        existing_lower = [e.lower() for e in existing]
        new_items: list[str] = []
        for item in candidates:
            item_lower = item.lower()
            if any(item_lower in ex or ex in item_lower for ex in existing_lower):
                logger.debug("[EXTRACTOR] Duplicate skipped: %s", item)
                continue
            new_items.append(item)

        logger.info(
            "[EXTRACTOR] Result: %d new / %d skipped(dup) / %d total candidates",
            len(new_items), len(candidates) - len(new_items), len(candidates),
        )
        return new_items

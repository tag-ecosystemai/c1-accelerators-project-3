from __future__ import annotations

from pydantic import BaseModel


class KnowledgeResult(BaseModel):
    """A retrieved knowledge item returned to the agent."""

    content: str
    source: str
    relevance_score: float
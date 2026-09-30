from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NewsArticle(BaseModel):
    """Structured disruption-related news article."""

    title: str
    url: str
    source: str
    published_at: datetime | None = None
    summary: str | None = None
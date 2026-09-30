from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from intelligence.schemas.news import NewsArticle


GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


class NewsRepository:
    """Repository for retrieving disruption-related news from GDELT."""

    def search(
        self,
        query: str,
        timespan: str = "7d",
        max_records: int = 10,
    ) -> list[NewsArticle]:
        """Search recent news articles matching a query."""

        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "timespan": timespan,
            "maxrecords": max_records,
            "sort": "datedesc",
        }

        try:
            response = httpx.get(
                GDELT_URL,
                params=params,
                timeout=15.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise RuntimeError(
                    "News service rate limit reached. "
                    "Please retry later."
                ) from exc

            raise RuntimeError(
                f"News service returned HTTP "
                f"{exc.response.status_code}."
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"News service request failed: {exc}"
            ) from exc

        data: dict[str, Any] = response.json()

        articles: list[NewsArticle] = []

        for record in data.get("articles", []):
            published_at = self._parse_timestamp(
                record.get("seendate")
            )

            articles.append(
                NewsArticle(
                    title=record.get("title", ""),
                    url=record.get("url", ""),
                    source=record.get("domain", "Unknown"),
                    published_at=published_at,
                    summary=record.get("snippet"),
                )
            )

        return articles

    @staticmethod
    def _parse_timestamp(
        value: str | None,
    ) -> datetime | None:
        """Parse a GDELT publication timestamp."""
        if not value:
            return None

        try:
            return datetime.strptime(
                value,
                "%Y%m%dT%H%M%SZ",
            )
        except ValueError:
            return None
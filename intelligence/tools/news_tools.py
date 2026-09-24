from __future__ import annotations

from intelligence.repositories.news_repository import NewsRepository
from intelligence.schemas.news import NewsArticle


class NewsTools:
    """Tools for retrieving disruption-related news."""

    def __init__(
        self,
        repository: NewsRepository | None = None,
    ) -> None:
        self.repository = repository or NewsRepository()

    def find_disruption_news(
        self,
        country: str,
        keywords: list[str] | None = None,
        timespan: str = "7d",
        max_records: int = 10,
    ) -> list[NewsArticle]:
        """
        Find recent news relevant to a shipment destination.

        Args:
            country: Shipment destination country.
            keywords: Optional disruption-related search terms.
            timespan: GDELT search window.
            max_records: Maximum number of articles to return.

        Returns:
            Matching news articles.
        """
        search_terms = keywords or [
            "shipping",
            "port",
            "logistics",
            "disruption",
        ]

        query = f"{country} " + " ".join(search_terms)

        return self.repository.search(
            query=query,
            timespan=timespan,
            max_records=max_records,
        )
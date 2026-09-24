from intelligence.schemas.news import NewsArticle
from intelligence.tools.news_tools import NewsTools


class MockNewsRepository:
    def search(
        self,
        query: str,
        timespan: str,
        max_records: int,
    ) -> list[NewsArticle]:
        assert query == "Indonesia shipping port"
        assert timespan == "7d"
        assert max_records == 5

        return [
            NewsArticle(
                title="Port disruption affects shipping",
                url="https://example.com/article",
                source="example.com",
            )
        ]


def test_find_disruption_news():
    tools = NewsTools(repository=MockNewsRepository())

    articles = tools.find_disruption_news(
        country="Indonesia",
        keywords=["shipping", "port"],
        max_records=5,
    )

    assert len(articles) == 1
    assert articles[0].title == "Port disruption affects shipping"
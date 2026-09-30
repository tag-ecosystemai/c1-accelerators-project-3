import httpx

from intelligence.repositories.news_repository import NewsRepository


def test_search_news(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "articles": [
                    {
                        "title": "Port disruption affects shipping",
                        "url": "https://example.com/article",
                        "domain": "example.com",
                        "seendate": "20260924T100000Z",
                        "snippet": "A disruption has affected shipping operations.",
                    }
                ]
            }

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)

    repository = NewsRepository()

    articles = repository.search(
        query="shipping disruption",
        max_records=3,
    )

    assert len(articles) == 1
    assert articles[0].title == "Port disruption affects shipping"
    assert articles[0].url == "https://example.com/article"
    assert articles[0].source == "example.com"
    assert articles[0].summary == (
        "A disruption has affected shipping operations."
    )
    assert articles[0].published_at is not None


def test_search_news_rate_limit(monkeypatch):
    request = httpx.Request(
        "GET",
        "https://api.gdeltproject.org/api/v2/doc/doc",
    )

    response = httpx.Response(
        429,
        request=request,
    )

    def mock_get(*args, **kwargs):
        raise httpx.HTTPStatusError(
            "Too Many Requests",
            request=request,
            response=response,
        )

    monkeypatch.setattr(httpx, "get", mock_get)

    repository = NewsRepository()

    try:
        repository.search("shipping disruption")
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == (
            "News service rate limit reached. "
            "Please retry later."
        )


def test_search_news_network_failure(monkeypatch):
    def mock_get(*args, **kwargs):
        raise httpx.ConnectError("Connection failed")

    monkeypatch.setattr(httpx, "get", mock_get)

    repository = NewsRepository()

    try:
        repository.search("shipping disruption")
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == (
            "News service request failed: "
            "Connection failed"
        )
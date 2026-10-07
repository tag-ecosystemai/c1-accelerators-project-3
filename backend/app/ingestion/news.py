import time
from typing import Optional

import httpx

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MIN_INTERVAL = 6        # seconds between GDELT requests (they ask for 5)
_last_call = 0.0


def fetch_news(query: str, max_records: int = 5) -> Optional[list]:
    """Return recent headlines, [] if none match, or None if the service fails."""
    global _last_call

    # Never call GDELT faster than its limit
    wait = MIN_INTERVAL - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)

    for attempt in range(2):
        _last_call = time.time()
        try:
            response = httpx.get(
                GDELT_URL,
                params={
                    "query": query,
                    "mode": "artlist",
                    "format": "json",
                    "maxrecords": max_records,
                    "timespan": "3d",
                },
                timeout=30,
            )
        except httpx.HTTPError:
            return None

        if response.status_code == 429:      # rate limited
            if attempt == 0:
                time.sleep(MIN_INTERVAL)     # wait, then try once more
                continue
            return None

        try:
            response.raise_for_status()
            articles = response.json().get("articles", [])
        except (httpx.HTTPError, ValueError):
            return None

        return [
            {
                "title": a.get("title"),
                "url": a.get("url"),
                "domain": a.get("domain"),
                "seen": a.get("seendate"),
            }
            for a in articles
        ]

    return None
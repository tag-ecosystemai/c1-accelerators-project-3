import time

import httpx

params = {
    "query": '"Indonesia" (port OR shipping OR flood)',
    "mode": "artlist",
    "format": "json",
    "maxrecords": 5,
    "timespan": "3d",
}

start = time.time()
try:
    r = httpx.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params, timeout=30)
    print("Status:", r.status_code)
    print("Seconds:", round(time.time() - start, 1))
    print("Content-Type:", r.headers.get("content-type"))
    print("First 300 characters:")
    print(r.text[:300])
except Exception as e:
    print("Failed after", round(time.time() - start, 1), "seconds")
    print("Error type:", type(e).__name__)
    print("Error:", e)
import time
import requests
from typing import Any, Dict, Optional


def post_results(url: str, payload: Dict[str, Any], max_retries: int = 3, backoff_factor: float = 0.5) -> Optional[requests.Response]:
    """POST payload to evaluation_url with simple exponential backoff.

    Returns the successful requests.Response or None if all retries failed.
    """
    if not url:
        return None

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code < 400:
                return r
            # treat 4xx as non-retriable except 429
            if 400 <= r.status_code < 500 and r.status_code != 429:
                return r
            # else fallthrough to retry
        except requests.RequestException:
            r = None

        sleep = backoff_factor * (2 ** (attempt - 1))
        time.sleep(sleep)

    return None

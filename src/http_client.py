from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import settings


def build_session() -> Session:
    retry = Retry(
        total=settings.request_retries,
        connect=settings.request_retries,
        read=settings.request_retries,
        status=settings.request_retries,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
            )
        }
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_text(url: str) -> str:
    response = build_session().get(url, timeout=settings.request_timeout_seconds)
    response.raise_for_status()
    return response.text


def get_json(url: str, params: dict | None = None) -> dict:
    response = build_session().get(url, params=params, timeout=settings.request_timeout_seconds)
    response.raise_for_status()
    return response.json()

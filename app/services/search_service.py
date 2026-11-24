import time
import httpx
from app.config import settings
from app.utils.logger import logger

CACHE_TTL_SECONDS = 600  # 10 minutes
MAX_CACHE_ENTRIES = 50


class SearchService:
    def __init__(self):
        self.tavily_api_key = settings.tavily_api_key
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[float, list[dict]]] = {}

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(6.0, connect=3.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    async def search_web(self, query: str, max_results: int = 3) -> list[dict]:
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        if not self.tavily_api_key:
            logger.warning("TAVILY_API_KEY not configured. Returning simulated mock search results.")
            return [
                {
                    "title": f"Mock Research Result for: {clean_query}",
                    "url": "https://example.com/research-source",
                    "content": f"Comprehensive findings and factual analysis regarding {clean_query} gathered from verified academic and technical literature.",
                }
            ]

        effective_max = min(max_results, 3)
        cache_key = f"{clean_query.lower()}::{effective_max}"
        now = time.time()

        # Instant return (<1ms) if query was searched recently
        cached = self._cache.get(cache_key)
        if cached and (now - cached[0]) < CACHE_TTL_SECONDS:
            logger.info(f"Tavily cache hit for query: '{clean_query[:40]}'")
            return cached[1]

        try:
            client = self._get_client()
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_api_key,
                    "query": clean_query[:400],
                    "search_depth": "basic",
                    "max_results": effective_max,
                    "include_answer": False,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(
                    {
                        "title": (item.get("title") or "").strip(),
                        "url": (item.get("url") or "").strip(),
                        "content": (item.get("content") or "").strip()[:600],
                    }
                )

            # Lightweight RAM-safe cache eviction
            if len(self._cache) >= MAX_CACHE_ENTRIES:
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = (now, results)

            return results
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return []


search_service = SearchService()
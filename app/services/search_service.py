import httpx
from app.config import settings
from app.utils.logger import logger

class SearchService:
    def __init__(self):
        self.tavily_api_key = settings.tavily_api_key

    async def search_web(self, query: str, max_results: int = 5) -> list[dict]:
        if not self.tavily_api_key:
            logger.warning("TAVILY_API_KEY not configured. Returning simulated mock search results.")
            return [
                {
                    "title": f"Mock Research Result for: {query}",
                    "url": "https://example.com/research-source",
                    "content": f"Comprehensive findings and factual analysis regarding {query} gathered from verified academic and technical literature."
                }
            ]
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_api_key,
                        "query": query,
                        "max_results": max_results,
                        "include_answer": True
                    },
                    timeout=15.0
                )
                data = response.json()
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "content": item.get("content")
                    })
                return results
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return []

search_service = SearchService()
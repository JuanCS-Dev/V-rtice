"""Google OSINT Service for the Vertice Project.

This service specializes in conducting Open Source Intelligence (OSINT) gathering
by leveraging advanced Google search techniques, commonly known as "Google Dorking."
It provides a structured way to search for information about people, emails,
domains, documents, and more.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import aiohttp
import redis
import json
import hashlib
import logging
import random
import urllib.parse
import re

# ============================================================================
# Configuration and Initialization
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Google OSINT Service",
    description="A service specializing in OSINT using Google Dorking techniques.",
    version="1.0.0"
)

try:
    redis_client = redis.Redis(host='redis', port=6379, db=3, decode_responses=True)
    redis_client.ping()
    logger.info("Successfully connected to Redis.")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# ============================================================================
# Pydantic Models
# ============================================================================

class SearchType(str, Enum):
    """Enumeration for the different types of OSINT searches."""
    PERSON = "person"
    EMAIL = "email"
    DOMAIN = "domain"
    DOCUMENT = "document"
    VULNERABILITY = "vulnerability"

class GoogleDorkRequest(BaseModel):
    """Request model for a basic Google Dorking search."""
    query: str = Field(..., min_length=2, max_length=500)
    search_type: SearchType = SearchType.PERSON
    max_results: int = Field(default=50, ge=10, le=200)

# ============================================================================
# Google Dorking Logic
# ============================================================================

class GoogleDorker:
    """A class to handle the execution of Google searches, including rate
    limiting and parsing of results.
    """
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Initializes and returns an aiohttp client session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self.session

    async def search_google(self, query: str, max_results: int) -> Dict[str, Any]:
        """Executes a search on Google and parses the results.

        Args:
            query (str): The search query string (dork).
            max_results (int): The maximum number of results to return.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed search results.
        """
        session = await self.get_session()
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={max_results}"
        headers = {'User-Agent': random.choice(["Mozilla/5.0", "AppleWebKit/537.36"])}
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return {"error": f"HTTP status {response.status}"}
                html = await response.text()
                return self._parse_results(html, query)
        except Exception as e:
            return {"error": str(e)}

    def _parse_results(self, html: str, query: str) -> Dict[str, Any]:
        """Parses the HTML response from Google to extract search results."""
        # Simplified parsing logic for demonstration.
        links = re.findall(r'<a href="/url\?q=([^&]+)", html)
        results = [{
            "url": urllib.parse.unquote(link),
            "title": f"Result for {query}",
            "snippet": "..."
        } for link in links]
        return {"query": query, "results": results}

    async def close_session(self):
        """Closes the aiohttp client session."""
        if self.session: await self.session.close()

google_dorker = GoogleDorker()

# ============================================================================
# API Endpoints
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Handles graceful shutdown of the service."""
    await google_dorker.close_session()

@app.get("/", tags=["Health"])
async def health_check():
    """Provides a basic health check of the service."""
    return {"service": "Google OSINT Service", "status": "operational"}

@app.post("/api/search/basic", tags=["Search"])
async def basic_google_search(request: GoogleDorkRequest):
    """Performs a basic Google Dorking search based on a query and search type.

    Args:
        request (GoogleDorkRequest): The search request details.

    Returns:
        Dict[str, Any]: The search results.
    """
    dork_patterns = {
        SearchType.PERSON: ['"{query}" site:linkedin.com', '"{query}" cv filetype:pdf'],
        SearchType.EMAIL: ['intext:"{query}"', 'filetype:xls intext:"{query}"'],
        SearchType.DOMAIN: ['site:{query}', 'inurl:{query}'],
        SearchType.DOCUMENT: ['"{query}" filetype:pdf'],
        SearchType.VULNERABILITY: ['site:{query} intitle:"index of"'],
    }
    
    queries = [p.format(query=request.query) for p in dork_patterns.get(request.search_type, [request.query])]
    
    all_results = []
    for q in queries:
        res = await google_dorker.search_google(q, request.max_results // len(queries))
        if not res.get("error"): all_results.extend(res.get("results", []))
        await asyncio.sleep(random.uniform(2, 5)) # Rate limit

    # Remove duplicates
    unique_results = {r['url']: r for r in all_results}.values()
    
    return {
        "status": "success",
        "data": {
            "query": request.query,
            "results": list(unique_results)[:request.max_results]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)

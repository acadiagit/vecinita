"""Web search tool for Vecinita agent.

Provides web search via Tavily when available and falls back to DuckDuckGo
otherwise. Use when the internal database doesn't have relevant info or for
external, up-to-date sources.
"""

import logging
import os
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def web_search_tool(query: str) -> List[Dict[str, Any]]:
    """Search the web for information using Tavily or DuckDuckGo.

    Args:
        query: The search query to find information on the web.

    Returns:
        A list of result dicts with 'title', 'content'/'snippet', and 'url'.
    """
    # Placeholder; real implementation provided by create_web_search_tool
    raise NotImplementedError(
        "This tool must be created via create_web_search_tool() to configure "
        "the provider (Tavily or DuckDuckGo)."
    )


def create_web_search_tool() -> tool:
    """Create a configured web_search tool using Tavily or DuckDuckGo.

    Prefers Tavily when `TAVILY_API_KEY` (or `TVLY_API_KEY`) is set; otherwise
    falls back to DuckDuckGo. Results are normalized into a list of dicts with
    keys: 'title', 'content' (or 'snippet'), and 'url'.
    """
    # Support multiple env var names to avoid setup friction
    tavily_key = (
        os.getenv("TAVILY_API_KEY")
        or os.getenv("TAVILY_API_AI_KEY")
        or os.getenv("TVLY_API_KEY")
    )
    use_tavily = bool(tavily_key)

    tavily = None
    ddg = None

    if use_tavily:
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
            tavily = TavilySearchResults(
                max_results=5,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=False,
                api_key=tavily_key,
            )
            logger.info("Web search initialized with Tavily API")
        except Exception as e:
            logger.warning(
                f"Failed to initialize Tavily, falling back to DuckDuckGo: {e}")
            use_tavily = False

    if not use_tavily:
        try:
            from langchain_community.tools import DuckDuckGoSearchResults
            ddg = DuckDuckGoSearchResults(num_results=5)
            logger.info("Web search initialized with DuckDuckGo")
        except Exception as e:
            logger.error(f"Failed to initialize DuckDuckGo search: {e}")

    @tool
    def web_search(query: str) -> List[Dict[str, Any]]:
        """Search the web for information.

        Args:
            query: The search query

        Returns:
            List of normalized results with 'title', 'content'/'snippet', 'url'.
        """
        try:
            if use_tavily and tavily is not None:
                logger.info(f"Web search (Tavily): {query}")
                results = tavily.invoke({"query": query})
                normalized: List[Dict[str, Any]] = []
                for r in results or []:
                    normalized.append({
                        "title": r.get("title") or "",
                        "content": r.get("content") or r.get("answer") or "",
                        "url": r.get("url") or r.get("source") or "",
                    })
                return normalized

            # DuckDuckGo fallback
            if ddg is not None:
                logger.info(f"Web search (DuckDuckGo): {query}")
                results = ddg.invoke(query)
                normalized: List[Dict[str, Any]] = []
                if isinstance(results, list):
                    for r in results:
                        normalized.append({
                            "title": r.get("title") or "",
                            "content": r.get("snippet") or "",
                            "url": r.get("link") or "",
                        })
                elif isinstance(results, str) and results:
                    normalized.append({
                        "title": "DuckDuckGo Result",
                        "content": results,
                        "url": "",
                    })
                return normalized

            logger.error("No web search provider available")
            return []
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []

    return web_search

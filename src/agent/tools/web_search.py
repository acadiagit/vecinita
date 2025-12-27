"""Web search tool for Vecinita agent.

This tool performs external web scraping to retrieve content from URLs
when the internal database doesn't have sufficient information.
"""

import logging
from typing import Optional, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def web_search_tool(url: str) -> Optional[Dict[str, Any]]:
    """Search external web sources for information.

    Use this tool as a FALLBACK when the database search doesn't return
    relevant results. It scrapes and cleans content from a specified URL.

    IMPORTANT: This tool requires a specific URL to scrape. If you need to
    search for information but don't have a URL, you should use the database
    search tool instead.

    Args:
        url: The URL to scrape and extract content from

    Returns:
        A dictionary with 'content' and 'source_url' if successful,
        or None if scraping fails.

    Example:
        >>> result = web_search_tool("https://example.com/community-services")
        >>> if result:
        ...     print(f"Content: {result['content']}")
        ...     print(f"Source: {result['source_url']}")
    """
    # This will be implemented with actual scraper integration
    # For now, this is a placeholder that will be properly configured in main.py
    raise NotImplementedError(
        "This tool must be configured with scraper components. "
        "Use create_web_search_tool() to create a properly configured instance."
    )


def create_web_search_tool(scraper_config: Optional[Dict[str, Any]] = None):
    """Create a configured web_search tool with access to scraper utilities.

    Args:
        scraper_config: Optional configuration for the web scraper
                       (rate limits, user agents, etc.)

    Returns:
        A configured tool function that can be used with LangGraph
    """
    # Import scraper utilities (avoid circular imports)
    try:
        from ..utils.html_cleaner import clean_html
        from ..utils.scraper_to_text import scrape_url_content
    except ImportError:
        logger.warning(
            "Scraper utilities not available. Web search tool will be limited.")
        clean_html = None
        scrape_url_content = None

    @tool
    def web_search(url: str) -> Optional[Dict[str, Any]]:
        """Search external web sources for information.

        Use this tool as a FALLBACK when the database search doesn't return
        relevant results. It scrapes and cleans content from a specified URL.

        Args:
            url: The URL to scrape and extract content from

        Returns:
            A dictionary with 'content' and 'source_url' if successful,
            or None if scraping fails.
        """
        try:
            logger.info(f"Web Search: Scraping content from URL: {url}")

            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                logger.error(f"Web Search: Invalid URL format: {url}")
                return None

            # For now, return a placeholder since we need to properly integrate
            # the scraper utilities which may require async operations
            logger.warning(
                "Web Search: Full scraper integration pending. Returning placeholder.")

            return {
                'content': f"Web scraping for {url} is not yet fully implemented. "
                "Please use the database search tool for now.",
                'source_url': url,
                'scraped': False
            }

            # TODO: Implement full scraping logic
            # if scrape_url_content:
            #     raw_content = scrape_url_content(url)
            #     if raw_content and clean_html:
            #         cleaned_content = clean_html(raw_content)
            #         return {
            #             'content': cleaned_content,
            #             'source_url': url,
            #             'scraped': True
            #         }
            # return None

        except Exception as e:
            logger.error(f"Web Search: Error scraping URL {url}: {e}")
            return None

    return web_search

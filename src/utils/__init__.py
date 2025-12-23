"""
Compatibility package to support imports like `src.utils.scraper.*`.
Modules here forward to the canonical implementations under `src.scraper`.
"""

__all__ = [
    "scraper",
]

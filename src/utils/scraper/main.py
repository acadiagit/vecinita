from ...scraper.main import *  # noqa: F401,F403

# Ensure tests can patch `src.utils.scraper.main.VecinaScraper`
try:
    from ...scraper.scraper import VecinaScraper  # type: ignore
except Exception:
    # Fallback: leave attribute undefined if import fails
    pass
# Ensure VecinaScraper symbol exists here for tests to patch
try:  # pragma: no cover
    from ...scraper.scraper import VecinaScraper as VecinaScraper  # type: ignore
except Exception:  # pragma: no cover
    VecinaScraper = None  # type: ignore

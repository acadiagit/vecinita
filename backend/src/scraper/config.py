"""
Configuration management for the VECINA scraper.
Loads and manages site categorization and scraper settings.
"""

import os
import logging
from typing import Dict, List
from pathlib import Path

log = logging.getLogger(__name__)


class ScraperConfig:
    """Manages all scraper configuration."""

    # Try to find config dir relative to repo root
    # When running from backend/, look in ../data/config
    # When running from repo root, look in data/config
    _potential_config_dirs = [
        Path("data/config"),  # From repo root
        Path("../data/config"),  # From backend/
        Path(__file__).parent.parent.parent.parent /
        "data" / "config",  # Absolute from module
    ]

    CONFIG_DIR = None
    for _dir in _potential_config_dirs:
        if _dir.exists():
            CONFIG_DIR = str(_dir)
            break

    if CONFIG_DIR is None:
        CONFIG_DIR = "data/config"  # Fallback

    RECURSIVE_SITES_FILE = os.path.join(CONFIG_DIR, "recursive_sites.txt")
    PLAYWRIGHT_SITES_FILE = os.path.join(CONFIG_DIR, "playwright_sites.txt")
    SKIP_SITES_FILE = os.path.join(CONFIG_DIR, "skip_sites.txt")
    DATA_DIR = "data/"

    # Scraper settings
    RATE_LIMIT_DELAY = 2  # seconds
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    def __init__(self):
        """Initialize configuration by loading all site lists."""
        self.sites_to_crawl: Dict[str, Dict[str, int]] = {}
        self.sites_needing_playwright: List[str] = []
        self.sites_to_skip: List[str] = []
        self.load_all_configs()

    def load_all_configs(self) -> None:
        """Load all configuration files."""
        self.sites_to_crawl = self._load_recursive_config(
            self.RECURSIVE_SITES_FILE)
        self.sites_needing_playwright = self._load_config_list(
            self.PLAYWRIGHT_SITES_FILE)
        self.sites_to_skip = self._load_config_list(self.SKIP_SITES_FILE)

        log.info(
            f"Loaded {len(self.sites_to_crawl)} recursive sites, "
            f"{len(self.sites_needing_playwright)} playwright sites, "
            f"{len(self.sites_to_skip)} skip sites."
        )

    @staticmethod
    def _load_config_list(file_path: str) -> List[str]:
        """Load a simple list of domains/keywords from a .txt file."""
        if not os.path.exists(file_path):
            log.warning(
                f"Config file not found: {file_path}. List will be empty.")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            log.error(f"Failed to read config file {file_path}: {e}")
            return []

    @staticmethod
    def _load_recursive_config(file_path: str) -> Dict[str, Dict[str, int]]:
        """Load recursive site config (e.g., "https://example.com/ 2")."""
        config = {}
        if not os.path.exists(file_path):
            log.warning(
                f"Config file not found: {file_path}. Recursive crawl list will be empty.")
            return config

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            url_prefix = parts[0]
                            try:
                                depth = int(parts[1])
                                config[url_prefix] = {"max_depth": depth}
                            except ValueError:
                                log.error(
                                    f"Invalid depth '{parts[1]}' for site '{url_prefix}'. Skipping.")
                        elif len(parts) == 1:
                            config[parts[0]] = {"max_depth": 1}
            return config
        except Exception as e:
            log.error(f"Failed to read recursive config file {file_path}: {e}")
            return {}

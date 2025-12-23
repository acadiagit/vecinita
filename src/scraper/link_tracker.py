"""
Link tracking for the VECINA scraper.
Extracts and saves URLs and metadata from scraped content.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

log = logging.getLogger(__name__)


class LinkTracker:
    """Tracks and saves extracted links and metadata."""

    def __init__(self, output_file: Optional[str] = None):
        """Initialize with optional output file."""
        self.output_file = output_file
        self.links: Dict[str, List[str]] = {}

    def add_links(self, source_url: str, links: List[str], loader_type: str = "Unknown") -> None:
        """
        Add links from a source.

        Args:
            source_url: The URL that was scraped
            links: List of links found
            loader_type: The type of loader used
        """
        if source_url not in self.links:
            self.links[source_url] = links
        else:
            self.links[source_url].extend(links)

        log.info(f"--> Tracked {len(links)} links from {source_url}")

    def save_links(self) -> None:
        """Save all tracked links to file."""
        if not self.output_file or not self.links:
            return

        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"LINK EXTRACTION SUMMARY\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"{'='*70}\n\n")

                for source, links in self.links.items():
                    f.write(f"Source: {source}\n")
                    f.write(f"Links found: {len(set(links))}\n")
                    f.write("-" * 70 + "\n")

                    for link in sorted(set(links)):  # Deduplicate and sort
                        f.write(f"  • {link}\n")

                    f.write("\n")

            log.info(
                f"--> ✅ Saved {sum(len(v) for v in self.links.values())} links to {self.output_file}")
        except Exception as e:
            log.error(f"--> ❌ Failed to save links: {e}")

    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics."""
        return {
            "total_sources": len(self.links),
            "total_links": sum(len(v) for v in self.links.values()),
            "unique_links": sum(len(set(v)) for v in self.links.values())
        }

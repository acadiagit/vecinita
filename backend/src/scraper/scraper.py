"""
Main scraper orchestration for the VECINA project.
Coordinates all scraping components: config, loaders, processors, and link tracking.
"""

import logging
import time
from typing import Dict, List, Tuple, Optional
from .config import ScraperConfig
from .loaders import SmartLoader
from .processors import DocumentProcessor
from .link_tracker import LinkTracker
from .utils import write_to_failed_log
from .uploader import DatabaseUploader

# Use the vecinita_pipeline logger from the parent CLI if available
log = logging.getLogger('vecinita_pipeline.scraper')
# Fall back to module logger if not already configured
log.addHandler(logging.NullHandler())


class VecinaScraper:
    """Main scraper orchestrator."""

    def __init__(
        self,
        output_file: str,
        failed_log: str,
        links_file: Optional[str] = None,
        stream_mode: bool = False
    ):
        """
        Initialize the scraper.

        Args:
            output_file: Path to output chunks file
            failed_log: Path to failed URLs log file
            links_file: Optional path to save extracted links
            stream_mode: If True, upload chunks immediately to database (streaming mode)
        """
        log.debug(f"Initializing VecinaScraper with output_file={output_file}")
        log.debug(f"  failed_log={failed_log}")
        log.debug(f"  links_file={links_file}")
        log.debug(f"  stream_mode={stream_mode}")

        self.config = ScraperConfig()
        log.debug(
            f"ScraperConfig loaded: rate_limit={self.config.RATE_LIMIT_DELAY}s")

        self.loader = SmartLoader(self.config)
        log.debug("SmartLoader initialized")

        self.processor = DocumentProcessor(self.config)
        log.debug(
            f"DocumentProcessor initialized: chunk_size={self.config.CHUNK_SIZE}, overlap={self.config.CHUNK_OVERLAP}")

        self.link_tracker = LinkTracker(links_file)
        log.debug(f"LinkTracker initialized")

        self.output_file = output_file
        self.failed_log = failed_log
        self.links_file = links_file
        self.stream_mode = stream_mode
        self.uploader = None

        self.successful_sources: List[str] = []
        self.failed_sources: Dict[str, str] = {}
        self.stats = {
            "total_urls": 0,
            "successful": 0,
            "failed": 0,
            "total_chunks": 0,
            "total_links": 0,
            "total_uploads": 0,
            "failed_uploads": 0
        }

        if self.stream_mode:
            log.info(
                "Streaming mode enabled: chunks will be uploaded immediately to database")
            try:
                self.uploader = DatabaseUploader(use_local_embeddings=True)
                log.info("✓ Database uploader initialized")
            except Exception as e:
                log.error(f"Failed to initialize database uploader: {e}")
                log.warning(
                    "Streaming mode disabled. Falling back to file mode.")
                self.stream_mode = False
        else:
            log.info(
                f"Traditional mode: chunks will be written to {output_file}")

        log.info(f"VecinaScraper initialization complete")

    def scrape_urls(
        self,
        urls: List[str],
        force_loader: Optional[str] = None
    ) -> Tuple[int, int, int]:
        """
        Scrape a list of URLs.

        Args:
            urls: List of URLs to scrape
            force_loader: Optional loader type to force ('playwright', 'recursive', 'unstructured')

        Returns:
            Tuple of (total_urls, successful, failed)
        """
        log.info(f"\n{'='*70}")
        log.info(f"Starting to scrape {len(urls)} URLs...")
        if force_loader:
            log.info(f"Forcing loader type: {force_loader}")
        log.info(f"{'='*70}")

        self.stats["total_urls"] = len(urls)
        start_time = time.time()

        for idx, url in enumerate(urls, 1):
            log.debug(f"Processing URL {idx}/{len(urls)}: {url}")
            self._process_single_url(url, force_loader)
            # Rate limiting after each URL
            time.sleep(self.config.RATE_LIMIT_DELAY)

        elapsed = time.time() - start_time
        log.info(f"Scraping completed in {elapsed:.2f} seconds")
        return self.stats["total_urls"], self.stats["successful"], self.stats["failed"]

    def _process_single_url(self, url: str, force_loader: Optional[str] = None) -> None:
        """Process a single URL with detailed logging."""
        log.debug(f"[Loading] Attempting to load: {url}")

        # Load the URL
        try:
            docs, loader_type, success = self.loader.load_url(
                url, self.failed_log, force_loader)
            log.debug(
                f"[Load Result] Loader type: {loader_type}, Success: {success}, Docs: {len(docs) if docs else 0}")
        except Exception as e:
            log.error(f"[Load Error] Exception loading {url}: {e}")
            self.stats["failed"] += 1
            self.failed_sources[url] = f"Loading exception: {str(e)}"
            return

        if not success or not docs:
            log.warning(
                f"[Load Failed] Could not load {url} (loader: {loader_type})")
            self.stats["failed"] += 1
            self.failed_sources[url] = f"Failed to load ({loader_type})"
            return

        # Process documents
        try:
            log.debug(
                f"[Processing] Processing {len(docs)} document(s) from {url}")

            chunks_written, extracted_links = self.processor.process_documents(
                docs=docs,
                source_identifier=url,
                loader_type=loader_type,
                output_file=self.output_file,
                links_file=self.links_file
            )

            log.debug(
                f"[Processing Result] Chunks written: {chunks_written}, Links extracted: {len(extracted_links) if extracted_links else 0}")

            if chunks_written > 0:
                self.successful_sources.append(url)
                self.stats["successful"] += 1
                self.stats["total_chunks"] += chunks_written

                # Upload to database if streaming mode
                if self.stream_mode and self.uploader and getattr(self.processor, 'last_chunks', None):
                    log.debug(
                        f"[Upload] Uploading {len(self.processor.last_chunks)} chunks to database...")
                    try:
                        uploaded, failed = self.uploader.upload_chunks(
                            chunks=self.processor.last_chunks,
                            source_identifier=url,
                            loader_type=loader_type
                        )
                        self.stats["total_uploads"] += uploaded
                        self.stats["failed_uploads"] += failed
                        log.debug(
                            f"[Upload Result] {uploaded} uploaded, {failed} failed")
                    except Exception as upload_err:
                        log.error(
                            f"[Upload Error] Failed to upload chunks: {upload_err}")
                        self.stats["failed_uploads"] += len(
                            self.processor.last_chunks)

                # Track links
                if extracted_links:
                    self.link_tracker.add_links(
                        url, extracted_links, loader_type)
                    self.stats["total_links"] += len(extracted_links)
                    log.debug(
                        f"[Links] Tracked {len(extracted_links)} links from {url}")

                log.info(
                    f"SUCCESS: {url} ({chunks_written} chunks, {len(extracted_links) if extracted_links else 0} links)")
            else:
                # Fallback: try Playwright if not already used
                if 'Playwright' not in loader_type:
                    log.info(
                        f"[Processing] No usable chunks. Retrying {url} with Playwright fallback...")
                    try:
                        pw_docs, pw_loader, pw_success = self.loader.load_url(
                            url, self.failed_log, force_loader='playwright')
                        if pw_success and pw_docs:
                            log.info(
                                f"[Fallback] Playwright returned {len(pw_docs)} document(s). Re-processing...")
                            chunks_written, extracted_links = self.processor.process_documents(
                                docs=pw_docs,
                                source_identifier=url,
                                loader_type=pw_loader,
                                output_file=self.output_file,
                                links_file=self.links_file
                            )
                            if chunks_written > 0:
                                self.successful_sources.append(url)
                                self.stats["successful"] += 1
                                self.stats["total_chunks"] += chunks_written
                                if self.stream_mode and self.uploader and getattr(self.processor, 'last_chunks', None):
                                    log.debug(
                                        f"[Upload] Uploading {len(self.processor.last_chunks)} chunks to database...")
                                    try:
                                        uploaded, failed = self.uploader.upload_chunks(
                                            chunks=self.processor.last_chunks,
                                            source_identifier=url,
                                            loader_type=pw_loader
                                        )
                                        self.stats["total_uploads"] += uploaded
                                        self.stats["failed_uploads"] += failed
                                        log.debug(
                                            f"[Upload Result] {uploaded} uploaded, {failed} failed")
                                    except Exception as upload_err:
                                        log.error(
                                            f"[Upload Error] Failed to upload chunks: {upload_err}")
                                        self.stats["failed_uploads"] += len(
                                            self.processor.last_chunks)
                                if extracted_links:
                                    self.link_tracker.add_links(
                                        url, extracted_links, pw_loader)
                                    self.stats["total_links"] += len(
                                        extracted_links)
                                    log.debug(
                                        f"[Links] Tracked {len(extracted_links)} links from {url}")
                                log.info(
                                    f"SUCCESS (fallback): {url} ({chunks_written} chunks, {len(extracted_links) if extracted_links else 0} links)")
                                return
                        # If fallback didn't help, mark as failed
                        log.warning(
                            f"[Processing] No usable chunks generated from {url} after Playwright fallback")
                        self.stats["failed"] += 1
                        self.failed_sources[
                            url] = "No usable chunks after processing (with Playwright fallback)"
                        return
                    except Exception as e_fallback:
                        log.error(
                            f"[Fallback Error] Playwright attempt failed for {url}: {e_fallback}")
                        self.stats["failed"] += 1
                        self.failed_sources[
                            url] = f"No usable chunks; Playwright fallback error: {e_fallback}"
                        return
                else:
                    log.warning(
                        f"[Processing] No usable chunks generated from {url}")
                    self.stats["failed"] += 1
                    self.failed_sources[url] = "No usable chunks after processing"

        except Exception as e:
            log.error(f"[Processing Error] Exception processing {url}: {e}")
            log.debug(f"Full exception:", exc_info=True)
            self.stats["failed"] += 1
            self.failed_sources[url] = f"Processing error: {str(e)}"

    def print_summary(self) -> None:
        """Print a summary of scraping results."""
        log.info("\n" + "="*70)
        log.info("SCRAPING SUMMARY")
        log.info("="*70)
        log.info(f"Total URLs processed: {self.stats['total_urls']}")
        log.info(f"Successful: {self.stats['successful']}")
        log.info(f"Failed: {self.stats['failed']}")
        log.info(f"Total chunks generated: {self.stats['total_chunks']}")
        log.info(f"Total links tracked: {self.stats['total_links']}")

        if self.stream_mode:
            log.info(
                f"Chunks uploaded to database: {self.stats['total_uploads']}")
            if self.stats['failed_uploads'] > 0:
                log.warning(f"Failed uploads: {self.stats['failed_uploads']}")

        log.info("="*70)

        if self.successful_sources:
            log.info("\nSuccessfully processed sources:")
            for url in self.successful_sources:
                log.info(f"  - {url}")

        if self.failed_sources:
            log.info(
                f"\nFailed/Skipped sources ({len(self.failed_sources)}):")
            for url, reason in self.failed_sources.items():
                reason_short = (
                    reason[:80] + '...') if len(reason) > 80 else reason
                log.info(f"  - {url}")
                log.info(f"    Reason: {reason_short}")

        log.info("="*70)

    def finalize(self) -> None:
        """Finalize scraping (save links, close connections, etc.)."""
        if self.links_file:
            self.link_tracker.save_links()
        if self.uploader:
            self.uploader.close()
        log.info("\nScraping pipeline complete!")

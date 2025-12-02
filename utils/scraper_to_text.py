#!/usr/bin/env python3
# utils/scraper_to_text.py
#
# Data-driven scraper for the VECINA project.
# This script is designed to be called by the 'load_data.sh' orchestrator.
#
# It reads all configurations (sites to skip, scrape, etc.) from files
# in the 'data/config/' directory.
#
# It accepts:
#   --input <file>        : The file of URLs to process (e.g., data/urls.txt)
#   --output-file <file>  : The file to *append* chunked content to.
#   --failed-log <file>   : The file to *append* failed URLs to.
#   --loader [name]       : (Optional) Force a specific loader for all URLs.
#

import os
import time
import argparse
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, UnstructuredURLLoader,
    PlaywrightURLLoader, CSVLoader
)
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import requests
import logging

# --- Configuration ---
CONFIG_DIR = "data/config"
RECURSIVE_SITES_FILE = os.path.join(CONFIG_DIR, "recursive_sites.txt")
PLAYWRIGHT_SITES_FILE = os.path.join(CONFIG_DIR, "playwright_sites.txt")
SKIP_SITES_FILE = os.path.join(CONFIG_DIR, "skip_sites.txt")
DATA_DIR = "data/" # For processing local files

# Delay between web requests to avoid overwhelming servers
RATE_LIMIT_DELAY = 2  # seconds

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Global Config Lists (will be populated at startup) ---
SITES_TO_CRAWL = {}
SITES_NEEDING_PLAYWRIGHT = []
SITES_TO_SKIP = []

# --- Helper Functions ---

def load_config_list(file_path):
    """Loads a simple list of domains/keywords from a .txt file."""
    if not os.path.exists(file_path):
        log.warning(f"Config file not found: {file_path}. List will be empty.")
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        log.error(f"Failed to read config file {file_path}: {e}")
        return []

def load_recursive_config(file_path):
    """Loads the recursive site config (e.g., "https://example.com/ 2")."""
    config = {}
    if not os.path.exists(file_path):
        log.warning(f"Config file not found: {file_path}. Recursive crawl list will be empty.")
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
                            log.error(f"Invalid depth '{parts[1]}' for site '{url_prefix}' in {file_path}. Skipping.")
                    elif len(parts) == 1:
                         # Default to depth 1 if not specified
                         config[parts[0]] = {"max_depth": 1}
        return config
    except Exception as e:
        log.error(f"Failed to read recursive config file {file_path}: {e}")
        return {}


def convert_github_to_raw(url):
    """Converts GitHub 'blob' URLs to 'raw' URLs for direct content access."""
    if "github.com" in url and "/blob/" in url:
        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        log.info(f"--> Converted GitHub URL to raw: {raw_url}")
        return raw_url
    return url

def should_skip_url(url):
    """Checks if a URL matches any pattern in the SITES_TO_SKIP list."""
    for skip_pattern in SITES_TO_SKIP:
        if skip_pattern in url:
            log.warning(f"--> ⚠️ Skipping {url} (matches skip pattern: '{skip_pattern}')")
            return True
    return False

def needs_playwright(url):
    """Checks if a URL matches any pattern needing Playwright."""
    return any(pattern in url for pattern in SITES_NEEDING_PLAYWRIGHT)

def is_csv_file(url):
    """Checks if a URL likely points to a CSV file."""
    if url.lower().endswith('.csv'):
        return True
    if "github.com" in url and "/blob/" in url and '.csv' in url.lower():
        return True
    return False

def get_crawl_config(url):
    """Checks if the given URL starts with any of the base URLs for recursive crawling."""
    for site_prefix, config in SITES_TO_CRAWL.items():
        if url.startswith(site_prefix):
            return config
    return None

def write_to_failed_log(url, reason, log_file):
    """Appends a failed URL and its reason to the specified log file."""
    if not log_file:
        return # Do nothing if no log file is specified
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{url}\n") # Write the URL on its own line
    except Exception as e:
        log.error(f"Failed to write to failed-log {log_file}: {e}")

def download_file(url, save_path):
    """Downloads a file from a URL to a specified local path."""
    try:
        log.info(f"--> Downloading file from {url}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (VECINA Project - Community Resource Scraper; +https://vecina.wrwc.org/)"
        }
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        log.info(f"--> ✅ File saved to {save_path}")
        return True
    except requests.exceptions.RequestException as e:
        log.error(f"--> ❌ Failed to download file (Request Error): {e}")
        return False
    except Exception as e:
        log.error(f"--> ❌ Failed to download file (Other Error): {e}")
        return False


def clean_text(text):
    """Cleans scraped text content."""
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    noise_patterns = [
        r'cookie\s+policy', r'privacy\s+policy', r'terms\s+of\s+service',
        r'terms\s+&\s+conditions', r'©\s*(\d{4})?', r'all\s+rights\s+reserved',
        r'site\s+map', r'contact\s+us', r'log\s*in', r'sign\s*up',
        r'register', r'search(\s+site)?', r'skip\s+to\s+(main\s+)?content',
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Keep lines with more than 3 words to avoid menu fragments
    lines = text.split('\n')
    cleaned_lines = [line for line in lines if len(line.split()) > 3]
    text = '\n'.join(cleaned_lines)

    return text.strip()

# --- Main Processing Functions ---

def process_documents(docs, source_identifier, loader_type, output_file=None):
    """Chunks documents and appends them to the specified output file."""
    start_time = time.time()

    if not docs:
        log.warning("--> No documents found to process. Skipping.")
        return 0

    cleaned_docs_content = []
    log.info("--> Cleaning document content...")
    if "Loader" in loader_type or "Crawler" in loader_type:
        bs_transformer = BeautifulSoupTransformer()
        try:
            docs = bs_transformer.transform_documents(
                docs,
                tags_to_extract=["main", "article", "section", "p", "h1", "h2", "h3", "h4", "li", "td", "th", "pre"]
            )
        except Exception as e:
            log.warning(f"--> ⚠️ BeautifulSoup cleaning failed: {e}. Using raw content.")

    for doc in docs:
        cleaned_content = clean_text(doc.page_content)
        if cleaned_content:
            cleaned_docs_content.append((cleaned_content, doc.metadata))

    if not cleaned_docs_content:
        log.warning("--> No content found after cleaning. Skipping.")
        return 0

    preview_text = cleaned_docs_content[0][0][:200].replace('\n', ' ') + '...'
    log.info(f"--> PREVIEW (after cleaning): {preview_text}")

    log.info("--> Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""],
        keep_separator=False
    )

    chunks_for_file = []
    total_chunks_generated = 0
    for content, metadata in cleaned_docs_content:
        split_chunks = text_splitter.split_text(content)
        total_chunks_generated += len(split_chunks)
        for chunk_text in split_chunks:
            chunks_for_file.append({'text': chunk_text, 'metadata': metadata})

    log.info(f"--> Created {total_chunks_generated} chunks from {len(cleaned_docs_content)} processed documents.")

    if output_file and chunks_for_file:
        log.info(f"--> Appending {total_chunks_generated} chunks to {output_file}...")
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{'='*70}\n")
                f.write(f"SOURCE: {source_identifier}\n")
                f.write(f"LOADER: {loader_type}\n")
                f.write(f"DOCUMENTS_LOADED: {len(docs)} | DOCUMENTS_PROCESSED: {len(cleaned_docs_content)} | CHUNKS: {total_chunks_generated}\n")
                f.write(f"{'='*70}\n\n")
                for i, chunk_data in enumerate(chunks_for_file):
                    f.write(f"--- CHUNK {i+1}/{total_chunks_generated} ---\n")
                    f.write(chunk_data['text'])
                    chunk_source = chunk_data['metadata'].get('source', source_identifier)
                    if chunk_source != source_identifier:
                         f.write(f"\n(Chunk Source: {chunk_source})")
                    f.write("\n\n")
        except Exception as e:
            log.error(f"--> ❌ Error writing to output file {output_file}: {e}")
    elif not chunks_for_file:
        log.warning("--> No chunks generated after splitting. Nothing written to file.")

    elapsed = time.time() - start_time
    log.info(f"--> ✅ Document processing complete in {elapsed:.2f} seconds.")
    return total_chunks_generated


def load_url(url, output_file=None, failed_log=None, force_loader=None):
    """Loads content from a single URL using the most appropriate method."""
    log.info(f"\n{'='*70}")
    log.info(f"Processing URL: {url}")
    log.info(f"{'='*70}")

    if should_skip_url(url):
        write_to_failed_log(url, "Skipped (Matches SITES_TO_SKIP pattern)", failed_log)
        return False # Return failure

    docs = []
    loader_type = "Unknown"
    load_success = False
    error_reason = "Unknown error"

    try:
        start_load_time = time.time()
        
        # --- Smart Loader Routing ---
        
        # 1. Check for Forced Loader
        if force_loader:
            log.warning(f"--> Loader forced by flag: {force_loader}")
            if force_loader == 'playwright':
                loader_type = "Playwright (FORCED)"
            elif force_loader == 'recursive':
                loader_type = "Recursive Crawler (FORCED)"
            else:
                loader_type = "Unstructured (FORCED)"
        
        # 2. GitHub CSV
        elif is_csv_file(url):
            url = convert_github_to_raw(url)
            loader_type = "CSV File"
            log.info(f"--> Detected {loader_type}. Downloading...")
            temp_csv_name = f"temp_{os.path.basename(urlparse(url).path)}_{int(time.time())}.csv"
            temp_csv_path = os.path.join(DATA_DIR, temp_csv_name)
            if download_file(url, temp_csv_path):
                try:
                    loader = CSVLoader(file_path=temp_csv_path, encoding='utf-8')
                    docs = loader.load()
                    load_success = True
                except Exception as e:
                    error_reason = f"CSV parsing failed: {e}"
                finally:
                    if os.path.exists(temp_csv_path): os.remove(temp_csv_path)
            else:
                 error_reason = "CSV download failed."

        # 3. Recursive Crawl
        crawl_config = get_crawl_config(url)
        if force_loader == 'recursive' or (not force_loader and crawl_config):
            config = crawl_config or {"max_depth": 1} # Default depth 1 if forced
            loader_type = f"Recursive Crawler (Depth: {config['max_depth']})"
            log.info(f"--> Using {loader_type}")
            try:
                loader = RecursiveUrlLoader(
                    url=url, max_depth=config['max_depth'],
                    extractor=lambda x: BeautifulSoup(x, "html.parser").get_text(separator=" ", strip=True),
                    prevent_outside=True, timeout=30,
                    headers={"User-Agent": "Mozilla/5.0 (VECINA Project - Community Resource Scraper)"}
                )
                docs = loader.load()
                load_success = True
            except Exception as e:
                error_reason = f"Recursive crawl failed: {e}"

        # 4. Playwright
        elif force_loader == 'playwright' or (not force_loader and needs_playwright(url)):
            loader_type = "Playwright (JavaScript rendering)"
            log.info(f"--> Using {loader_type}")
            try:
                loader = PlaywrightURLLoader(
                    urls=[url],
                    remove_selectors=["header", "footer", "nav", "script", "style", ".cookie-banner", "#cookie-notice", "aside", "figure", "figcaption"],
                )
                docs = loader.load()
                load_success = True
            except Exception as e:
                 error_reason = f"Playwright loading failed: {e}"

        # 5. Standard URL (Default)
        else:
            loader_type = "Unstructured URL Loader"
            log.info(f"--> Using {loader_type}")
            try:
                headers = {"User-Agent": "Mozilla/5.0 (VECINA Project - Community Resource Scraper)"}
                loader = UnstructuredURLLoader(urls=[url], headers=headers, ssl_verify=True, mode="elements")
                docs = loader.load()
                load_success = True
            except Exception as e:
                error_reason = f"Unstructured loading failed: {e}"

        # --- Process Documents ---
        end_load_time = time.time()
        loading_duration = end_load_time - start_load_time

        if load_success:
            log.info(f"--> ✅ Loading complete. Found {len(docs)} documents in {loading_duration:.2f} seconds.")
            if docs:
                chunks_written = process_documents(docs, url, loader_type, output_file=output_file)
                if chunks_written > 0:
                    log.info(f"--> Successfully wrote {chunks_written} chunks for {url}")
                    return True # Success
                else:
                    error_reason = "Processing resulted in zero usable chunks after cleaning/splitting."
            else:
                error_reason = f"Loader ({loader_type}) returned zero documents."
        
        # If we are here, it's a failure (either load failed or processing failed)
        log.warning(f"--> ❌ Failed to process {url}. Reason: {error_reason}")
        write_to_failed_log(url, error_reason, failed_log)
        return False # Failure

    except Exception as e:
        log.error(f"--> ❌ Unexpected error processing {url}: {e}")
        write_to_failed_log(url, f"Unexpected error: {e}", failed_log)
        return False # Failure
    finally:
        # Rate limiting - apply after every URL attempt
        log.info(f"--> Applying rate limit delay ({RATE_LIMIT_DELAY}s)...")
        time.sleep(RATE_LIMIT_DELAY)


def print_summary(successful_urls, failed_urls):
    """Prints a summary of successful and failed URL processing."""
    log.info("\n" + "="*70)
    log.info("📊 SCRAPING SUMMARY")
    log.info("="*70)
    log.info(f"✅ Successful sources processed (generated chunks): {len(successful_urls)}")
    for url in successful_urls:
        log.info(f"  - {url}")
    log.info(f"\n❌ Failed/Skipped sources: {len(failed_urls)}")
    if failed_urls:
        log.info("--- Failure/Skip Details ---")
        for url, reason in failed_urls.items():
            reason_short = (reason[:120] + '...') if len(reason) > 120 else reason
            log.warning(f"  - {url}")
            log.warning(f"    Reason: {reason_short}")
        log.info("--------------------------")
    else:
        log.info("--> No failures or skips detected.")
    log.info("="*70)

# --- Main Function ---

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="VECINA Scraper: Scrapes URLs and local files, outputting to a single text file.")
    
    parser.add_argument("--input", 
                        type=str, 
                        required=True,
                        help="REQUIRED: Path to the input file of URLs to process (e.g., data/urls.txt).")
    
    parser.add_argument("--output-file", 
                        type=str, 
                        required=True,
                        help="REQUIRED: Path to the output file. New content will be APPENDED.")
    
    parser.add_argument("--failed-log", 
                        type=str, 
                        required=True,
                        help="REQUIRED: Path to a file where failed URLs will be logged.")
    
    parser.add_argument("--loader", 
                        type=str,
                        choices=['playwright', 'recursive', 'unstructured'],
                        help="(Optional) Force a specific loader for all URLs in the input file.")

    args = parser.parse_args()

    # --- Initialize Summary Lists ---
    successful_sources = []
    failed_sources = {} # Dict to store URL -> reason for failure/skip
    
    # --- Load Configs ---
    global SITES_TO_CRAWL, SITES_NEEDING_PLAYWRIGHT, SITES_TO_SKIP
    SITES_TO_CRAWL = load_recursive_config(RECURSIVE_SITES_FILE)
    SITES_NEEDING_PLAYWRIGHT = load_config_list(PLAYWRIGHT_SITES_FILE)
    SITES_TO_SKIP = load_config_list(SKIP_SITES_FILE)
    log.info(f"Loaded {len(SITES_TO_CRAWL)} recursive sites, {len(SITES_NEEDING_PLAYWRIGHT)} playwright sites, {len(SITES_TO_SKIP)} skip sites.")


    # --- Check for output file ---
    # This script *appends*, so we just check if it's writable.
    # The load_data.sh script is responsible for *cleaning* it first.
    log.info(f"\n📝 Appending output to: {args.output_file}")
    try:
        with open(args.output_file, 'a', encoding='utf-8') as f:
            f.write(f"# --- VECINA Scraper run started {time.ctime()} ---\n\n")
    except Exception as e:
        log.error(f"--> ❌ CRITICAL: Cannot write to output file {args.output_file}: {e}")
        return

    # --- Process URLs ---
    log.info(f"\n🌐 Starting website processing from {args.input}...")
    if not os.path.exists(args.input):
        log.error(f"❌ Input URL file not found: {args.input}")
    else:
        urls_to_process = []
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and line.startswith('http') and not line.startswith('#'):
                         urls_to_process.append(line)
                    elif line and not line.startswith('#') and not line.startswith('http'):
                        log.warning(f"--> Skipping invalid line {line_num} in {args.input}: '{line}'")
        except Exception as e:
            log.error(f"--> ❌ Error reading URL file {args.input}: {e}")

        log.info(f"Found {len(urls_to_process)} valid URLs to process in {args.input}")

        for i, url in enumerate(urls_to_process, 1):
            log.info(f"\n[{i}/{len(urls_to_process)}]")
            is_success = load_url(url, args.output_file, args.failed_log, args.loader)
            if is_success:
                successful_sources.append(url)
            # Failure is handled inside load_url by writing to the failed_log

    # --- Process Local Files (only if NOT in forced-loader mode) ---
    if not args.loader:
        log.info("\n📁 Processing local files in data/ directory...")
        processed_local_sources = set()
        if os.path.exists(DATA_DIR):
            try:
                filenames = sorted(os.listdir(DATA_DIR))
            except Exception as e:
                log.error(f"--> ❌ Could not list files in {DATA_DIR}: {e}")
                filenames = [] 

            for filename in filenames:
                file_path = os.path.join(DATA_DIR, filename)
                abs_file_path = os.path.abspath(file_path) 

                if not os.path.isfile(file_path): continue
                if filename == os.path.basename(args.input): continue # Don't process the input list
                if filename.startswith("failed_urls"): continue # Don't process failure logs
                if os.path.basename(args.output_file) == filename: continue # Don't process the output file
                if filename.startswith("temp_"): continue # Skip temp files
                
                # Check for config files
                if os.path.abspath(os.path.dirname(file_path)) == os.path.abspath(CONFIG_DIR):
                    log.info(f"--> Skipping config file: {filename}")
                    continue

                if file_path in processed_local_sources: continue

                log.info(f"\nProcessing local file: {filename}")
                docs = []
                loader_type = "File Loader"
                file_processed_successfully = False

                try:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext == '.pdf':
                        loader_type = "PDF"
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                    elif ext == '.txt':
                        loader_type = "Text"
                        try:
                            loader = TextLoader(file_path, encoding='utf-8')
                            docs = loader.load()
                        except UnicodeDecodeError:
                            log.warning(f"--> UTF-8 decode error, trying latin-1 for {filename}")
                            loader = TextLoader(file_path, encoding='latin-1') 
                            docs = loader.load()
                    elif ext == '.csv':
                        loader_type = "CSV"
                        loader = CSVLoader(file_path, encoding='utf-8') 
                        docs = loader.load()
                    else:
                        log.info(f"--> Skipping unsupported file type: {filename}")
                        continue 

                    if docs:
                        chunks_written = process_documents(docs, file_path, loader_type, output_file=args.output_file)
                        if chunks_written > 0:
                            file_processed_successfully = True
                    else:
                         log.warning(f"--> No documents extracted from local file: {filename}")

                    processed_local_sources.add(file_path)
                    
                    if file_processed_successfully:
                         successful_sources.append(f"local:{filename}")
                    else:
                         failed_sources[f"local:{filename}"] = "Processing resulted in zero usable chunks or loader failed."

                except Exception as e:
                    log.error(f"❌ Error processing local file {filename}: {e}")
                    failed_sources[f"local:{filename}"] = f"Unexpected error: {str(e)}"
        else:
            log.warning(f"Data directory {DATA_DIR} not found. Skipping local file processing.")

    # --- Print Final Summary ---
    print_summary(successful_sources, failed_sources)

    log.info("\n" + "="*70)
    log.info("✅ ALL PROCESSING COMPLETE!")
    log.info("="*70)

if __name__ == "__main__":
    main()
##--end-of-filr--

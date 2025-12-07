import pytest
from playwright.sync_api import sync_playwright

# Example Playwright test: open index.html and check title


def test_client_index_title():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # Open the local index.html file
        page.goto("file://" + __import__('os').path.abspath("client/index.html"))
        title = page.title()
        assert "" != title  # Adjust to expected title if known
        browser.close()

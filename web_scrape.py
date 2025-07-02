from playwright.async_api import async_playwright, Error as PlaywrightError # FIX: Import Error as PlaywrightError
from pathlib import Path
import os

# FIX: Dynamically determine RAW_DIR based on the new BASE_DIR from memory.py
# Assuming memory.py is imported and its BASE_DIR is the source of truth
import memory
RAW_DIR = memory.BASE_DIR / "raw_hits"
RAW_DIR.mkdir(parents=True, exist_ok=True) # Ensure this directory exists

async def scrape_text_content(url: str, selector: str = 'body') -> str:
    """
    Navigates to a URL, waits for a specified selector (defaulting to the entire body),
    and returns its full text content. Designed for general web scraping of readable text.
    """
    print(f"Scraping text content from: {url} using selector: {selector}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True) # Run headless browser
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded') # Wait for DOM to be loaded
            
            # Wait for the specific selector to be present
            try:
                await page.wait_for_selector(selector, timeout=10000) # 10 seconds timeout
            except PlaywrightError as e: # FIX: Use PlaywrightError
                print(f"Warning: Selector '{selector}' not found on page {url} within timeout. Trying to get body content.")
                selector = 'body' # Fallback to body if specific selector fails

            # Get all text content within the specified selector
            content = await page.locator(selector).all_text_contents()
            
            await browser.close()
            
            if content:
                # Join all text content into a single string, remove excessive whitespace
                full_text = "\n".join(content)
                # Basic cleanup: replace multiple newlines/spaces with single ones
                full_text = ' '.join(full_text.split())
                return full_text
            else:
                print(f"No text content found for selector '{selector}' on {url}.")
                return ""
    except Exception as e:
        print(f"Error during web scraping {url}: {e}")
        return ""

from playwright.async_api import async_playwright, Playwright, Browser
import asyncio
from typing import Union # FIX: Added import for Union
from typing import Dict # FIX: Added import for Dict (used in fill_form)

# Global variables to store the Playwright instance and the browser
# These will be initialized once and reused.
_playwright_instance: Union[Playwright, None] = None
_browser_instance: Union[Browser, None] = None

async def _initialize_playwright_browser():
    """Initializes the Playwright instance and launches a browser."""
    global _playwright_instance, _browser_instance
    if _browser_instance is None:
        print("Initializing Playwright and launching browser (this may take a moment)...")
        _playwright_instance = await async_playwright().start()
        _browser_instance = await _playwright_instance.chromium.launch(headless=True)
        print("Playwright browser launched.")

async def _close_playwright_browser():
    """Closes the Playwright browser instance."""
    global _playwright_instance, _browser_instance
    if _browser_instance:
        print("Closing Playwright browser...")
        await _browser_instance.close()
        _browser_instance = None
    if _playwright_instance:
        await _playwright_instance.stop()
        _playwright_instance = None
        print("Playwright instance stopped.")

async def navigate_to(url: str) -> str:
    """
    Opens a page asynchronously and returns page content using a reusable browser instance.
    """
    await _initialize_playwright_browser() # Ensure browser is launched
    if _browser_instance is None:
        return "Error: Playwright browser not initialized."

    try:
        page = await _browser_instance.new_page() # Open a new page in the existing browser
        await page.goto(url, wait_until='domcontentloaded')
        content = await page.content()
        await page.close() # Close the page, but keep the browser open
        return content
    except Exception as e:
        print(f"Error navigating to {url}: {e}")
        return f"Error navigating to {url}: {e}"

async def fill_form(url: str, data: Dict) -> None:
    """
    Navigates to a URL asynchronously and fills a form using a reusable browser instance.
    """
    await _initialize_playwright_browser() # Ensure browser is launched
    if _browser_instance is None:
        return "Error: Playwright browser not initialized."

    try:
        page = await _browser_instance.new_page() # Open a new page in the existing browser
        await page.goto(url, wait_until='domcontentloaded')
        for selector, value in data.items():
            await page.fill(selector, value)
        await page.click('input[type=submit], button[type=submit]')
        await page.close() # Close the page, but keep the browser open
        return f"Form submitted successfully on {url}."
    except Exception as e:
        print(f"Error filling form on {url}: {e}")
        return f"Error filling form on {url}: {e}"

# --- NEW: Function to ensure browser is closed on application exit ---
# This will be called from main.py's cleanup
async def cleanup_browser():
    """Call this function to ensure the Playwright browser is properly closed."""
    await _close_playwright_browser()

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
# No unused imports found in this file to remove


def product_research_ali(kw: str) -> List[Dict]:
    """Searches AliExpress for products based on keywords and returns a list of product details."""
    url = f"https://www.aliexpress.com/wholesale?SearchText={kw}"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        products = []
        for item in soup.select('a[itemprop="url"]')[:5]:
            products.append({"title": item.get('title'), "link": item.get('href')})
        return products
    except Exception:
        return []


def tiktok_trend_scrape(tag: str) -> List[Dict]:
    """Scrapes TikTok for trending videos/data related to a given hashtag."""
    url = f"https://www.tiktok.com/tag/{tag}"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        vids = []
        for div in soup.find_all('div', {'data-e2e': 'search-video-item'})[:5]:
            title = div.get_text(strip=True)
            vids.append({"title": title})
        return vids
    except Exception:
        return []


def profit_calc(revenue: float, cogs: float, ship: float, ads: float) -> float: # FIX: Added revenue parameter
    """Calculates potential profit given revenue, cost of goods sold, shipping, and advertising costs."""
    return revenue - (cogs + ship + ads) # FIX: Corrected calculation


def shopify_api_upload(prod_json: dict) -> str:
    """Uploads product data to Shopify via API and returns the product ID."""
    # Placeholder stub; integration would require API keys and endpoints
    return "fake_product_id"

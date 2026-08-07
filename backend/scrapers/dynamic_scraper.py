from typing import List, Optional
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class DynamicScraper:
    def __init__(self):
        pass

    async def scrape_url(self, url: str) -> str:
        """
        Scrapes a Javascript-rendered page using Playwright.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)
                content = await page.content()
                
                soup = BeautifulSoup(content, 'html.parser')
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text(separator=' ', strip=True)
                return text
            except Exception as e:
                print(f"Playwright failed to scrape {url}: {e}")
                return ""
            finally:
                await browser.close()

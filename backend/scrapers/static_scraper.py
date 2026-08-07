import requests
from bs4 import BeautifulSoup
from typing import List, Dict

class StaticScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def scrape_url(self, url: str) -> str:
        """
        Scrapes a static HTML page and returns the text content.
        Useful for generic career pages.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text(separator=' ', strip=True)
            return text
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            return ""

    def extract_links(self, url: str, domain: str = "") -> List[str]:
        """
        Extracts all relevant links from a page (like job postings).
        """
        links = []
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/'):
                    href = domain + href
                links.append(href)
        except Exception as e:
            pass
        return list(set(links))

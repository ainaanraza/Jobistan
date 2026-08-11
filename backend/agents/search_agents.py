from typing import TypedDict, Annotated, List, Dict, Any, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
import operator

# The state schema for our LangGraph agents
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    jobs_found: List[Dict[str, Any]]
    companies_to_search: List[str]
    urls_to_scrape: List[str]
    user_profile: Dict[str, Any]
    final_report: str

from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests

def global_search_node(state: AgentState):
    """
    Searches global job boards using DuckDuckGo.
    """
    import concurrent.futures
    jobs = state.get("jobs_found", [])
    print("Running global search (DuckDuckGo)...")
    
    preferred_roles = state.get("user_profile", {}).get("preferred_roles", "Software Engineer")
    locations = state.get("user_profile", {}).get("preferred_locations", "Remote")
    
    def fetch_duckduckgo():
        with DDGS() as ddgs:
            return list(ddgs.text(f"{preferred_roles} jobs {locations}", max_results=5))

    try:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            results = pool.submit(fetch_duckduckgo).result(timeout=10)
            
            # If DuckDuckGo rate-limits us (returns empty), fallback to an open job API
            if not results:
                print("DuckDuckGo returned empty (likely rate limit), falling back to Arbeitnow API...")
                import requests
                resp = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
                if resp.status_code == 200:
                    api_jobs = resp.json().get("data", [])[:5]
                    for j in api_jobs:
                        jobs.append({
                            "title": j.get("title", ""),
                            "company": j.get("company_name", ""),
                            "job_url": j.get("url", ""),
                            "description": j.get("description", "")[:200] + "...",
                            "location": j.get("location", "Remote"),
                            "salary_range": "Undisclosed"
                        })
            else:
                for r in results:
                    jobs.append({
                        "title": r.get("title", ""),
                        "company": r.get("title", "").split(" - ")[0][:50], # Rough extraction
                        "job_url": r.get("href", ""),
                        "description": r.get("body", ""),
                        "location": locations,
                        "salary_range": "Undisclosed"
                    })
    except Exception as e:
        print(f"Failed to fetch DuckDuckGo jobs: {e}")
        
    return {"jobs_found": jobs}

def company_career_node(state: AgentState):
    """
    Visits company career pages to scrape jobs using Playwright and Gemini.
    """
    print("Running advanced company career scraper (Playwright + Gemini)...")
    jobs = state.get("jobs_found", [])
    urls_to_scrape = state.get("urls_to_scrape", [])
    user_profile = state.get("user_profile", {})
    
    from playwright.sync_api import sync_playwright
    from core.ai import extract_jobs_from_text
    from urllib.parse import urlparse
    import time
    import sys
    
    if sys.platform == 'win32':
        import asyncio
        old_policy = asyncio.get_event_loop_policy()
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            for url in urls_to_scrape:
                try:
                    print(f"Navigating to {url}...")
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    time.sleep(2)
                    page_text = page.evaluate('document.body.innerText')
                    links = page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('a')).map(a => `${a.innerText.trim()} -> ${a.href}`).join('\\n');
                    }''')
                    
                    combined_content = f"PAGE TEXT:\n{page_text}\n\nPAGE LINKS:\n{links}"
                    print(f"Extracting jobs from {url} using Gemini AI...")
                    extracted_jobs = extract_jobs_from_text(combined_content, url, user_profile)
                    
                    parsed_uri = urlparse(url)
                    domain = f"{parsed_uri.netloc}"
                    
                    for j in extracted_jobs:
                        jobs.append({
                            "title": j.get("title", "Unknown Role"),
                            "company": domain,
                            "job_url": j.get("job_url", url),
                            "description": j.get("description", "Discovered via AI Scraper"),
                            "location": j.get("location", "Varies"),
                            "salary_range": j.get("salary_range", "Undisclosed")
                        })
                except Exception as e:
                    print(f"Failed to scrape {url} with Playwright: {e}")
                    
            browser.close()
    finally:
        if sys.platform == 'win32':
            import asyncio
            asyncio.set_event_loop_policy(old_policy)
            
    return {"jobs_found": jobs}

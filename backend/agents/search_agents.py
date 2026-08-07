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

import requests

def global_search_node(state: AgentState):
    """
    Searches global job boards.
    """
    jobs = state.get("jobs_found", [])
    print("Running global search (Hacker News Jobs)...")
    try:
        resp = requests.get("https://hacker-news.firebaseio.com/v0/jobstories.json", timeout=5)
        if resp.status_code == 200:
            job_ids = resp.json()[:5]  # Get top 5 jobs
            for j_id in job_ids:
                job_resp = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{j_id}.json", timeout=5)
                if job_resp.status_code == 200:
                    job_data = job_resp.json()
                    title = job_data.get("title", "")
                    company = title.split(" is ")[0] if " is " in title else "HackerNews Startup"
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "job_url": job_data.get("url", f"https://news.ycombinator.com/item?id={j_id}"),
                        "description": job_data.get("text", title),
                        "location": "Remote / US",
                        "salary_range": "Undisclosed"
                    })
    except Exception as e:
        print(f"Failed to fetch real jobs: {e}")
        
    return {"jobs_found": jobs}

def company_career_node(state: AgentState):
    """
    Visits company career pages to scrape jobs.
    """
    print("Running company career scraper...")
    jobs = state.get("jobs_found", [])
    # In a real scenario, use DynamicScraper/StaticScraper here
    return {"jobs_found": jobs}

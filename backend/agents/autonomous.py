from sqlalchemy.orm import Session
from agents.search_agents import global_search_node, company_career_node, AgentState
from crud.crud_job import create_job
from core.ai import generate_embedding
from db.session import SessionLocal

def run_autonomous_scraper():
    """
    Runs the job scraping agents autonomously in the background.
    """
    print("Starting Autonomous Background Agent...")
    
    # Initialize a dummy state for the global scrape
    # We could also loop through all users in the DB and get their preferences,
    # but for a global background scraper, we'll run a general tech sweep.
    initial_state: AgentState = {
        "messages": [],
        "jobs_found": [],
        "companies_to_search": [],
        "urls_to_scrape": [
            "https://careers.google.com",
            "https://www.metacareers.com"
        ],
        "user_profile": {
            "preferred_roles": "Software Engineer, Full Stack, Backend",
            "preferred_locations": "Remote"
        },
        "final_report": ""
    }
    
    # 1. Run Global Search
    state_after_global = global_search_node(initial_state)
    
    # 2. Run Company Scraper
    final_state = company_career_node(state_after_global)
    
    jobs_found = final_state.get("jobs_found", [])
    print(f"Autonomous agent found {len(jobs_found)} jobs. Saving to database...")
    
    # 3. Save to database
    db: Session = SessionLocal()
    try:
        saved_count = 0
        for job_data in jobs_found:
            # Generate embedding for semantic matching later
            embedding = generate_embedding(job_data.get("title", "") + " " + job_data.get("description", ""))
            
            # Save job
            job = create_job(db=db, job_data=job_data, embedding=embedding)
            if job:
                saved_count += 1
                
        print(f"Autonomous agent successfully saved {saved_count} new jobs.")
    except Exception as e:
        print(f"Database error during autonomous run: {e}")
    finally:
        db.close()

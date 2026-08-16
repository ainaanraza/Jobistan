from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api import deps
from models.user import User
from schemas.job import Job
from crud.crud_job import get_jobs, seed_mock_data, search_jobs_semantically
from crud.crud_profile import get_profile_by_user_id
from core.ai import generate_embedding

router = APIRouter()

@router.get("/", response_model=List[Job])
def read_jobs(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve matched jobs for the current user.
    """
    res = []
    profile = get_profile_by_user_id(db, current_user.id)
    
    # Try semantic search if profile has data
    if profile and (profile.skills or profile.preferred_roles or profile.experience):
        profile_text = f"{profile.preferred_roles or ''} {profile.skills or ''} {profile.experience or ''}"
        profile_embedding = generate_embedding(profile_text)
        
        if profile_embedding:
            semantic_jobs = search_jobs_semantically(db, profile_embedding, limit)
            for j, distance in semantic_jobs:
                # Cosine distance: 0 is exact match.
                # Convert to a percentage score (0-100)
                score = max(0, (1 - distance)) * 100
                res.append({
                    "id": j.id,
                    "title": j.title,
                    "description": j.description,
                    "location": j.location,
                    "salary_range": j.salary_range,
                    "job_url": j.job_url,
                    "company_id": j.company_id,
                    "company_name": j.company.name if j.company else None,
                    "match_score": round(score, 1)
                })
            return res

    # Fallback to standard jobs if no profile or embedding failed
    jobs = get_jobs(db, skip=skip, limit=limit)
    for j in jobs:
        res.append({
            "id": j.id,
            "title": j.title,
            "description": j.description,
            "location": j.location,
            "salary_range": j.salary_range,
            "job_url": j.job_url,
            "company_id": j.company_id,
            "company_name": j.company.name if j.company else None,
            "match_score": None
        })
    return res

@router.post("/seed")
def seed_jobs(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Run LangGraph Agent Workflow to discover jobs.
    """
    from core.ingestion.manager import IngestionManager
    from models.job_source import JobSource
    
    manager = IngestionManager()
    
    # Get active job sources
    sources = db.query(JobSource).filter(JobSource.user_id == current_user.id, JobSource.is_active == True).all()
    
    results = []
    total_new = 0
    total_updated = 0
    
    # 1. Process deterministic sources via IngestionManager
    for source in sources:
        summary = manager.process_source(db, source)
        results.append(summary)
        total_new += summary.get("new", 0)
        total_updated += summary.get("updated", 0)
        
    # 2. (Optional/Background) Run the old AI agent workflow for broad searches
    # To keep it fast, we can either queue it or just let it run if there are no URLs
    # Since instructions say "don't delete it, make it one source", we'll run it on empty URLs or general broad queries.
    from agents.supervisor import run_workflow
    from crud.crud_profile import get_profile_by_user_id
    from models.job import Job
    
    profile = get_profile_by_user_id(db, current_user.id)
    profile_dict = {
        "preferred_roles": profile.preferred_roles if profile else "Software Engineer",
        "preferred_locations": profile.preferred_locations if profile else "Remote"
    }
    
    # Only run AI workflow for generic queries (empty URLs list triggers DuckDuckGo search)
    # The previous code passed all URLs to AI. We now handle URLs deterministically.
    try:
        ai_result = run_workflow(user_profile=profile_dict, urls=[])
        found_jobs = ai_result.get("jobs_found", [])
        
        for j_data in found_jobs:
            existing = db.query(Job).filter(Job.job_url == j_data["job_url"]).first()
            if existing:
                continue
                
            new_job = Job(
                title=j_data["title"],
                description=j_data.get("description", ""),
                location=j_data.get("location", ""),
                salary_range=j_data.get("salary_range", ""),
                job_url=j_data["job_url"],
                embedding=j_data.get("embedding"),
                source_type="AI_Search",
                source_name="DuckDuckGo",
                is_active=True
            )
            db.add(new_job)
            total_new += 1
            
        db.commit()
    except Exception as e:
        print(f"AI search fallback failed: {e}")
    
    return {
        "message": f"Ingestion completed. Found {total_new} new jobs and updated {total_updated}.",
        "source_results": results
    }

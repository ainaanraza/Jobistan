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
    from agents.supervisor import run_workflow
    from models.job_source import JobSource
    from models.job import Job
    from crud.crud_profile import get_profile_by_user_id
    
    profile = get_profile_by_user_id(db, current_user.id)
    profile_dict = {
        "preferred_roles": profile.preferred_roles if profile else "Software Engineer",
        "preferred_locations": profile.preferred_locations if profile else "Remote"
    }
    
    # Get active job sources
    sources = db.query(JobSource).filter(JobSource.user_id == current_user.id, JobSource.is_active == True).all()
    urls = [s.url for s in sources]
    
    # Run agent workflow
    result = run_workflow(user_profile=profile_dict, urls=urls)
    
    # The deduplication node has already run and populated `embedding` and returned unique jobs
    found_jobs = result.get("jobs_found", [])
    
    added_count = 0
    for j_data in found_jobs:
        # Prevent IntegrityError by checking if URL already exists
        existing = db.query(Job).filter(Job.job_url == j_data["job_url"]).first()
        if existing:
            continue
            
        new_job = Job(
            title=j_data["title"],
            description=j_data.get("description", ""),
            location=j_data.get("location", ""),
            salary_range=j_data.get("salary_range", ""),
            job_url=j_data["job_url"],
            embedding=j_data.get("embedding")
            # For simplicity, ignoring company_id mapping for now
        )
        db.add(new_job)
        added_count += 1
        
    db.commit()
    
    return {"message": f"Agent workflow completed successfully! Found and added {added_count} new unique jobs."}

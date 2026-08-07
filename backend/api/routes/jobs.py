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
    Seed mock jobs for developer testing/preview.
    """
    seed_mock_data(db)
    return {"message": "Database seeded successfully with mock jobs and companies"}

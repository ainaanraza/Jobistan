from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api import deps
from models.user import User
from schemas.job import Job
from crud.crud_job import get_jobs, seed_mock_data

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
    jobs = get_jobs(db, skip=skip, limit=limit)
    res = []
    for j in jobs:
        res.append({
            "id": j.id,
            "title": j.title,
            "description": j.description,
            "location": j.location,
            "salary_range": j.salary_range,
            "job_url": j.job_url,
            "company_id": j.company_id,
            "company_name": j.company.name if j.company else None
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

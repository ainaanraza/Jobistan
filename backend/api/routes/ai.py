from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api import deps
from models.user import User
from models.job import Job
from models.profile import Profile
from core.ai import generate_cover_letter

router = APIRouter()

@router.post("/generate-cover-letter/{job_id}")
def generate_cl(
    job_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Generate a tailored cover letter for a specific job using the user's profile.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="User profile is required to generate a cover letter")
        
    profile_dict = {
        "skills": profile.skills,
        "experience": profile.experience,
        "education": profile.education,
        "projects": profile.projects
    }
    
    cover_letter = generate_cover_letter(
        profile_dict=profile_dict,
        job_title=job.title,
        job_company=job.company.name if job.company else "Unknown Company",
        job_desc=job.description
    )
    
    return {"cover_letter": cover_letter}

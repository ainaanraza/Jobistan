from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from db.session import get_db
from models.user import User
from models.job_match import JobMatch
from api.deps import get_current_user

router = APIRouter()

@router.get("/")
def get_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    min_score: float = Query(0.0),
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    remote_only: bool = Query(False),
):
    query = db.query(JobMatch).filter(JobMatch.user_id == current_user.id)
    
    if min_score > 0:
        query = query.filter(JobMatch.match_score >= min_score)
        
    matches = query.order_by(JobMatch.rank.asc(), JobMatch.match_score.desc()).all()
    
    # Filter related to job attributes
    results = []
    for m in matches:
        job = m.canonical_job
        
        if remote_only and not job.remote:
            continue
        if role and job.role_category and role.lower() not in job.role_category.lower() and role.lower() not in job.title.lower():
            continue
        if location and job.location and location.lower() not in job.location.lower():
            continue
            
        results.append({
            "id": m.id,
            "job_id": job.id,
            "title": job.title,
            "company": job.company_name,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "currency": job.currency,
            "match_score": m.match_score,
            "match_reasons": m.match_reasons,
            "posted_at": job.first_seen_at,
            "application_url": job.best_application_url,
            "is_saved": m.is_saved
        })
        
    return results

@router.get("/{id}")
def get_match(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(JobMatch).filter(JobMatch.id == id, JobMatch.user_id == current_user.id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    job = match.canonical_job
    return {
        "id": match.id,
        "job_id": job.id,
        "title": job.title,
        "company": job.company_name,
        "description": job.description,
        "location": job.location,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "currency": job.currency,
        "skills": job.skills,
        "match_score": match.match_score,
        "match_reasons": match.match_reasons,
        "application_url": job.best_application_url,
        "is_saved": match.is_saved
    }

@router.post("/{id}/save")
def save_match(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(JobMatch).filter(JobMatch.id == id, JobMatch.user_id == current_user.id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    match.is_saved = True
    db.commit()
    return {"status": "saved"}

@router.delete("/{id}/save")
def unsave_match(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    match = db.query(JobMatch).filter(JobMatch.id == id, JobMatch.user_id == current_user.id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    match.is_saved = False
    db.commit()
    return {"status": "unsaved"}

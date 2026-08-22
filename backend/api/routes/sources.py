from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api import deps
from schemas.job_source import JobSource, JobSourceCreate, JobSourceUpdate
from models.job_source import JobSource as JobSourceModel
from models.user import User

router = APIRouter()

@router.get("/", response_model=List[JobSource])
def read_job_sources(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve job sources.
    """
    sources = db.query(JobSourceModel).filter(JobSourceModel.user_id == current_user.id).offset(skip).limit(limit).all()
    return sources

@router.post("/", response_model=JobSource)
def create_job_source(
    *,
    db: Session = Depends(deps.get_db),
    source_in: JobSourceCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new job source.
    """
    source = JobSourceModel(
        **source_in.dict(),
        user_id=current_user.id
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.put("/{id}", response_model=JobSource)
def update_job_source(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    source_in: JobSourceUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a job source.
    """
    source = db.query(JobSourceModel).filter(JobSourceModel.id == id, JobSourceModel.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Job source not found")
    
    update_data = source_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)
        
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.delete("/{id}", response_model=JobSource)
def delete_job_source(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a job source.
    """
    source = db.query(JobSourceModel).filter(JobSourceModel.id == id, JobSourceModel.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Job source not found")
    
    db.delete(source)
    db.commit()
    return source

@router.post("/{id}/repair")
def repair_job_source(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Manually trigger self-healing for a source.
    """
    source = db.query(JobSourceModel).filter(JobSourceModel.id == id, JobSourceModel.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Job source not found")
        
    from core.ingestion.manager import IngestionManager
    manager = IngestionManager()
    
    result = manager.process_source(db, source, force_heal=True)
    return result

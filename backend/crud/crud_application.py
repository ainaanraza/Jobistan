from typing import List, Optional
from sqlalchemy.orm import Session
from models.application import Application
from schemas.application import ApplicationCreate, ApplicationUpdate

def get_applications(db: Session, user_id: int) -> List[Application]:
    """Retrieve all applications for a specific user, with job details included."""
    return db.query(Application).filter(Application.user_id == user_id).all()

def create_application(db: Session, user_id: int, obj_in: ApplicationCreate) -> Application:
    """Create a new application record."""
    # Check if application already exists for this user and job
    existing = db.query(Application).filter(
        Application.user_id == user_id, 
        Application.job_id == obj_in.job_id
    ).first()
    
    if existing:
        return existing
        
    db_obj = Application(
        user_id=user_id,
        job_id=obj_in.job_id,
        status=obj_in.status,
        notes=obj_in.notes
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_application(db: Session, app_id: int, user_id: int, obj_in: ApplicationUpdate) -> Optional[Application]:
    """Update application status or notes."""
    db_obj = db.query(Application).filter(
        Application.id == app_id, 
        Application.user_id == user_id
    ).first()
    
    if not db_obj:
        return None
        
    if obj_in.status is not None:
        db_obj.status = obj_in.status
    if obj_in.notes is not None:
        db_obj.notes = obj_in.notes
        
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_application(db: Session, app_id: int, user_id: int) -> bool:
    """Delete an application."""
    db_obj = db.query(Application).filter(
        Application.id == app_id, 
        Application.user_id == user_id
    ).first()
    
    if not db_obj:
        return False
        
    db.delete(db_obj)
    db.commit()
    return True

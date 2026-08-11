from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api import deps
from models.user import User
from schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from crud.crud_application import get_applications, create_application, update_application, delete_application

router = APIRouter()

@router.get("/", response_model=List[ApplicationResponse])
def read_applications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve all applications for the current user.
    """
    return get_applications(db, current_user.id)

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_new_application(
    obj_in: ApplicationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Save a job as an application.
    """
    return create_application(db, current_user.id, obj_in)

@router.patch("/{app_id}", response_model=ApplicationResponse)
def update_existing_application(
    app_id: int,
    obj_in: ApplicationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update an application (status or notes).
    """
    app = update_application(db, app_id, current_user.id, obj_in)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_application(
    app_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> None:
    """
    Delete a saved application.
    """
    success = delete_application(db, app_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return None

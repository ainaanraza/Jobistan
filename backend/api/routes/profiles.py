from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import deps
from models.user import User
from schemas.profile import Profile, ProfileUpdate
from crud.crud_profile import get_profile_by_user_id, update_profile

router = APIRouter()

@router.get("/me", response_model=Profile)
def read_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current user's profile.
    """
    profile = get_profile_by_user_id(db, user_id=current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/me", response_model=Profile)
def update_user_profile(
    *,
    db: Session = Depends(deps.get_db),
    profile_in: ProfileUpdate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update current user's profile.
    """
    profile = get_profile_by_user_id(db, user_id=current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = update_profile(db, db_obj=profile, obj_in=profile_in)
    return profile

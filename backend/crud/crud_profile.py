from typing import Optional
from sqlalchemy.orm import Session
from models.profile import Profile
from schemas.profile import ProfileUpdate

def get_profile_by_user_id(db: Session, user_id: int) -> Optional[Profile]:
    return db.query(Profile).filter(Profile.user_id == user_id).first()

def update_profile(db: Session, *, db_obj: Profile, obj_in: ProfileUpdate) -> Profile:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field in update_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

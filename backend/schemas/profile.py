from pydantic import BaseModel
from typing import Optional

# Shared properties
class ProfileBase(BaseModel):
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    preferred_roles: Optional[str] = None
    preferred_locations: Optional[str] = None
    salary_expectations: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    college: Optional[str] = None
    school: Optional[str] = None
    city: Optional[str] = None
    projects: Optional[str] = None

# Properties to receive via API on update
class ProfileUpdate(ProfileBase):
    pass

class ProfileCreate(ProfileBase):
    pass

# Properties in DB
class ProfileInDBBase(ProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# Additional properties to return via API
class Profile(ProfileInDBBase):
    pass

from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum

class SourceTypeEnum(str, Enum):
    company_career_page = "company_career_page"
    job_portal = "job_portal"
    direct_url = "direct_url"

class JobSourceBase(BaseModel):
    name: str
    url: str
    source_type: SourceTypeEnum
    is_active: Optional[bool] = True

class JobSourceCreate(JobSourceBase):
    pass

class JobSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[SourceTypeEnum] = None
    is_active: Optional[bool] = None

class JobSourceInDBBase(JobSourceBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class JobSource(JobSourceInDBBase):
    pass

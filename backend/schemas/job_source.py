from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class SourceTypeEnum(str, Enum):
    ATS = "ATS"
    CAREER_PAGE = "CAREER_PAGE"
    DIRECT_JOB = "DIRECT_JOB"
    JOB_PORTAL = "JOB_PORTAL"
    SEARCH_ENGINE = "SEARCH_ENGINE"

class JobSourceBase(BaseModel):
    name: str
    url: str
    source_type: SourceTypeEnum
    is_active: Optional[bool] = True
    crawl_frequency: Optional[int] = 14400
    configuration: Optional[Dict[str, Any]] = None

class JobSourceCreate(JobSourceBase):
    pass

class JobSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[SourceTypeEnum] = None
    is_active: Optional[bool] = None
    crawl_frequency: Optional[int] = None
    configuration: Optional[Dict[str, Any]] = None

class JobSourceInDBBase(JobSourceBase):
    id: int
    user_id: int
    last_checked_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    content_hash: Optional[str] = None

    class Config:
        from_attributes = True

class JobSource(JobSourceInDBBase):
    pass

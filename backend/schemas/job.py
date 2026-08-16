from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# Shared properties
class JobBase(BaseModel):
    title: str
    description: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: str
    company_id: Optional[int] = None
    
    external_id: Optional[str] = None
    remote: Optional[bool] = False
    employment_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    posted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

# Properties to return via API
class Job(JobBase):
    id: int
    company_name: Optional[str] = None
    match_score: Optional[float] = None

    class Config:
        from_attributes = True

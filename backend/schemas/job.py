from pydantic import BaseModel
from typing import Optional

# Shared properties
class JobBase(BaseModel):
    title: str
    description: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: str
    company_id: Optional[int] = None

# Properties to return via API
class Job(JobBase):
    id: int
    company_name: Optional[str] = None

    class Config:
        from_attributes = True

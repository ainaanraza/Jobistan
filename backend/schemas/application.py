from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from schemas.job import Job

# Shared properties
class ApplicationBase(BaseModel):
    job_id: int
    status: Optional[str] = "Saved"
    notes: Optional[str] = None

# Properties to receive on item creation
class ApplicationCreate(ApplicationBase):
    pass

# Properties to receive on item update
class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

# Properties to return to client
class ApplicationResponse(ApplicationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    job: Job

    class Config:
        from_attributes = True

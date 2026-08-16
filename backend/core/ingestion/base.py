from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel

class NormalizedJob(BaseModel):
    external_id: str
    title: str
    company: str
    description: str
    location: Optional[str] = None
    remote: bool = False
    employment_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    salary_period: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    hybrid: bool = False
    extraction_confidence: Optional[float] = None
    validation_status: Optional[str] = None
    extraction_method: Optional[str] = None
    posted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    application_url: str
    source_url: str
    source_type: str
    source_name: str
    raw_data: Dict[str, Any] = {}

class IngestionDiagnostics(BaseModel):
    status: str
    adapter: str
    http_status: Optional[int] = None
    extraction_method: Optional[str] = None
    jobs_found: int = 0
    execution_time_ms: Optional[float] = None
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}

class FetchResult(BaseModel):
    jobs: List[NormalizedJob]
    diagnostics: IngestionDiagnostics

class JobSourceAdapter(ABC):
    @classmethod
    @abstractmethod
    def can_handle(cls, url: str) -> bool:
        """Return True if this adapter can handle the given URL."""
        pass

    @abstractmethod
    def fetch_jobs(self, url: str) -> FetchResult:
        """Fetch all jobs from the given URL and return a FetchResult."""
        pass

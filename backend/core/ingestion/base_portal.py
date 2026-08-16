from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.ingestion.base import JobSourceAdapter, FetchResult

class JobPortalAdapter(JobSourceAdapter, ABC):
    """
    Abstract base class for Job Portals. 
    Concrete subclasses should handle domain matching in `can_handle`.
    """
    
    @abstractmethod
    def parse_search_config(self, url: str) -> Dict[str, Any]:
        """Parse a portal search URL into configuration components, separating raw_params."""
        pass
        
    @abstractmethod
    def validate_source(self) -> bool:
        """Validate if the given portal/configuration is supported."""
        pass
        
    @abstractmethod
    def fetch_jobs(self, url: str) -> FetchResult:
        """Fetch jobs based on the portal URL."""
        pass

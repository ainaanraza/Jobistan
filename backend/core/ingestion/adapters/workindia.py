from typing import Dict, Any
from urllib.parse import urlparse, parse_qs
from core.ingestion.base import FetchResult
from core.ingestion.base_portal import JobPortalAdapter

class WorkIndiaAdapter(JobPortalAdapter):
    @classmethod
    def can_handle(cls, url: str) -> bool:
        parsed = urlparse(url)
        return "workindia" in parsed.netloc

    def parse_search_config(self, url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        
        config = {
            "query": None,
            "location": None,
            "raw_params": {}
        }
        
        for key, values in qs.items():
            if not values:
                continue
                
            val = values[0]
            if key == "query":
                config["query"] = val
            elif key == "city":
                config["location"] = val
            else:
                config["raw_params"][key] = val
                
        return config

    def validate_source(self) -> bool:
        return True

    def fetch_jobs(self, url: str) -> FetchResult:
        return self._default_fetch_jobs(url, "WorkIndia", ['job_id'])

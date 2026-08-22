from typing import Dict, Any
from urllib.parse import urlparse, parse_qs
from core.ingestion.base import FetchResult
from core.ingestion.base_portal import JobPortalAdapter

class TimesJobsAdapter(JobPortalAdapter):
    @classmethod
    def can_handle(cls, url: str) -> bool:
        parsed = urlparse(url)
        return "timesjobs" in parsed.netloc

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
            if key == "search":
                config["query"] = val
            elif key == "location":
                config["location"] = val
            else:
                config["raw_params"][key] = val
                
        return config

    def validate_source(self) -> bool:
        return True

    def fetch_jobs(self, url: str, db=None, source_id=None) -> FetchResult:
        return self._default_fetch_jobs(url, "TimesJobs", ['jobid'])

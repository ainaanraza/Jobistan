from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs
import time
from core.ingestion.base import FetchResult, IngestionDiagnostics
from core.ingestion.base_portal import JobPortalAdapter

class IndeedAdapter(JobPortalAdapter):
    @classmethod
    def can_handle(cls, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc == "indeed.com" or parsed.netloc.endswith(".indeed.com")

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
            if key == "q":
                config["query"] = val
            elif key == "l":
                config["location"] = val
            else:
                config["raw_params"][key] = val
                
        return config

    def validate_source(self) -> bool:
        return True

    def fetch_jobs(self, url: str) -> FetchResult:
        start_time = time.time()
        
        # Indeed is known to block headless browsers via Cloudflare.
        # Until an authorized API integration is provided, we return ACCESS_BLOCKED
        # instead of pretending we found 0 jobs.
        
        diagnostics = IngestionDiagnostics(
            status="ACCESS_BLOCKED",
            adapter="IndeedAdapter",
            http_status=403,
            extraction_method="Indeed Direct",
            jobs_found=0,
            execution_time_ms=round((time.time() - start_time) * 1000, 2),
            errors=["Indeed access is blocked by the current environment's Cloudflare challenge."],
            warnings=[],
            metadata={
                "parsed_config": self.parse_search_config(url)
            }
        )
        
        return FetchResult(jobs=[], diagnostics=diagnostics)

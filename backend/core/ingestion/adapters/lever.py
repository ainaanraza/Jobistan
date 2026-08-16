import requests
from typing import List, Dict, Any
from urllib.parse import urlparse
from core.ingestion.base import JobSourceAdapter, NormalizedJob, FetchResult, IngestionDiagnostics
from core.ingestion.utils import parse_location, validate_job
import datetime

class LeverAdapter(JobSourceAdapter):
    @classmethod
    def can_handle(cls, url: str) -> bool:
        # Prevent bare jobs.lever.co from being claimed if no company is present
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        
        if "api.lever.co" in url or "jobs.lever.co" in url:
            # We must have a company token in the path
            return len(path_parts) >= 1
        return False

    def fetch_jobs(self, url: str) -> FetchResult:
        import time
        start_time = time.time()
        
        diagnostics = IngestionDiagnostics(
            status="SUCCESS",
            adapter="LeverAdapter",
            http_status=None,
            extraction_method="Lever API",
            jobs_found=0,
            execution_time_ms=0.0,
            errors=[],
            warnings=[],
            metadata={}
        )
        
        company_name = self._extract_company(url)
        if not company_name:
            diagnostics.status = "ERROR"
            diagnostics.errors.append(f"Could not extract Lever company name from {url}")
            diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return FetchResult(jobs=[], diagnostics=diagnostics)

        api_url = f"https://api.lever.co/v0/postings/{company_name}?mode=json"
        try:
            response = requests.get(api_url, timeout=10)
            diagnostics.http_status = response.status_code
            
            if response.status_code == 404:
                diagnostics.status = "ERROR"
                diagnostics.errors.append(f"Lever board for '{company_name}' not found.")
                diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
                return FetchResult(jobs=[], diagnostics=diagnostics)
                
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            diagnostics.status = "ERROR"
            diagnostics.errors.append(f"Failed to fetch Lever API: {e}")
            diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return FetchResult(jobs=[], diagnostics=diagnostics)
            
        jobs_data = response.json()
        
        normalized_jobs = []
        for j in jobs_data:
            desc = j.get("descriptionPlain", "") or j.get("description", "")
            categories = j.get("categories", {})
            location_raw = categories.get("location", "Unknown")
            department = categories.get("department", "Unknown")
            
            loc_data = parse_location(location_raw)
            
            created_at = None
            if j.get("createdAt"):
                try:
                    # Lever returns milliseconds timestamp usually
                    created_at = datetime.datetime.fromtimestamp(j["createdAt"] / 1000.0)
                except:
                    pass

            nj = NormalizedJob(
                external_id=str(j.get("id")),
                title=j.get("text", ""),
                company=company_name.capitalize(),
                description=desc or "No description provided.",
                location=location_raw,
                remote="remote" in location_raw.lower() or "remote" in j.get("text", "").lower() or loc_data["remote"],
                hybrid=loc_data["hybrid"],
                city=loc_data["city"],
                state=loc_data["state"],
                country=loc_data["country"],
                posted_at=created_at,
                application_url=j.get("applyUrl") or j.get("hostedUrl", ""),
                source_url=url,
                source_type="ATS",
                source_name="Lever",
                raw_data=j
            )
            val_status, conf = validate_job(nj)
            nj.validation_status = val_status
            nj.extraction_confidence = conf
            nj.extraction_method = "Lever API"
            
            normalized_jobs.append(nj)
            
        diagnostics.jobs_found = len(normalized_jobs)
        diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        return FetchResult(jobs=normalized_jobs, diagnostics=diagnostics)

    def _extract_company(self, url: str) -> str:
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        
        if "api.lever.co" in parsed.netloc:
            if "postings" in path_parts:
                idx = path_parts.index("postings")
                if len(path_parts) > idx + 1:
                    return path_parts[idx + 1]
                    
        # jobs.lever.co/company
        if path_parts:
            return path_parts[0]
            
        return ""

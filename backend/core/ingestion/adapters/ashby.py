import requests
from typing import List, Dict, Any
from urllib.parse import urlparse
from core.ingestion.base import JobSourceAdapter, NormalizedJob, FetchResult, IngestionDiagnostics
import datetime

class AshbyAdapter(JobSourceAdapter):
    @classmethod
    def can_handle(cls, url: str) -> bool:
        return "jobs.ashbyhq.com" in url or "api.ashbyhq.com" in url

    def fetch_jobs(self, url: str) -> FetchResult:
        import time
        start_time = time.time()
        
        diagnostics = IngestionDiagnostics(
            status="SUCCESS",
            adapter="AshbyAdapter",
            http_status=None,
            extraction_method="Ashby API",
            jobs_found=0,
            execution_time_ms=0.0,
            errors=[],
            warnings=[],
            metadata={}
        )
        
        company_name = self._extract_company(url)
        if not company_name:
            diagnostics.status = "ERROR"
            diagnostics.errors.append(f"Could not extract Ashby company name from {url}")
            diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return FetchResult(jobs=[], diagnostics=diagnostics)

        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{company_name}"
        try:
            response = requests.get(api_url, timeout=10)
            diagnostics.http_status = response.status_code
            
            if response.status_code == 404:
                diagnostics.status = "ERROR"
                diagnostics.errors.append(f"Ashby board for '{company_name}' not found.")
                diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
                return FetchResult(jobs=[], diagnostics=diagnostics)
                
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            diagnostics.status = "ERROR"
            diagnostics.errors.append(f"Failed to fetch Ashby API: {e}")
            diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return FetchResult(jobs=[], diagnostics=diagnostics)
            
        data = response.json()
        jobs_data = data.get("jobs", [])
        
        from core.ingestion.utils import parse_location, validate_job
        
        normalized_jobs = []
        for j in jobs_data:
            desc = j.get("descriptionHtml", "")
            location_raw = j.get("location", "Unknown")
            
            loc_data = parse_location(location_raw)
            
            created_at = None
            if j.get("publishedAt"):
                try:
                    # ISO format string usually
                    created_at = datetime.datetime.fromisoformat(j["publishedAt"].replace("Z", "+00:00"))
                except:
                    pass

            # Sometimes Ashby returns compensation
            salary_min = None
            salary_max = None
            currency = None
            comp = j.get("compensation", {})
            if comp and isinstance(comp, dict):
                salary_min = comp.get("compensationTier", {}).get("minimum")
                salary_max = comp.get("compensationTier", {}).get("maximum")
                currency = comp.get("compensationTier", {}).get("currency")

            nj = NormalizedJob(
                external_id=str(j.get("id")),
                title=j.get("title", ""),
                company=company_name.capitalize(),
                description=desc or "No description provided.",
                location=location_raw,
                remote="remote" in location_raw.lower() or j.get("isRemote", False) or loc_data["remote"],
                hybrid=loc_data["hybrid"],
                city=loc_data["city"],
                state=loc_data["state"],
                country=loc_data["country"],
                salary_min=salary_min,
                salary_max=salary_max,
                currency=currency,
                posted_at=created_at,
                application_url=j.get("jobUrl", ""),
                source_url=url,
                source_type="ATS",
                source_name="Ashby",
                raw_data=j
            )
            val_status, conf = validate_job(nj)
            nj.validation_status = val_status
            nj.extraction_confidence = conf
            nj.extraction_method = "Ashby API"
            
            normalized_jobs.append(nj)
            
        diagnostics.jobs_found = len(normalized_jobs)
        diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        return FetchResult(jobs=normalized_jobs, diagnostics=diagnostics)

    def _extract_company(self, url: str) -> str:
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        
        if "api.ashbyhq.com" in parsed.netloc:
            if "job-board" in path_parts:
                idx = path_parts.index("job-board")
                if len(path_parts) > idx + 1:
                    return path_parts[idx + 1]
                    
        # jobs.ashbyhq.com/company
        if path_parts:
            return path_parts[0]
            
        return ""

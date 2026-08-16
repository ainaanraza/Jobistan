import requests
from typing import List, Tuple, Dict, Any
from urllib.parse import urlparse
from core.ingestion.base import JobSourceAdapter, NormalizedJob, FetchResult, IngestionDiagnostics
import html

class GreenhouseAdapter(JobSourceAdapter):
    @classmethod
    def can_handle(cls, url: str) -> bool:
        return "boards.greenhouse.io" in url or "boards-api.greenhouse.io" in url

    def fetch_jobs(self, url: str) -> FetchResult:
        import time
        start_time = time.time()
        
        diagnostics = IngestionDiagnostics(
            status="SUCCESS",
            adapter="GreenhouseAdapter",
            http_status=None,
            extraction_method="Greenhouse API",
            jobs_found=0,
            execution_time_ms=0.0,
            errors=[],
            warnings=[],
            metadata={}
        )
        
        board_token = self._extract_token(url)
        if not board_token:
            diagnostics.status = "ERROR"
            diagnostics.errors.append(f"Could not extract Greenhouse board token from {url}")
            diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return FetchResult(jobs=[], diagnostics=diagnostics)

        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        try:
            response = requests.get(api_url, timeout=10)
            diagnostics.http_status = response.status_code
            
            if response.status_code == 404:
                diagnostics.status = "ERROR"
                diagnostics.errors.append(f"Greenhouse board '{board_token}' not found.")
                # This explicitly handles invalid Greenhouse boards
                diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
                return FetchResult(jobs=[], diagnostics=diagnostics)
                
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            diagnostics.status = "ERROR"
            diagnostics.errors.append(f"Failed to fetch Greenhouse API: {e}")
            diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return FetchResult(jobs=[], diagnostics=diagnostics)
            
        data = response.json()
        jobs_data = data.get("jobs", [])
        
        from core.ingestion.utils import parse_location, validate_job
        
        normalized_jobs = []
        for j in jobs_data:
            # Parse HTML description if needed, or keep raw text
            desc = html.unescape(j.get("content", "")) if j.get("content") else ""
            
            # Extract location
            loc_obj = j.get("location", {})
            location_raw = loc_obj.get("name", "Unknown")
            loc_data = parse_location(location_raw)
            
            # Greenhouse sometimes uses 'departments'
            dept = "Unknown"
            if j.get("departments"):
                dept = j["departments"][0].get("name", "Unknown")
                
            nj = NormalizedJob(
                external_id=str(j.get("id")),
                title=j.get("title", ""),
                company=board_token.capitalize(),
                description=desc or "No description provided.",
                location=location_raw,
                remote="remote" in location_raw.lower() or "remote" in j.get("title", "").lower() or loc_data["remote"],
                hybrid=loc_data["hybrid"],
                city=loc_data["city"],
                state=loc_data["state"],
                country=loc_data["country"],
                application_url=j.get("absolute_url", ""),
                source_url=url,
                source_type="ATS",
                source_name="Greenhouse",
                raw_data=j
            )
            val_status, conf = validate_job(nj)
            nj.validation_status = val_status
            nj.extraction_confidence = conf
            nj.extraction_method = "Greenhouse API"
            
            normalized_jobs.append(nj)
            
        diagnostics.jobs_found = len(normalized_jobs)
        diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        return FetchResult(jobs=normalized_jobs, diagnostics=diagnostics)

    def _extract_token(self, url: str) -> str:
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        
        # https://boards.greenhouse.io/openai -> token is openai
        # https://boards-api.greenhouse.io/v1/boards/openai/jobs -> token is openai
        
        if "boards-api" in parsed.netloc:
            if "boards" in path_parts:
                idx = path_parts.index("boards")
                if len(path_parts) > idx + 1:
                    return path_parts[idx + 1]
        
        # embed check: https://boards.greenhouse.io/embed/job_board?for=openai
        if "embed" in path_parts:
            from urllib.parse import parse_qs
            qs = parse_qs(parsed.query)
            if "for" in qs:
                return qs["for"][0]
                
        # Normal check
        if path_parts:
            return path_parts[0]
            
        return ""

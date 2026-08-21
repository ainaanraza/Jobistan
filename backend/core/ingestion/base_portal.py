from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import sys
from urllib.parse import urlparse, parse_qs
from core.ingestion.base import JobSourceAdapter, FetchResult, IngestionDiagnostics, NormalizedJob
from core.ingestion.utils import validate_job, parse_location, parse_salary
from core.ai import extract_jobs_from_text

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

    def _default_fetch_jobs(self, url: str, portal_name: str, job_id_params: list[str]) -> FetchResult:
        from playwright.sync_api import sync_playwright
        
        start_time = time.time()
        
        diagnostics = IngestionDiagnostics(
            status="SUCCESS",
            adapter=self.__class__.__name__,
            http_status=None,
            extraction_method=f"{portal_name} Direct",
            jobs_found=0,
            execution_time_ms=0.0,
            errors=[],
            warnings=[],
            metadata={
                "parsed_config": self.parse_search_config(url)
            }
        )
        
        old_policy = None
        if sys.platform == 'win32':
            import asyncio
            old_policy = asyncio.get_event_loop_policy()
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
        page_text = ""
        links_text = ""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                try:
                    res = page.goto(url, wait_until="networkidle", timeout=30000)
                    if res:
                        diagnostics.http_status = res.status
                        content_lower = page.content().lower()
                        title_lower = page.title().lower()
                        is_blocked = (
                            res.status in (403, 429) or 
                            'access denied' in title_lower or 
                            'attention required! | cloudflare' in title_lower or
                            'please verify you are a human' in content_lower
                        )
                        if is_blocked:
                            diagnostics.status = "ACCESS_BLOCKED"
                            diagnostics.errors.append(f"{portal_name} access is blocked by anti-bot protections or rate limits.")
                            return FetchResult(jobs=[], diagnostics=diagnostics)
                except Exception as e:
                    diagnostics.errors.append(f"Playwright navigation error: {e}")
                    diagnostics.status = "FETCH_ERROR"
                    return FetchResult(jobs=[], diagnostics=diagnostics)
                
                time.sleep(2)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                
                page_text = page.evaluate('document.body.innerText')
                raw_links = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('a')).map(a => ({text: a.innerText.trim(), href: a.href}));
                }""")
                
                job_links = []
                for link in raw_links:
                    txt = link.get("text", "").lower()
                    href = link.get("href", "").lower()
                    if "job" in href or "view" in href or "clk" in href or "role" in href or "career" in href:
                        job_links.append(f"{link.get('text')} -> {link.get('href')}")
                
                links_text = "\n".join(job_links[:100])
                browser.close()
        except Exception as e:
            diagnostics.errors.append(f"Playwright execution error: {e}")
            diagnostics.status = "FETCH_ERROR"
            return FetchResult(jobs=[], diagnostics=diagnostics)
        finally:
            if sys.platform == 'win32' and old_policy is not None:
                import asyncio
                asyncio.set_event_loop_policy(old_policy)
                
        diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)

        if not page_text.strip():
            diagnostics.status = "EXTRACTION_ERROR"
            diagnostics.errors.append("No page content retrieved.")
            return FetchResult(jobs=[], diagnostics=diagnostics)

        diagnostics.extraction_method = "LLM"
        combined_content = f"PAGE TEXT:\n{page_text}\n\nPAGE LINKS:\n{links_text}"
        
        try:
            extracted = extract_jobs_from_text(combined_content, url, {"preferred_roles": "All"})
        except Exception as e:
            diagnostics.errors.append(f"LLM extraction failed: {e}")
            extracted = []
            
        if not extracted:
            diagnostics.status = "NO_JOBS_FOUND"
            diagnostics.warnings.append("LLM returned no jobs.")
            return FetchResult(jobs=[], diagnostics=diagnostics)
            
        normalized_jobs = []
        for idx, j in enumerate(extracted):
            loc_data = parse_location(j.get("location", ""))
            sal_data = parse_salary(j.get("salary_range", ""))
            
            job_url = j.get("job_url", url)
            if not job_url or job_url == "None" or job_url == "Undisclosed" or job_url.lower() == "null":
                job_url = url
                
            parsed_job_url = urlparse(job_url)
            qs = parse_qs(parsed_job_url.query)
            ext_id = None
            for param in job_id_params:
                if param in qs:
                    ext_id = qs[param][0]
                    break
            
            if not ext_id:
                ext_id = f"{portal_name.lower()}_{idx}"
                
            llm_confidence = float(j.get("confidence", 0.5))
            
            nj = NormalizedJob(
                external_id=ext_id,
                title=j.get("title", "Unknown Role"),
                company=j.get("company") or "Unknown Company",
                description=j.get("description", "Discovered via AI Scraper"),
                location=j.get("location", "Varies"),
                remote=loc_data["remote"] or "remote" in str(j.get("title", "")).lower(),
                hybrid=loc_data["hybrid"],
                city=loc_data["city"],
                state=loc_data["state"],
                country=loc_data["country"],
                salary_min=sal_data["salary_min"],
                salary_max=sal_data["salary_max"],
                currency=sal_data["currency"],
                salary_period=sal_data["period"],
                application_url=job_url,
                source_url=url,
                source_type="Job Portal",
                source_name=portal_name,
                raw_data=j
            )
            val_status, base_conf = validate_job(nj)
            nj.validation_status = val_status
            nj.extraction_confidence = (base_conf + llm_confidence) / 2.0
            nj.extraction_method = "LLM"
            
            normalized_jobs.append(nj)
            
        diagnostics.jobs_found = len(normalized_jobs)
        diagnostics.status = "SUCCESS" if normalized_jobs else "NO_JOBS_FOUND"
        return FetchResult(jobs=normalized_jobs, diagnostics=diagnostics)

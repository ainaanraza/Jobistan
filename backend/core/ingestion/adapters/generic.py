import json
import time
import sys
from typing import List, Dict, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re

from core.ingestion.base import JobSourceAdapter, NormalizedJob, FetchResult, IngestionDiagnostics
from core.ai import extract_jobs_from_text
from core.ingestion.utils import parse_salary, parse_location, validate_job

class GenericAdapter(JobSourceAdapter):
    @classmethod
    def can_handle(cls, url: str) -> bool:
        return True

    def fetch_jobs(self, url: str) -> FetchResult:
        from playwright.sync_api import sync_playwright
        
        diagnostics = IngestionDiagnostics(
            status="SUCCESS",
            adapter="GenericAdapter",
            http_status=None,
            extraction_method=None,
            jobs_found=0,
            execution_time_ms=0.0,
            errors=[],
            warnings=[],
            metadata={
                "page_load_time": 0.0,
                "javascript_used": True,
                "json_ld_found": 0,
                "embedded_json_found": 0,
                "network_api_detected": False,
                "job_links_found": 0,
                "llm_used": False,
                "network_endpoints": []
            }
        )
        
        page_html = ""
        page_text = ""
        links_text = ""
        
        start_time = time.time()

        old_policy = None
        if sys.platform == 'win32':
            import asyncio
            old_policy = asyncio.get_event_loop_policy()
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # Network Listener
                def handle_response(response):
                    try:
                        # Ignore common static assets
                        if response.request.resource_type in ["image", "stylesheet", "font", "media"]:
                            return
                            
                        # Look for JSON APIs
                        content_type = response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            url_lower = response.url.lower()
                            # Basic heuristic for job-like APIs
                            if any(k in url_lower for k in ["jobs", "graphql", "api", "careers", "search"]):
                                diagnostics.metadata["network_api_detected"] = True
                                diagnostics.metadata["network_endpoints"].append({
                                    "endpoint": response.url,
                                    "method": response.request.method,
                                    "status": response.status
                                })
                    except:
                        pass
                
                page.on("response", handle_response)
                
                try:
                    res = page.goto(url, wait_until="networkidle", timeout=30000)
                    if res:
                        diagnostics.http_status = res.status
                except Exception as e:
                    diagnostics.errors.append(f"Playwright navigation error: {e}")
                
                time.sleep(2)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                
                try:
                    page_html = page.content()
                    page_text = page.evaluate('document.body.innerText')
                    
                    # Get links that might be jobs
                    raw_links = page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('a')).map(a => ({text: a.innerText.trim(), href: a.href}));
                    }''')
                    
                    job_links = []
                    for link in raw_links:
                        txt = link.get("text", "").lower()
                        href = link.get("href", "").lower()
                        if any(k in txt or k in href for k in ["job", "career", "apply", "engineer", "manager", "developer"]):
                            job_links.append(f"{link.get('text')} -> {link.get('href')}")
                    
                    diagnostics.metadata["job_links_found"] = len(job_links)
                    links_text = "\\n".join(job_links[:50]) # Limit to 50 links
                    
                except Exception as e:
                    diagnostics.errors.append(f"Playwright evaluation error: {e}")
                
                browser.close()
        finally:
            if sys.platform == 'win32' and old_policy is not None:
                import asyncio
                asyncio.set_event_loop_policy(old_policy)

        diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        diagnostics.metadata["page_load_time"] = round(time.time() - start_time, 2)

        # 1. Try extracting JSON-LD JobPosting
        json_ld_jobs = self._extract_json_ld(page_html, url)
        diagnostics.metadata["json_ld_found"] = len(json_ld_jobs)
        
        if json_ld_jobs:
            diagnostics.extraction_method = "JSON-LD"
            diagnostics.jobs_found = len(json_ld_jobs)
            return FetchResult(jobs=json_ld_jobs, diagnostics=diagnostics)
            
        # 2. Try embedded JSON blocks (e.g. Next.js __NEXT_DATA__)
        embedded_jobs = self._extract_embedded_json(page_html, url)
        diagnostics.metadata["embedded_json_found"] = len(embedded_jobs)
        if embedded_jobs:
            diagnostics.extraction_method = "Embedded-JSON"
            diagnostics.jobs_found = len(embedded_jobs)
            return FetchResult(jobs=embedded_jobs, diagnostics=diagnostics)

        # 3. Fallback to LLM extraction
        diagnostics.metadata["llm_used"] = True
        diagnostics.extraction_method = "LLM"
        
        combined_content = f"PAGE TEXT:\\n{page_text}\\n\\nPAGE LINKS:\\n{links_text}"
        
        try:
            extracted = extract_jobs_from_text(combined_content, url, {"preferred_roles": "All"})
        except Exception as e:
            diagnostics.errors.append(f"LLM extraction failed: {e}")
            extracted = []
            
        if not extracted:
            diagnostics.warnings.append("LLM returned no jobs or failed.")
            return FetchResult(jobs=[], diagnostics=diagnostics)
            
        parsed_uri = urlparse(url)
        domain = f"{parsed_uri.netloc}"
        
        normalized_jobs = []
        for idx, j in enumerate(extracted):
            loc_data = parse_location(j.get("location", ""))
            sal_data = parse_salary(j.get("salary_range", ""))
            
            job_url = j.get("job_url", url)
            if not job_url or job_url == "None" or job_url == "Undisclosed" or job_url.lower() == "null":
                job_url = url
                
            # If the LLM returned a unique URL, try to extract an ID from it
            # Otherwise fallback to a generated ID
            parsed_job_url = urlparse(job_url)
            import urllib.parse as up
            qs = up.parse_qs(parsed_job_url.query)
            
            # Simple heuristic to find an ID in query string like ?job_id=6167
            ext_id = None
            for key, val in qs.items():
                if "id" in key.lower() and val:
                    ext_id = val[0]
                    break
            
            if not ext_id:
                path_parts = [p for p in parsed_job_url.path.split("/") if p]
                if path_parts:
                    ext_id = path_parts[-1]
            
            if not ext_id or ext_id == parsed_uri.netloc:
                ext_id = f"llm_{idx}"
                
            llm_confidence = float(j.get("confidence", 0.5))
            
            nj = NormalizedJob(
                external_id=ext_id,
                title=j.get("title", "Unknown Role"),
                company=j.get("company") or domain, # Use LLM extracted company
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
                source_type="Career Page",
                source_name=domain, # Generic portal domain
                raw_data=j
            )
            val_status, base_conf = validate_job(nj)
            nj.validation_status = val_status
            nj.extraction_confidence = (base_conf + llm_confidence) / 2.0 # Blend structural confidence with LLM confidence
            nj.extraction_method = "LLM"
            
            normalized_jobs.append(nj)
            
        diagnostics.jobs_found = len(normalized_jobs)
        return FetchResult(jobs=normalized_jobs, diagnostics=diagnostics)
        
    def _extract_json_ld(self, html_content: str, source_url: str) -> List[NormalizedJob]:
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all('script', type='application/ld+json')
        
        jobs = []
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    if item.get('@type') == 'JobPosting':
                        jobs.append(self._parse_json_ld_job(item, source_url))
            except Exception:
                pass
        return jobs
        
    def _extract_embedded_json(self, html_content: str, source_url: str) -> List[NormalizedJob]:
        # Very basic implementation to find __NEXT_DATA__
        soup = BeautifulSoup(html_content, 'html.parser')
        next_script = soup.find('script', id='__NEXT_DATA__')
        
        jobs = []
        if next_script and next_script.string:
            try:
                data = json.loads(next_script.string)
                # Attempt to find job objects in the sprawling JSON
                # A robust implementation would recursively search for common job fields
                # This is a placeholder for the diagnostic tracking
            except:
                pass
        return jobs
        
    def _parse_json_ld_job(self, item: Dict[str, Any], source_url: str) -> NormalizedJob:
        title = item.get("title", "Unknown Role")
        desc = item.get("description", "No description")
        
        company = "Unknown Company"
        hiring_org = item.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
            company = hiring_org.get("name", company)
            
        location = "Unknown"
        job_loc = item.get("jobLocation", {})
        if isinstance(job_loc, list) and len(job_loc) > 0:
            job_loc = job_loc[0]
        if isinstance(job_loc, dict):
            addr = job_loc.get("address", {})
            if isinstance(addr, dict):
                location = addr.get("addressLocality", "") + ", " + addr.get("addressRegion", "")
                
        posted_at = None
        if item.get("datePosted"):
            try:
                from dateutil import parser
                posted_at = parser.parse(item["datePosted"]).replace(tzinfo=None)
            except:
                pass
                
        # Use our new utilities for robust parsing
        sal_data = {"salary_min": None, "salary_max": None, "currency": None, "period": None}
        base_salary = item.get("baseSalary", {})
        if isinstance(base_salary, dict):
            val = base_salary.get("value", {})
            if isinstance(val, dict):
                sal_data["salary_min"] = val.get("minValue")
                sal_data["salary_max"] = val.get("maxValue")
            sal_data["currency"] = base_salary.get("currency")
            sal_data["period"] = base_salary.get("unitText") # Standard Schema.org field
            
        loc_data = parse_location(location)
            
        app_url = item.get("url", source_url)

        nj = NormalizedJob(
            external_id=str(item.get("identifier", {}).get("value", app_url)),
            title=title,
            company=company,
            description=desc,
            location=location.strip(", "),
            remote="TELECOMMUTE" in str(item.get("jobLocationType", "")).upper() or loc_data["remote"],
            hybrid=loc_data["hybrid"],
            city=loc_data["city"],
            state=loc_data["state"],
            country=loc_data["country"],
            employment_type=item.get("employmentType"),
            salary_min=sal_data["salary_min"],
            salary_max=sal_data["salary_max"],
            currency=sal_data["currency"],
            salary_period=sal_data["period"],
            posted_at=posted_at,
            application_url=app_url,
            source_url=source_url,
            source_type="JobPosting",
            source_name="JSON-LD",
            raw_data=item
        )
        
        val_status, conf = validate_job(nj)
        nj.validation_status = val_status
        nj.extraction_confidence = conf
        nj.extraction_method = "JSON-LD"
        
        return nj

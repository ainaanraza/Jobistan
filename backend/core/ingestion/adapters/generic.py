import json
import time
import sys
import uuid
from typing import List, Dict, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

from core.ingestion.base import JobSourceAdapter, NormalizedJob, FetchResult, IngestionDiagnostics
from core.ai import extract_jobs_from_text
from core.ingestion.utils import parse_salary, parse_location, validate_job
from core.extraction.rule_engine import RuleEngine
from core.extraction.rule_validator import RuleValidator
from core.extraction.scraper_health import ScraperHealthService, HealthState
from core.extraction.healing_engine import ScraperHealingService
from core.config import settings

class GenericAdapter(JobSourceAdapter):
    @classmethod
    def can_handle(cls, url: str) -> bool:
        return True

    def fetch_jobs(self, url: str, db=None, source_id=None, force_heal: bool = False) -> FetchResult:
        from playwright.sync_api import sync_playwright
        
        diagnostics = IngestionDiagnostics(
            status="SUCCESS",
            adapter="GenericAdapter",
            jobs_found=0,
            metadata={"network_endpoints": []}
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
                
                def handle_response(response):
                    try:
                        content_type = response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            url_lower = response.url.lower()
                            if any(k in url_lower for k in ["jobs", "graphql", "api", "careers", "search"]):
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
                    
                    raw_links = page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('a')).map(a => ({text: a.innerText.trim(), href: a.href}));
                    }''')
                    
                    job_links = [f"{l.get('text')} -> {l.get('href')}" for l in raw_links 
                                 if any(k in str(l.get("text")).lower() or k in str(l.get("href")).lower() 
                                        for k in ["job", "career", "apply", "engineer"])]
                    links_text = "\n".join(job_links[:50])
                    
                except Exception as e:
                    diagnostics.errors.append(f"Playwright evaluation error: {e}")
                
                browser.close()
        finally:
            if sys.platform == 'win32' and old_policy is not None:
                import asyncio
                asyncio.set_event_loop_policy(old_policy)

        diagnostics.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        parsed_uri = urlparse(url)
        domain = f"{parsed_uri.netloc}"

        # 1. JSON-LD
        json_ld_jobs = self._extract_json_ld(page_html, url)
        if json_ld_jobs:
            diagnostics.extraction_method = "JSON-LD"
            diagnostics.jobs_found = len(json_ld_jobs)
            return FetchResult(jobs=json_ld_jobs, diagnostics=diagnostics)
            
        # 2. Embedded JSON
        embedded_jobs = self._extract_embedded_json(page_html, url)
        if embedded_jobs:
            diagnostics.extraction_method = "Embedded-JSON"
            diagnostics.jobs_found = len(embedded_jobs)
            return FetchResult(jobs=embedded_jobs, diagnostics=diagnostics)

        # DB Setup for Rules
        active_rule = None
        if db and source_id:
            from models.scraper_rule import ScraperRule, RuleStatus
            active_rule = db.query(ScraperRule).filter_by(source_id=source_id, status=RuleStatus.ACTIVE).first()
            
        # 3. Active Scraper Rules
        rule_extracted_count = 0
        if active_rule:
            diagnostics.rule_version = active_rule.version
            try:
                from core.extraction.models import ScraperRuleSchema
                rule_schema = ScraperRuleSchema(**active_rule.rules_json)
                raw_records = RuleEngine.extract(page_html, url, rule_schema)
                rule_extracted_count = len(raw_records)
                
                is_valid, score, reasons = RuleValidator.validate_extracted_records(raw_records, url)
                diagnostics.validation_score = score
                
                if is_valid:
                    normalized_jobs = self._normalize_raw_records(raw_records, domain, url, "DETERMINISTIC_RULE", score)
                    diagnostics.extraction_method = "DETERMINISTIC_RULE"
                    diagnostics.jobs_found = len(normalized_jobs)
                    
                    active_rule.last_used_at = datetime.utcnow()
                    db.commit()
                    return FetchResult(jobs=normalized_jobs, diagnostics=diagnostics)
                else:
                    diagnostics.warnings.append(f"Active rule validation failed. Score: {score}")
            except Exception as e:
                diagnostics.errors.append(f"Active rule execution error: {e}")

        # 4. Scraper Health Detection
        previous_jobs = 10 # Ideally fetch from DB metrics
        health, health_reason = ScraperHealthService.evaluate(
            http_status=diagnostics.http_status,
            current_jobs=0,
            previous_jobs=previous_jobs,
            has_active_rule=bool(active_rule),
            rule_matched_elements=rule_extracted_count
        )
        diagnostics.health_status = health.value
        
        # 5. Self-Healing
        if (health == HealthState.BROKEN or force_heal) and db and source_id:
            diagnostics.healing_attempted = True
            try:
                proposed_schema = ScraperHealingService.propose_rule(page_html, url)
                raw_records = RuleEngine.extract(page_html, url, proposed_schema)
                
                is_valid, score, reasons = RuleValidator.validate_extracted_records(raw_records, url)
                
                if is_valid and score >= getattr(settings, 'HEALING_MIN_VALIDATION_SCORE', 0.85):
                    diagnostics.healing_status = "SUCCESS"
                    diagnostics.healing_reason = "Generated and validated new rules."
                    diagnostics.new_rule_version = active_rule.version + 1 if active_rule else 1
                    diagnostics.validation_score = score
                    
                    from models.scraper_rule import ScraperRule, RuleStatus
                    if active_rule:
                        active_rule.status = RuleStatus.ARCHIVED
                        
                    new_rule = ScraperRule(
                        source_id=source_id,
                        domain=domain,
                        version=diagnostics.new_rule_version,
                        status=RuleStatus.ACTIVE,
                        rules_json=proposed_schema.model_dump(),
                        validation_score=score,
                        created_by="gemini",
                        activated_at=datetime.utcnow(),
                        healing_attempt_id=str(uuid.uuid4())
                    )
                    db.add(new_rule)
                    db.commit()
                    
                    normalized_jobs = self._normalize_raw_records(raw_records, domain, url, "SELF_HEALED_RULE", score)
                    diagnostics.extraction_method = "SELF_HEALED_RULE"
                    diagnostics.jobs_found = len(normalized_jobs)
                    return FetchResult(jobs=normalized_jobs, diagnostics=diagnostics)
                else:
                    diagnostics.healing_status = "FAILED"
                    diagnostics.healing_reason = f"Proposed rule failed validation. Score: {score}. Reasons: {reasons}"
            except Exception as e:
                diagnostics.healing_status = "FAILED"
                diagnostics.healing_reason = f"Healing exception: {e}"

        # 6. LLM Extraction Fallback
        diagnostics.extraction_method = "LLM_FALLBACK"
        combined_content = f"PAGE TEXT:\n{page_text}\n\nPAGE LINKS:\n{links_text}"
        
        try:
            extracted = extract_jobs_from_text(combined_content, url, {"preferred_roles": "All"})
        except Exception as e:
            diagnostics.errors.append(f"LLM extraction failed: {e}")
            extracted = []
            
        if not extracted:
            diagnostics.warnings.append("LLM returned no jobs or failed.")
            return FetchResult(jobs=[], diagnostics=diagnostics)
            
        normalized_jobs = self._normalize_raw_records(extracted, domain, url, "LLM_FALLBACK", 0.5, is_llm=True)
        diagnostics.jobs_found = len(normalized_jobs)
        return FetchResult(jobs=normalized_jobs, diagnostics=diagnostics)

    def _normalize_raw_records(self, raw_records: List[Dict[str, Any]], domain: str, source_url: str, method: str, conf: float, is_llm=False) -> List[NormalizedJob]:
        normalized = []
        for idx, j in enumerate(raw_records):
            loc_data = parse_location(j.get("location", ""))
            sal_data = parse_salary(j.get("salary_range", "") if is_llm else j.get("salary", ""))
            
            job_url = j.get("application_url") or j.get("job_url") or source_url
            if job_url in ["None", "Undisclosed", "null"]:
                job_url = source_url
                
            parsed_job_url = urlparse(job_url)
            import urllib.parse as up
            qs = up.parse_qs(parsed_job_url.query)
            
            ext_id = None
            for key, val in qs.items():
                if "id" in key.lower() and val:
                    ext_id = val[0]
                    break
            
            if not ext_id:
                path_parts = [p for p in parsed_job_url.path.split("/") if p]
                if path_parts:
                    ext_id = path_parts[-1]
            
            if not ext_id or ext_id == domain:
                ext_id = f"job_{idx}"
                
            nj = NormalizedJob(
                external_id=ext_id,
                title=j.get("title", "Unknown Role"),
                company=j.get("company") or domain, 
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
                source_url=source_url,
                source_type="Career Page",
                source_name=domain,
                raw_data=j
            )
            val_status, base_conf = validate_job(nj)
            nj.validation_status = val_status
            nj.extraction_confidence = conf
            nj.extraction_method = method
            
            normalized.append(nj)
        return normalized

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
            except:
                pass
        return jobs
        
    def _extract_embedded_json(self, html_content: str, source_url: str) -> List[NormalizedJob]:
        soup = BeautifulSoup(html_content, 'html.parser')
        next_script = soup.find('script', id='__NEXT_DATA__')
        jobs = []
        if next_script and next_script.string:
            try:
                data = json.loads(next_script.string)
            except:
                pass
        return jobs
        
    def _parse_json_ld_job(self, item: Dict[str, Any], source_url: str) -> NormalizedJob:
        title = item.get("title", "Unknown Role")
        desc = item.get("description", "No description")
        company = item.get("hiringOrganization", {}).get("name", "Unknown Company") if isinstance(item.get("hiringOrganization"), dict) else "Unknown"
        location = "Unknown"
        job_loc = item.get("jobLocation", {})
        if isinstance(job_loc, list) and len(job_loc) > 0:
            job_loc = job_loc[0]
        if isinstance(job_loc, dict):
            addr = job_loc.get("address", {})
            if isinstance(addr, dict):
                location = addr.get("addressLocality", "") + ", " + addr.get("addressRegion", "")
        
        sal_data = {"salary_min": None, "salary_max": None, "currency": None, "period": None}
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

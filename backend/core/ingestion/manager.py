from typing import List, Dict, Any
from core.ingestion.base import JobSourceAdapter, NormalizedJob, FetchResult, IngestionDiagnostics
from core.ingestion.adapters.greenhouse import GreenhouseAdapter
from core.ingestion.adapters.lever import LeverAdapter
from core.ingestion.adapters.ashby import AshbyAdapter
from core.ingestion.adapters.generic import GenericAdapter
from core.ingestion.adapters.indeed import IndeedAdapter
from core.ingestion.adapters.linkedin import LinkedInAdapter
from core.ingestion.adapters.glassdoor import GlassdoorAdapter
from core.ingestion.adapters.ziprecruiter import ZipRecruiterAdapter
from core.ingestion.adapters.careerbuilder import CareerBuilderAdapter
from core.ingestion.adapters.naukri import NaukriAdapter
from core.ingestion.adapters.foundit import FounditAdapter
from core.ingestion.adapters.apna import ApnaAdapter
from core.ingestion.adapters.shine import ShineAdapter
from core.ingestion.adapters.timesjobs import TimesJobsAdapter
from core.ingestion.adapters.workindia import WorkIndiaAdapter
from core.ingestion.adapters.instahyre import InstahyreAdapter
from core.ingestion.adapters.wellfound import WellfoundAdapter
from core.ingestion.adapters.flexjobs import FlexJobsAdapter
from core.ingestion.adapters.internshala import InternshalaAdapter
import hashlib
import json
import datetime
from sqlalchemy.orm import Session
from models.job_source import JobSource
from models.job import Job

class IngestionManager:
    def __init__(self):
        # Register adapters in order of preference
        self.adapters: List[JobSourceAdapter] = [
            IndeedAdapter(),
            LinkedInAdapter(),
            GlassdoorAdapter(),
            ZipRecruiterAdapter(),
            CareerBuilderAdapter(),
            NaukriAdapter(),
            FounditAdapter(),
            ApnaAdapter(),
            ShineAdapter(),
            TimesJobsAdapter(),
            WorkIndiaAdapter(),
            InstahyreAdapter(),
            WellfoundAdapter(),
            FlexJobsAdapter(),
            InternshalaAdapter(),
            GreenhouseAdapter(),
            LeverAdapter(),
            AshbyAdapter(),
            GenericAdapter() # Always last
        ]

    def get_adapter(self, url: str) -> JobSourceAdapter:
        for adapter in self.adapters:
            if adapter.can_handle(url):
                return adapter
        return self.adapters[-1] # Fallback to generic

    def compute_content_hash(self, jobs: List[NormalizedJob]) -> str:
        # Hash external IDs, updated_ats, and core content to detect changes even if updated_at is missing
        identifiers = [
            f"{j.external_id}_{j.updated_at or ''}_{j.title}_{hashlib.md5((j.description or '').encode()).hexdigest()[:8]}_{j.location}_{j.salary_min or ''}_{j.salary_max or ''}" 
            for j in jobs
        ]
        identifiers.sort()
        raw = "|".join(identifiers)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def fetch_source(self, url: str) -> FetchResult:
        adapter = self.get_adapter(url)
        return adapter.fetch_jobs(url)

    def process_source(self, db: Session, source: JobSource) -> Dict[str, Any]:
        """
        Fetches the source, computes hashes, and updates DB jobs.
        Returns a summary dictionary for tracking.
        """
        summary = {
            "url": source.url,
            "detected_platform": "Unknown",
            "jobs_found": 0,
            "new": 0,
            "updated": 0,
            "removed": 0,
            "status": "SUCCESS",
            "error": None,
            "warnings": [],
            "validation_count": {"VALID": 0, "WARNING": 0, "INVALID": 0},
            "diagnostics": {}
        }

        try:
            result = self.fetch_source(source.url)
            jobs = result.jobs
            diagnostics = result.diagnostics.model_dump()
            
            summary["detected_platform"] = result.diagnostics.adapter
            summary["jobs_found"] = len(jobs)
            summary["diagnostics"] = diagnostics
            summary["status"] = result.diagnostics.status
            
            if not jobs and summary["status"] == "SUCCESS":
                summary["status"] = "NO_JOBS_FOUND"
            
            new_hash = self.compute_content_hash(jobs)
            
            if source.content_hash == new_hash and jobs:
                # No changes detected, skip DB processing
                source.last_checked_at = datetime.datetime.utcnow()
                source.last_success_at = datetime.datetime.utcnow()
                db.commit()
                return summary

            # Process changes
            existing_jobs = db.query(Job).filter(Job.source_url == source.url, Job.is_active == True).all()
            existing_job_map = {j.external_id or j.job_url: j for j in existing_jobs}
            
            found_ids = set()
            
            for nj in jobs:
                # Fallback to application_url if external_id is missing
                ident = nj.external_id or nj.application_url
                found_ids.add(ident)
                
                # Validation logic here? No, done by generic/adapters or we can do it here:
                # Actually, adapters should set validation status. Let's assume nj has it set.
                if hasattr(nj, "validation_status") and nj.validation_status:
                    if nj.validation_status in summary["validation_count"]:
                        summary["validation_count"][nj.validation_status] += 1
                
                if ident in existing_job_map:
                    # Update existing
                    existing_job = existing_job_map[ident]
                    has_changed = False
                    
                    if existing_job.title != nj.title:
                        existing_job.title = nj.title
                        has_changed = True
                    if existing_job.description != nj.description:
                        existing_job.description = nj.description
                        has_changed = True
                    if existing_job.location != nj.location:
                        existing_job.location = nj.location
                        has_changed = True
                    
                    new_salary_range = f"{nj.currency or '$'}{nj.salary_min or ''}-{nj.salary_max or ''}" if nj.salary_min else existing_job.salary_range
                    if existing_job.salary_range != new_salary_range:
                        existing_job.salary_range = new_salary_range
                        has_changed = True

                    if existing_job.job_url != nj.application_url:
                        existing_job.job_url = nj.application_url
                        has_changed = True
                        
                    # Always update last_seen
                    existing_job.last_seen_at = datetime.datetime.utcnow()
                    
                    if has_changed:
                        existing_job.last_changed_at = datetime.datetime.utcnow()
                        summary["updated"] += 1
                else:
                    # Create new
                    new_job = Job(
                        title=nj.title,
                        description=nj.description,
                        location=nj.location,
                        salary_range=f"{nj.currency or '$'}{nj.salary_min or ''}-{nj.salary_max or ''}" if nj.salary_min else None,
                        job_url=nj.application_url,
                        external_id=nj.external_id,
                        remote=nj.remote,
                        employment_type=nj.employment_type,
                        salary_min=nj.salary_min,
                        salary_max=nj.salary_max,
                        currency=nj.currency,
                        salary_period=nj.salary_period,
                        city=nj.city,
                        state=nj.state,
                        country=nj.country,
                        hybrid=nj.hybrid,
                        extraction_confidence=nj.extraction_confidence,
                        validation_status=nj.validation_status,
                        extraction_method=nj.extraction_method,
                        posted_at=nj.posted_at,
                        updated_at=nj.updated_at,
                        source_url=nj.source_url,
                        source_type=nj.source_type,
                        source_name=nj.source_name,
                        raw_data=nj.raw_data,
                        is_active=True
                    )
                    db.add(new_job)
                    summary["new"] += 1

            # Detect removed jobs
            for ej in existing_jobs:
                ident = ej.external_id or ej.job_url
                if ident not in found_ids:
                    ej.is_active = False
                    summary["removed"] += 1
                    
            source.content_hash = new_hash
            source.last_checked_at = datetime.datetime.utcnow()
            source.last_success_at = datetime.datetime.utcnow()
            source.last_error = None
            db.commit()

        except Exception as e:
            summary["status"] = "ERROR"
            summary["error"] = str(e)
            source.last_checked_at = datetime.datetime.utcnow()
            source.last_error = str(e)
            db.commit()

        return summary

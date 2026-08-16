import re
import difflib
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models.job import Job
from models.canonical_job import CanonicalJob
import datetime

class DeduplicationService:
    def __init__(self, db: Session):
        self.db = db
        
    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        # Lowercase, remove special characters, remove extra whitespace
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return re.sub(r'\s+', ' ', text).strip()
        
    def find_match(self, job: Job) -> Optional[CanonicalJob]:
        """Finds an existing CanonicalJob that matches the given Job."""
        
        # 1. Exact external_id match (only if it's reliable like an ATS ID, skip for scraped generic sites)
        if job.external_id and job.source_type == "ATS":
            # Some sources prepend company to external_id, but assuming it's globally unique per source for now
            # Better: check if any CanonicalJob has a child job with this external_id from this source
            existing_child = self.db.query(Job).filter(
                Job.external_id == job.external_id,
                Job.source_url == job.source_url, # Same board
                Job.canonical_job_id != None,
                Job.id != job.id
            ).first()
            if existing_child and existing_child.canonical_job:
                return existing_child.canonical_job
                
        # 2. Exact application_url match
        if job.application_url:
            existing_child = self.db.query(Job).filter(
                Job.application_url == job.application_url,
                Job.canonical_job_id != None,
                Job.id != job.id
            ).first()
            if existing_child and existing_child.canonical_job:
                return existing_child.canonical_job
                
        # 3. Company + Normalized Title + Location string matching
        norm_company = self._normalize_text(job.company_name or "")
        norm_title = self._normalize_text(job.title)
        
        # Only compare against active canonical jobs from the same normalized company
        # We fetch potential candidates based on company name
        candidates = self.db.query(CanonicalJob).filter(
            CanonicalJob.is_active == True
        ).all() # In production, filter by company name locally or via DB ILIKE
        
        candidates = [c for c in candidates if self._normalize_text(c.company_name) == norm_company]
        
        for candidate in candidates:
            c_norm_title = self._normalize_text(candidate.title)
            c_norm_loc = self._normalize_text(candidate.location or "")
            j_norm_loc = self._normalize_text(job.location or "")
            
            # If title is exactly the same and location is same
            if norm_title == c_norm_title and c_norm_loc == j_norm_loc:
                return candidate
                
            # 4. Description similarity
            # If company and title are very close, check description similarity
            title_ratio = difflib.SequenceMatcher(None, norm_title, c_norm_title).ratio()
            if title_ratio > 0.8:
                desc_ratio = difflib.SequenceMatcher(None, job.description[:1000], candidate.description[:1000]).ratio()
                if desc_ratio > 0.90:
                    return candidate

        return None

    def create_canonical_from_job(self, job: Job) -> CanonicalJob:
        cj = CanonicalJob(
            company_name=job.company_name or "Unknown",
            company_url=job.company_url,
            title=job.title,
            description=job.description,
            location=job.location,
            remote=job.remote,
            hybrid=job.hybrid,
            employment_type=job.employment_type,
            seniority=job.seniority,
            role_category=job.role_category,
            skills=job.skills,
            experience_min=job.experience_min,
            experience_max=job.experience_max,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            currency=job.currency,
            salary_period=job.salary_period,
            city=job.city,
            state=job.state,
            country=job.country,
            best_application_url=job.application_url or job.job_url,
            is_active=True
        )
        self.db.add(cj)
        self.db.flush() # Get ID
        return cj

    def deduplicate_job(self, job: Job) -> CanonicalJob:
        """Process a single job to find its canonical parent, or create one."""
        match = self.find_match(job)
        if match:
            job.canonical_job_id = match.id
            # Merge some data if needed, e.g. update best_application_url
            if job.application_url and not match.best_application_url:
                match.best_application_url = job.application_url
            return match
        else:
            cj = self.create_canonical_from_job(job)
            job.canonical_job_id = cj.id
            return cj

    def process_unlinked_jobs(self):
        """Batch process all jobs that don't have a canonical_job_id yet."""
        unlinked_jobs = self.db.query(Job).filter(Job.canonical_job_id == None).all()
        for job in unlinked_jobs:
            self.deduplicate_job(job)
        self.db.commit()

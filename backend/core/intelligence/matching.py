import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.user_profile import UserProfile
from models.canonical_job import CanonicalJob
from models.job_match import JobMatch
from core.ai import generate_embedding
import numpy as np

class JobMatchingService:
    def __init__(self, db: Session):
        self.db = db
        
    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        return re.sub(r'[^a-z0-9\s]', '', text).strip()
        
    def _cosine_similarity(self, v1, v2):
        if v1 is None or v2 is None:
            return 0.0
        v1_arr = np.array(v1)
        v2_arr = np.array(v2)
        if np.linalg.norm(v1_arr) == 0 or np.linalg.norm(v2_arr) == 0:
            return 0.0
        return np.dot(v1_arr, v2_arr) / (np.linalg.norm(v1_arr) * np.linalg.norm(v2_arr))

    def score_skills(self, profile: UserProfile, job: CanonicalJob) -> float:
        if not profile.skills or not job.skills:
            return 0.5 # Neutral if unknown
            
        p_skills = set([self._normalize_text(s) for s in profile.skills])
        j_skills = set([self._normalize_text(s) for s in job.skills])
        
        if not j_skills:
            return 0.5
            
        # Intersection over job skills (how many of the job's skills does the user have)
        overlap = len(p_skills.intersection(j_skills))
        return overlap / len(j_skills)
        
    def score_role(self, profile: UserProfile, job: CanonicalJob) -> float:
        if not profile.preferred_roles:
            return 0.5
            
        p_roles = [self._normalize_text(r) for r in profile.preferred_roles]
        j_title = self._normalize_text(job.title)
        
        # Exact match
        for pr in p_roles:
            if pr in j_title:
                return 1.0
                
        # Sub-string match
        for pr in p_roles:
            words = pr.split()
            if any(w in j_title for w in words if len(w) > 3):
                return 0.8
                
        # If we have embeddings, we could use them, but let's stick to text for now
        # Fallback to embedding similarity if profile embedding and job embedding exist
        if profile.profile_embedding is not None and job.embedding is not None:
            sim = self._cosine_similarity(profile.profile_embedding, job.embedding)
            return max(0.0, float(sim))
            
        return 0.0

    def score_experience(self, profile: UserProfile, job: CanonicalJob) -> float:
        if profile.experience is None:
            return 0.5
            
        p_exp = profile.experience
        
        j_min = job.experience_min
        j_max = job.experience_max
        
        if j_min is None and j_max is None:
            return 0.5
            
        if j_min is not None and j_max is not None:
            if j_min <= p_exp <= j_max:
                return 1.0
            if p_exp < j_min:
                return max(0.0, 1.0 - (j_min - p_exp) * 0.2)
            if p_exp > j_max:
                return max(0.0, 1.0 - (p_exp - j_max) * 0.1) # Being overqualified is less penalizing
                
        if j_min is not None:
            if p_exp >= j_min:
                return 1.0
            return max(0.0, 1.0 - (j_min - p_exp) * 0.2)
            
        if j_max is not None:
            if p_exp <= j_max:
                return 1.0
            return max(0.0, 1.0 - (p_exp - j_max) * 0.1)
            
        return 0.5

    def score_location(self, profile: UserProfile, job: CanonicalJob) -> float:
        if profile.remote_preference and job.remote:
            return 1.0
            
        if not profile.preferred_locations:
            return 0.5
            
        if not job.location:
            return 0.5
            
        p_locs = [self._normalize_text(l) for l in profile.preferred_locations]
        j_loc = self._normalize_text(job.location)
        
        for pl in p_locs:
            if pl in j_loc or j_loc in pl:
                return 1.0
                
        return 0.0

    def score_salary(self, profile: UserProfile, job: CanonicalJob) -> float:
        if not profile.salary_preferences or 'min' not in profile.salary_preferences:
            return 0.5
            
        p_min = profile.salary_preferences.get('min')
        
        if job.salary_min is None and job.salary_max is None:
            return 0.5
            
        # Simple overlap check
        if job.salary_max and job.salary_max < p_min:
            return 0.0 # Dealbreaker
            
        if job.salary_min and job.salary_min >= p_min:
            return 1.0
            
        return 0.8 # Some overlap

    def calculate_match(self, profile: UserProfile, job: CanonicalJob) -> JobMatch:
        match = self.db.query(JobMatch).filter(
            JobMatch.user_id == profile.user_id,
            JobMatch.canonical_job_id == job.id
        ).first()
        
        if not match:
            match = JobMatch(user_id=profile.user_id, canonical_job_id=job.id)
            self.db.add(match)
            
        match.skill_match = self.score_skills(profile, job)
        match.role_match = self.score_role(profile, job)
        match.experience_match = self.score_experience(profile, job)
        match.location_match = self.score_location(profile, job)
        match.salary_match = self.score_salary(profile, job)
        
        # Weights
        w_skill = 0.35
        w_role = 0.35
        w_exp = 0.15
        w_loc = 0.10
        w_sal = 0.05
        
        total_score = (
            match.skill_match * w_skill +
            match.role_match * w_role +
            match.experience_match * w_exp +
            match.location_match * w_loc +
            match.salary_match * w_sal
        ) * 100.0
        
        match.match_score = min(100.0, max(0.0, total_score))
        self.db.commit()
        return match
        
    def batch_calculate_matches(self, profile: UserProfile, active_only: bool = True):
        query = self.db.query(CanonicalJob)
        if active_only:
            query = query.filter(CanonicalJob.is_active == True)
            
        jobs = query.all()
        for job in jobs:
            self.calculate_match(profile, job)

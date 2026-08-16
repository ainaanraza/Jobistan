import json
from sqlalchemy.orm import Session
from models.user_profile import UserProfile
from models.canonical_job import CanonicalJob
from models.job_match import JobMatch
from core.config import settings
from google import genai

class ExplanationService:
    def __init__(self, db: Session):
        self.db = db
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY) if settings.GOOGLE_API_KEY else None

    def generate_explanation(self, profile: UserProfile, job: CanonicalJob, match: JobMatch):
        """Generates human-readable match reasons using Gemini based on deterministic scores."""
        if not self.client:
            match.match_reasons = [{"reason": "API Key missing for AI explanation."}]
            self.db.commit()
            return
            
        prompt = (
            "You are a job matching assistant. Based on the following deterministic scores, "
            "generate exactly 3-5 short, punchy reasons why this job is a match (or mismatch) for the user.\n\n"
            f"Job Title: {job.title}\n"
            f"Company: {job.company_name}\n"
            f"User Preferred Roles: {profile.preferred_roles}\n"
            f"User Skills: {profile.skills}\n"
            f"Job Skills: {job.skills}\n"
            f"Overall Score: {match.match_score:.1f}/100\n"
            f"Skill Match Score: {match.skill_match:.2f}\n"
            f"Role Match Score: {match.role_match:.2f}\n"
            f"Experience Match Score: {match.experience_match:.2f}\n"
            f"Location Match Score: {match.location_match:.2f}\n\n"
            "Output the reasons as a raw JSON array of strings ONLY. No markdown wrapping."
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            reasons = json.loads(response_text.strip())
            if isinstance(reasons, list):
                match.match_reasons = [{"reason": r} for r in reasons]
            else:
                match.match_reasons = [{"reason": "Strong overall match."}]
                
        except Exception as e:
            print(f"Failed to generate explanation: {e}")
            match.match_reasons = [{"reason": f"System determined a score of {match.match_score:.0f}%"}]
            
        self.db.commit()

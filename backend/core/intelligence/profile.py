from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models.user import User
from models.user_profile import UserProfile
from core.ai import generate_embedding

class UserProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_profile(self, user_id: int) -> UserProfile:
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def update_profile(self, user_id: int, profile_data: Dict[str, Any]) -> UserProfile:
        profile = self.get_or_create_profile(user_id)
        
        # Update scalar/JSON fields
        if "skills" in profile_data:
            profile.skills = profile_data["skills"]
        if "preferred_roles" in profile_data:
            profile.preferred_roles = profile_data["preferred_roles"]
        if "preferred_locations" in profile_data:
            profile.preferred_locations = profile_data["preferred_locations"]
        if "experience" in profile_data:
            profile.experience = profile_data["experience"]
        if "education" in profile_data:
            profile.education = profile_data["education"]
        if "salary_preferences" in profile_data:
            profile.salary_preferences = profile_data["salary_preferences"]
        if "remote_preference" in profile_data:
            profile.remote_preference = profile_data["remote_preference"]
            
        self.db.commit()
        
        # Generate embedding based on combined profile text
        self._generate_embedding(profile)
        
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def _generate_embedding(self, profile: UserProfile):
        """Generates an embedding for the user's professional profile using core.ai"""
        parts = []
        if profile.skills:
            parts.append(f"Skills: {', '.join(profile.skills)}")
        if profile.preferred_roles:
            parts.append(f"Preferred Roles: {', '.join(profile.preferred_roles)}")
        if profile.experience is not None:
            parts.append(f"Experience: {profile.experience} years")
        if profile.education:
            parts.append(f"Education: {profile.education}")
        if profile.preferred_locations:
            parts.append(f"Locations: {', '.join(profile.preferred_locations)}")
        if profile.remote_preference:
            parts.append("Prefers Remote Work")
            
        if not parts:
            profile.profile_embedding = None
            return
            
        profile_text = "\n".join(parts)
        
        # Call Google GenAI for embedding
        embedding = generate_embedding(profile_text)
        if embedding and len(embedding) > 0:
            profile.profile_embedding = embedding

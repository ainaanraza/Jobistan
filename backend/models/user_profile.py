from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from db.base_class import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    skills = Column(JSON, nullable=True) # list of skills
    preferred_roles = Column(JSON, nullable=True) # list of roles
    preferred_locations = Column(JSON, nullable=True) # list of locations
    experience = Column(Integer, nullable=True) # years of experience
    education = Column(String, nullable=True) # education level
    
    salary_preferences = Column(JSON, nullable=True) # {"min": int, "currency": str}
    remote_preference = Column(Boolean, default=False)
    
    # We use 1536 dimensions for OpenAI embeddings (text-embedding-3-small/ada-002)
    profile_embedding = Column(Vector(1536), nullable=True)

    user = relationship("User", backref="profile_data")

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, Boolean, DateTime, JSON
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
import datetime
from db.base_class import Base

class CanonicalJob(Base):
    __tablename__ = "canonical_jobs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Core Data
    company_name = Column(String, index=True, nullable=False)
    company_url = Column(String, nullable=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=True)
    
    # Normalized Fields
    remote = Column(Boolean, default=False)
    hybrid = Column(Boolean, default=False)
    employment_type = Column(String, nullable=True)
    seniority = Column(String, nullable=True)
    role_category = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)
    
    experience_min = Column(Integer, nullable=True)
    experience_max = Column(Integer, nullable=True)
    
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    salary_period = Column(String, nullable=True)
    
    # Granular Location
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    # Timestamps
    first_seen_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Best Application URL (e.g. from the most reliable source)
    best_application_url = Column(String, nullable=True)
    
    # We use 1536 dimensions for OpenAI embeddings (text-embedding-3-small/ada-002)
    embedding = Column(Vector(1536), nullable=True) 

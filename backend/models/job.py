from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, Boolean, DateTime, JSON
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
import datetime
from db.base_class import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=True)
    salary_range = Column(String, nullable=True)
    job_url = Column(String, unique=True, nullable=False)
    
    # Normalized Fields
    external_id = Column(String, nullable=True, index=True)
    remote = Column(Boolean, default=False)
    employment_type = Column(String, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    salary_period = Column(String, nullable=True)
    
    # Granular Location
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    hybrid = Column(Boolean, default=False)
    
    # Confidence and Validation
    extraction_confidence = Column(Float, nullable=True)
    validation_status = Column(String, nullable=True)
    extraction_method = Column(String, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    source_url = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    source_name = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)

    # Tracking Fields
    first_seen_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=True)
    last_changed_at = Column(DateTime, nullable=True)
    content_hash = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Added Intelligence Fields
    company_name = Column(String, nullable=True)
    company_url = Column(String, nullable=True)
    seniority = Column(String, nullable=True)
    role_category = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)
    experience_min = Column(Integer, nullable=True)
    experience_max = Column(Integer, nullable=True)
    application_url = Column(String, nullable=True)
    
    canonical_job_id = Column(Integer, ForeignKey("canonical_jobs.id"), nullable=True)
    
    # We use 1536 dimensions for OpenAI embeddings (text-embedding-3-small/ada-002)
    embedding = Column(Vector(1536), nullable=True) 

    company = relationship("Company", backref="jobs")
    canonical_job = relationship("CanonicalJob", backref="source_jobs")

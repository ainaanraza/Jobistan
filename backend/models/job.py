from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
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
    
    # We use 1536 dimensions for OpenAI embeddings (text-embedding-3-small)
    # or 768 for Gemini embeddings (text-embedding-004)
    # Let's use 768 since Gemini is free as per user request
    embedding = Column(Vector(768), nullable=True) 

    company = relationship("Company", backref="jobs")

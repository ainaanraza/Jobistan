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
    
    # We use 1536 dimensions for OpenAI embeddings (text-embedding-3-small/ada-002)
    embedding = Column(Vector(1536), nullable=True) 

    company = relationship("Company", backref="jobs")

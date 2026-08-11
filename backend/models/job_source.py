from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from db.base_class import Base

class SourceType(str, enum.Enum):
    company_career_page = "company_career_page"
    job_portal = "job_portal"
    direct_url = "direct_url"

class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    url = Column(String)
    source_type = Column(String) # Storing as string for simplicity, can cast to Enum in Pydantic
    is_active = Column(Boolean, default=True)

    user = relationship("User", backref="job_sources")

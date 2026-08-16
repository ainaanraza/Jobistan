from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime, JSON
from sqlalchemy.orm import relationship
import enum
from db.base_class import Base

class SourceType(str, enum.Enum):
    ATS = "ATS"
    CAREER_PAGE = "CAREER_PAGE"
    DIRECT_JOB = "DIRECT_JOB"
    JOB_PORTAL = "JOB_PORTAL"
    SEARCH_ENGINE = "SEARCH_ENGINE"

class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    url = Column(String)
    source_type = Column(String)
    is_active = Column(Boolean, default=True)

    # New fields for ingestion tracking
    crawl_frequency = Column(Integer, default=14400) # seconds (e.g. 4 hours)
    last_checked_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error = Column(String, nullable=True)
    etag = Column(String, nullable=True)
    last_modified = Column(String, nullable=True)
    content_hash = Column(String, nullable=True)
    configuration = Column(JSON, nullable=True)

    user = relationship("User", backref="job_sources")

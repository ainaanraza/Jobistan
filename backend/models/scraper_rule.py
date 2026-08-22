from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from db.base_class import Base

class RuleStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    TESTING = "TESTING"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

class ScraperRule(Base):
    __tablename__ = "scraper_rules"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("job_sources.id"), index=True, nullable=False)
    domain = Column(String, index=True, nullable=True) # Metadata, source_id is primary
    version = Column(Integer, nullable=False)
    status = Column(String, default=RuleStatus.TESTING)
    rules_json = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)
    validation_score = Column(Float, nullable=True)
    
    healing_attempt_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    created_by = Column(String, nullable=True) # E.g., 'gemini', 'user', 'system'
    failure_reason = Column(String, nullable=True)

    source = relationship("JobSource", backref="scraper_rules")

    __table_args__ = (
        UniqueConstraint('source_id', 'version', name='uix_source_id_version'),
    )

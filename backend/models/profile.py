from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.base_class import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    phone = Column(String, nullable=True)
    resume_url = Column(String, nullable=True)
    skills = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    preferred_roles = Column(String, nullable=True)
    preferred_locations = Column(String, nullable=True)
    salary_expectations = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)
    college = Column(String, nullable=True)
    school = Column(String, nullable=True)
    city = Column(String, nullable=True)
    projects = Column(Text, nullable=True)

    user = relationship("User", backref="profile")

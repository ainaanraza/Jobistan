from sqlalchemy import Column, Integer, String, Text
from db.base_class import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    website_url = Column(String, nullable=True)
    career_page_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    industry = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)

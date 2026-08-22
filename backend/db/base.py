from db.base_class import Base

# Import all models here for Alembic to auto-discover them
from models.user import User
from models.profile import Profile
from models.company import Company
from models.job import Job
from models.employee import EmployeeProfile
from models.job_source import JobSource
from models.application import Application
from models.canonical_job import CanonicalJob
from models.user_profile import UserProfile
from models.job_match import JobMatch
from models.scraper_rule import ScraperRule
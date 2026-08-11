from typing import List, Optional
from sqlalchemy.orm import Session
from models.job import Job
from models.company import Company

def get_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[Job]:
    # Query jobs and eagerly load company relationship
    return db.query(Job).order_by(Job.id.desc()).offset(skip).limit(limit).all()

def seed_mock_data(db: Session):
    # Check if we already have jobs
    if db.query(Job).count() > 0:
        return
    
    # Create companies if they don't exist
    google = db.query(Company).filter(Company.name == "Google").first()
    if not google:
        google = Company(
            name="Google",
            website_url="https://google.com",
            description="Organize the world's information and make it universally accessible and useful."
        )
        db.add(google)

    meta = db.query(Company).filter(Company.name == "Meta").first()
    if not meta:
        meta = Company(
            name="Meta",
            website_url="https://meta.com",
            description="Giving people the power to build community and bring the world closer together."
        )
        db.add(meta)

    stripe = db.query(Company).filter(Company.name == "Stripe").first()
    if not stripe:
        stripe = Company(
            name="Stripe",
            website_url="https://stripe.com",
            description="Financial infrastructure for the internet."
        )
        db.add(stripe)
    
    db.commit()
    db.refresh(google)
    db.refresh(meta)
    db.refresh(stripe)

    # Seed Jobs
    jobs_data = [
        {
            "title": "Senior Full Stack Engineer",
            "company_id": google.id,
            "location": "Remote",
            "salary_range": "$180k - $250k",
            "job_url": "https://careers.google.com/jobs/results/senior-full-stack",
            "description": "Develop and launch complex, user-facing features on Google Search and Cloud platforms using React and Python."
        },
        {
            "title": "React Developer",
            "company_id": meta.id,
            "location": "Menlo Park, CA",
            "salary_range": "$160k - $210k",
            "job_url": "https://careers.facebook.com/jobs/react-dev",
            "description": "Design and build the next generation of user experiences across Meta's family of apps using React and modern frontend tech."
        },
        {
            "title": "Backend Software Engineer",
            "company_id": stripe.id,
            "location": "Remote",
            "salary_range": "$170k - $220k",
            "job_url": "https://careers.stripe.com/jobs/backend-eng",
            "description": "Scale and improve APIs and systems that process hundreds of billions of dollars of transactions yearly. FastAPI / Python experience a plus."
        }
    ]

    for job_info in jobs_data:
        job = Job(
            title=job_info["title"],
            company_id=job_info["company_id"],
            location=job_info["location"],
            salary_range=job_info["salary_range"],
            job_url=job_info["job_url"],
            description=job_info["description"]
        )
        db.add(job)
    
    db.commit()

def create_job(db: Session, job_data: dict, embedding: List[float] = None) -> Optional[Job]:
    # Check if job already exists by URL
    existing_job = db.query(Job).filter(Job.job_url == job_data["job_url"]).first()
    if existing_job:
        return existing_job
        
    company_name = job_data.get("company") or "Unknown"
    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        company = Company(name=company_name)
        db.add(company)
        db.commit()
        db.refresh(company)
        
    job = Job(
        title=job_data.get("title", ""),
        company_id=company.id,
        location=job_data.get("location", ""),
        salary_range=job_data.get("salary_range", ""),
        job_url=job_data.get("job_url", ""),
        description=job_data.get("description", ""),
        embedding=embedding
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def search_jobs_semantically(db: Session, profile_embedding: List[float], limit: int = 100):
    """
    Returns jobs ordered by cosine distance to the given profile_embedding.
    """
    distance_col = Job.embedding.cosine_distance(profile_embedding).label("distance")
    results = (
        db.query(Job, distance_col)
        .filter(Job.embedding.isnot(None))
        .order_by(distance_col)
        .limit(limit)
        .all()
    )
    return results

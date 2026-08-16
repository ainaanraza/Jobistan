import pytest
from sqlalchemy.orm import Session
from models.user import User
from models.user_profile import UserProfile
from models.job import Job
from models.canonical_job import CanonicalJob
from models.job_match import JobMatch
from core.intelligence.deduplication import DeduplicationService
from core.intelligence.matching import JobMatchingService
from core.intelligence.ranking import RankingService
from core.intelligence.profile import UserProfileService
from core.intelligence.explanation import ExplanationService
from models.company import Company

def test_deduplication(db: Session):
    from models.application import Application
    db.query(JobMatch).delete()
    db.query(Application).delete()
    db.query(Job).delete()
    db.query(CanonicalJob).delete()
    db.commit()
    
    dedup_svc = DeduplicationService(db)
    
    # 1. Create two identical jobs from different sources
    job1 = Job(
        title="Software Engineer",
        description="Write code in Python.",
        company_name="Tech Corp",
        location="Remote",
        job_url="https://source1.com/job1",
        application_url="https://techcorp.com/apply",
        is_active=True
    )
    job2 = Job(
        title="Software Engineer",
        description="Write code in Python.",
        company_name="Tech Corp",
        location="Remote",
        job_url="https://source2.com/job2",
        application_url="https://techcorp.com/apply",
        is_active=True
    )
    db.add(job1)
    db.add(job2)
    db.commit()
    
    # Deduplicate Job 1
    cj1 = dedup_svc.deduplicate_job(job1)
    db.commit()
    assert cj1 is not None
    assert cj1.company_name == "Tech Corp"
    assert job1.canonical_job_id == cj1.id
    
    # Deduplicate Job 2
    cj2 = dedup_svc.deduplicate_job(job2)
    db.commit()
    assert cj2 is not None
    assert cj2.id == cj1.id # Should merge into the same canonical job
    assert job2.canonical_job_id == cj1.id

def test_matching_and_ranking(db: Session):
    db.query(JobMatch).delete()
    from models.application import Application
    db.query(Application).delete()
    db.query(Job).delete()
    db.query(CanonicalJob).delete()
    db.query(UserProfile).delete()
    db.query(User).filter(User.email == "test_match@example.com").delete()
    db.commit()
    
    match_svc = JobMatchingService(db)
    rank_svc = RankingService(db)
    
    # Create a user and profile
    user = User(email="test_match@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    
    profile = UserProfile(
        user_id=user.id,
        skills=["Java", "Spring Boot", "AWS"],
        preferred_roles=["Backend Engineer"],
        experience=2,
        preferred_locations=["India", "Remote"]
    )
    db.add(profile)
    db.commit()
    
    # Create canonical jobs
    # 1. Highly relevant job
    job1 = CanonicalJob(
        title="Backend Engineer",
        description="Java, Spring Boot, AWS backend development.",
        company_name="Relevance Corp",
        location="India",
        skills=["Java", "Spring Boot", "AWS"],
        experience_min=1,
        experience_max=3,
        is_active=True
    )
    # 2. Unrelated job
    job2 = CanonicalJob(
        title="Frontend Developer",
        description="React, CSS, HTML frontend development.",
        company_name="Irrelevance Corp",
        location="USA",
        skills=["React", "CSS", "HTML"],
        experience_min=5,
        experience_max=10,
        is_active=True
    )
    db.add_all([job1, job2])
    db.commit()
    
    # Calculate matches
    match1 = match_svc.calculate_match(profile, job1)
    match2 = match_svc.calculate_match(profile, job2)
    
    # Verify deterministic scores
    assert match1.skill_match == 1.0 # Perfect overlap
    assert match2.skill_match == 0.0 # No overlap
    
    assert match1.match_score > match2.match_score
    assert match1.match_score > 90.0 # Should be high
    assert match2.match_score < 30.0 # Should be low
    
    # Rank matches
    rank_svc.rank_matches_for_user(user.id)
    db.refresh(match1)
    db.refresh(match2)
    
    assert match1.rank == 1
    assert match2.rank == 2

def test_acceptance_intelligence_pipeline(db: Session):
    """
    Acceptance test verifying the full pipeline:
    10 jobs -> Deduplication -> Profiling -> Matching -> Ranking -> Explanations
    """
    from models.application import Application
    db.query(JobMatch).delete()
    db.query(Application).delete()
    db.query(Job).delete()
    db.query(CanonicalJob).delete()
    db.query(UserProfile).delete()
    db.query(User).filter(User.email == "pipeline@example.com").delete()
    db.commit()
    
    dedup_svc = DeduplicationService(db)
    profile_svc = UserProfileService(db)
    match_svc = JobMatchingService(db)
    rank_svc = RankingService(db)
    exp_svc = ExplanationService(db)
    
    # 1. User Profile Setup
    user = User(email="pipeline@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    
    profile_data = {
        "skills": ["Java", "Spring Boot", "AWS", "React"],
        "preferred_roles": ["Software Engineer", "Backend Engineer"],
        "preferred_locations": ["India"],
        "experience": 1
    }
    profile = profile_svc.update_profile(user.id, profile_data)
    
    # 2. Job Setup
    raw_jobs = [
        Job(title="Backend Engineer", company_name="Corp A", location="India", description="Java Spring", skills=["Java", "Spring Boot"], experience_min=0, experience_max=2, job_url="a1"),
        Job(title="Backend Engineer", company_name="Corp A", location="India", description="Java Spring", skills=["Java", "Spring Boot"], experience_min=0, experience_max=2, job_url="a2"), # Duplicate
        Job(title="Senior Java Dev", company_name="Corp B", location="India", description="Java AWS", skills=["Java", "AWS"], experience_min=5, experience_max=10, job_url="b1"), # Too senior
        Job(title="React Developer", company_name="Corp C", location="India", description="React Frontend", skills=["React"], experience_min=0, experience_max=1, job_url="c1"), # Partial match
        Job(title="Marketing Manager", company_name="Corp D", location="USA", description="Marketing", skills=["Marketing"], experience_min=3, experience_max=5, job_url="d1"), # Unrelated
        # Add a few more generic jobs
        Job(title="DevOps Engineer", company_name="Corp E", location="India", description="AWS CI/CD", skills=["AWS"], experience_min=1, experience_max=3, job_url="e1"),
        Job(title="Data Scientist", company_name="Corp F", location="Remote", description="Python ML", skills=["Python", "ML"], experience_min=1, experience_max=2, job_url="f1"),
    ]
    db.add_all(raw_jobs)
    db.commit()
    
    # 3. Deduplication
    for j in raw_jobs:
        dedup_svc.deduplicate_job(j)
        
    canonical_jobs = db.query(CanonicalJob).all()
    assert len(canonical_jobs) == 6 # 7 raw jobs - 1 duplicate = 6 canonical
    
    # 4. Matching & Ranking
    match_svc.batch_calculate_matches(profile, active_only=True)
    rank_svc.rank_matches_for_user(user.id)
    
    matches = db.query(JobMatch).filter(JobMatch.user_id == user.id).order_by(JobMatch.rank.asc()).all()
    assert len(matches) == 6
    
    # Best match should be Corp A (Backend Engineer, Java/Spring, 0-2 yrs)
    best_match = matches[0]
    assert best_match.canonical_job.company_name == "Corp A"
    assert best_match.match_score > 85.0
    
    # Worst match should be Corp D (Marketing)
    worst_match = matches[-1]
    assert worst_match.canonical_job.company_name == "Corp D"
    assert worst_match.match_score < 30.0
    
    # 5. Explanations (Mocking the AI call since we don't want to hit the API in tests)
    # The ExplanationsService will handle missing API key by providing a default reason
    exp_svc.generate_explanation(profile, best_match.canonical_job, best_match)
    assert best_match.match_reasons is not None
    assert len(best_match.match_reasons) > 0

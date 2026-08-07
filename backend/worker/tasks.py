import time
from worker.celery_app import celery_app
from agents.supervisor import run_workflow
from db.session import SessionLocal
from core.ai import generate_embedding
from crud.crud_job import create_job

@celery_app.task
def run_job_discovery_workflow():
    """
    This task will run every 6 hours for active users.
    """
    print("Executing job discovery workflow...")
    dummy_profile = {
        "skills": "React, FastAPI",
        "role": "Full Stack Engineer"
    }
    
    result = run_workflow(user_profile=dummy_profile)
    jobs_found = result.get("jobs_found", [])
    print(f"Workflow Complete: Found {len(jobs_found)} jobs.")
    
    db = SessionLocal()
    try:
        for job_data in jobs_found:
            text_to_embed = f"{job_data.get('title', '')} {job_data.get('description', '')}"
            embedding = generate_embedding(text_to_embed)
            create_job(db, job_data, embedding)
        print("Jobs successfully saved with embeddings!")
    except Exception as e:
        print(f"Error saving jobs: {e}")
    finally:
        db.close()
        
    return True

@celery_app.task
def send_email_digest(user_email: str, jobs: list):
    """
    Sends the job digest email using Resend (Placeholder).
    """
    print(f"Sending email digest to {user_email} with {len(jobs)} jobs...")
    return True

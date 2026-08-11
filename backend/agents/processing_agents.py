from agents.search_agents import AgentState
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.job import Job
import numpy as np

def deduplication_node(state: AgentState):
    """
    Removes duplicate jobs using pgvector cosine similarity.
    """
    print("Running deduplication...")
    jobs = state.get("jobs_found", [])
    
    if not jobs:
        return {"jobs_found": []}
        
    from core.config import settings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=settings.OPENAI_API_KEY)
    db: Session = SessionLocal()
    
    unique_jobs = []
    
    try:
        for job in jobs:
            text_to_embed = f"{job['title']} at {job['company']} - {job.get('description', '')[:500]}"
            try:
                vector = embeddings.embed_query(text_to_embed)
            except Exception as e:
                print(f"Skipping OpenAI deduplication for {job['title']} due to embedding error: {e}. Using mock embedding.")
                import random
                job['embedding'] = [random.random() for _ in range(1536)]
                unique_jobs.append(job)
                continue
                
            # Check db for similar jobs (distance < 0.1 means > 90% similar)
            similar_job = db.query(Job).filter(
                Job.embedding.cosine_distance(vector) < 0.1
            ).first()
            
            if not similar_job:
                job['embedding'] = vector
                unique_jobs.append(job)
            else:
                print(f"Skipping duplicate: {job['title']} at {job['company']}")
    finally:
        db.close()
        
    return {"jobs_found": unique_jobs}

def ranking_node(state: AgentState):
    """
    Ranks jobs based on user profile.
    """
    print("Running ranking...")
    jobs = state.get("jobs_found", [])
    for job in jobs:
        job["score"] = 85 # Dummy score
    jobs.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {"jobs_found": jobs}

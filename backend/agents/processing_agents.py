from agents.search_agents import AgentState

def deduplication_node(state: AgentState):
    """
    Removes duplicate jobs using basic URL/Title matching,
    and pgvector cosine similarity in a real scenario.
    """
    print("Running deduplication...")
    jobs = state.get("jobs_found", [])
    unique_jobs = {job["url"]: job for job in jobs}.values()
    return {"jobs_found": list(unique_jobs)}

def ranking_node(state: AgentState):
    """
    Ranks jobs based on user profile using embeddings/LLM.
    """
    print("Running ranking...")
    jobs = state.get("jobs_found", [])
    # Dummy ranking logic
    for job in jobs:
        job["score"] = 85 # Arbitrary score for testing
    
    # Sort by score descending
    jobs.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {"jobs_found": jobs}

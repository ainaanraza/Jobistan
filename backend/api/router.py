from fastapi import APIRouter
from api.routes import auth, users, profiles, jobs, sources, applications, ai, ingestion, matches

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])

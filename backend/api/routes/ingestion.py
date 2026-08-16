from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel, HttpUrl
from api.deps import get_db, get_current_active_user
from models.user import User
from core.ingestion.manager import IngestionManager

router = APIRouter()
ingestion_manager = IngestionManager()

class TestSourceRequest(BaseModel):
    url: HttpUrl

@router.post("/test-source")
def test_source(
    request: TestSourceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        url_str = str(request.url)
        result = ingestion_manager.fetch_source(url_str)
        jobs = result.jobs
        
        return {
            "status": result.diagnostics.status,
            "url": url_str,
            "detected_platform": result.diagnostics.adapter,
            "jobs_found": len(jobs),
            "sample_jobs": [j.model_dump() for j in jobs[:10]],
            "error": None
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "url": str(request.url),
            "detected_platform": "Unknown",
            "jobs_found": 0,
            "sample_jobs": [],
            "error": str(e)
        }

from typing import List
from sqlalchemy.orm import Session
from models.job_match import JobMatch

class RankingService:
    def __init__(self, db: Session):
        self.db = db
        
    def rank_matches_for_user(self, user_id: int):
        """Sorts all matches for a user by score and assigns a rank index (1 = highest)."""
        matches = self.db.query(JobMatch).filter(
            JobMatch.user_id == user_id
        ).order_by(JobMatch.match_score.desc()).all()
        
        for index, match in enumerate(matches):
            match.rank = index + 1
            
        self.db.commit()

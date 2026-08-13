from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.merge_digest.digest_builder import build_digest
from app.merge_digest.models import DigestEntry

router = APIRouter(prefix="/digest", tags=["merge_digest"])


class DigestPR(BaseModel):
    pr_id: str
    pr_number: int
    repo: str
    title: str
    risk_score: float
    risk_factors: List[str]
    summary: str


class DigestResponse(BaseModel):
    summary: str
    ready_to_merge: List[DigestPR]
    needs_review: List[DigestPR]
    in_progress: List[DigestPR]


class PRRiskDetail(BaseModel):
    pr_id: str
    pr_number: int
    repo: str
    title: str
    risk_score: float
    risk_factors: List[str]
    summary: str
    generated_at: datetime


@router.get("/today", response_model=DigestResponse)
def get_today_digest(db: Session = Depends(get_db)):
    return build_digest(db)


@router.get("/pr/{pr_id}", response_model=PRRiskDetail)
def get_pr_risk(pr_id: str, db: Session = Depends(get_db)):
    entry = db.query(DigestEntry).filter(DigestEntry.pr_id == pr_id).first()
    if not entry:
        raise HTTPException(404, "Digest entry not found")
    # pull request details
    from app.db.models import PullRequest
    pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(404, "PR not found")
    return PRRiskDetail(
        pr_id=pr.id,
        pr_number=pr.pr_number,
        repo=pr.repo,
        title=pr.title or "",
        risk_score=entry.risk_score,
        risk_factors=entry.risk_factors,
        summary=entry.summary_text or "",
        generated_at=entry.generated_at,
    )
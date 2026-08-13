"""
Build daily merge readiness digest.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import PullRequest
from app.merge_digest.risk_scoring import compute_risk
from app.merge_digest.models import DigestEntry


# Risk thresholds for bucketing
LOW_RISK_MAX = 30.0
MEDIUM_RISK_MAX = 60.0
# above MEDIUM_RISK_MAX => high risk

def build_digest(db: Session) -> Dict[str, Any]:
    """Compute risk for all open PRs, create DigestEntry rows, return structured digest."""
    open_prs = db.query(PullRequest).filter(PullRequest.state == "open").all()

    ready = []
    needs_review = []
    in_progress = []

    for pr in open_prs:
        risk_score, risk_factors = compute_risk(pr, db)
        # determine bucket
        # check if session is active (in_progress)
        session = pr.session
        in_prog = session and session.activity_state.value in ("active", "waiting_input", "blocked")
        if in_prog:
            bucket = "in_progress"
        elif risk_score <= LOW_RISK_MAX:
            bucket = "ready_to_merge"
        elif risk_score <= MEDIUM_RISK_MAX:
            bucket = "needs_review"
        else:
            bucket = "needs_review"

        # create or update DigestEntry
        entry = db.query(DigestEntry).filter(DigestEntry.pr_id == pr.id).first()
        if not entry:
            entry = DigestEntry(pr_id=pr.id)
            db.add(entry)
        entry.risk_score = risk_score
        entry.risk_factors = risk_factors
        entry.summary_text = _one_liner(pr, risk_score, risk_factors, bucket)
        entry.generated_at = __import__("datetime").datetime.utcnow()

        pr_data = {
            "pr_id": pr.id,
            "pr_number": pr.pr_number,
            "repo": pr.repo,
            "title": pr.title,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "summary": entry.summary_text,
        }

        if bucket == "ready_to_merge":
            ready.append(pr_data)
        elif bucket == "needs_review":
            needs_review.append(pr_data)
        else:
            in_progress.append(pr_data)

    db.commit()

    summary = _overall_summary(ready, needs_review, in_progress)

    return {
        "summary": summary,
        "ready_to_merge": ready,
        "needs_review": needs_review,
        "in_progress": in_progress,
    }


def _one_liner(pr: PullRequest, risk_score: float, factors: List[str], bucket: str) -> str:
    if bucket == "ready_to_merge":
        return f"#{pr.pr_number} ({pr.repo}) - low risk ({risk_score:.0f})"
    elif bucket == "needs_review":
        why = "; ".join(factors) if factors else "medium risk"
        return f"#{pr.pr_number} ({pr.repo}) - {why}"
    else:
        return f"#{pr.pr_number} ({pr.repo}) - session still active"


def _overall_summary(ready: List[Dict], needs_review: List[Dict], in_progress: List[Dict]) -> str:
    parts = []
    if ready:
        parts.append(f"{len(ready)} ready to merge, low risk")
    if needs_review:
        # pick first reason
        reasons = []
        for pr in needs_review:
            reasons.extend(pr.get("risk_factors", []))
        reason_text = "; ".join(set(reasons)) if reasons else "needs review"
        parts.append(f"{len(needs_review)} needs your eyes — {reason_text}")
    if in_progress:
        parts.append(f"{len(in_progress)} still iterating")
    if not parts:
        return "No open PRs."
    return ". ".join(parts) + "."
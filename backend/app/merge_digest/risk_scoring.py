"""
Risk scoring for merge readiness.
Pure functions, constants at top for easy tuning.
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db.models import PullRequest, Event, Session as SessionModel

# ---- Tunable constants -------------------------------------------------
# Base score
BASE_RISK = 0.0

# Diff size thresholds (lines changed)
DIFF_SMALL_MAX = 50
DIFF_MEDIUM_MAX = 200
DIFF_LARGE_MAX = 500
# Points added per bucket
DIFF_SMALL_POINTS = 5.0
DIFF_MEDIUM_POINTS = 15.0
DIFF_LARGE_POINTS = 30.0
DIFF_HUGE_POINTS = 50.0

# Sensitive path patterns (any match adds points)
SENSITIVE_PATH_PATTERNS = [
    r"auth/",
    r"config/",
    r"\.env",
    r"payment/",
    r"migrations/",
    r"Dockerfile",
    r"\.github/workflows/.*\.ya?ml$",
    r"\.gitlab/.*\.ya?ml$",
    r"circleci/.*\.ya?ml$",
    r"azure-pipelines/.*\.ya?ml$",
]
SENSITIVE_PATH_POINTS = 25.0

# CI status from events
CI_FAILED_POINTS = 40.0
CI_FLAKY_POINTS = 20.0  # if any failed then passed? simplify: if any failed event present

# Staleness: days since last update
STALE_DAYS_WARN = 7
STALE_DAYS_CRITICAL = 14
STALE_WARN_POINTS = 10.0
STALE_CRITICAL_POINTS = 25.0

MAX_RISK = 100.0
# ------------------------------------------------------------------------


def _score_diff(diff_lines: Optional[int]) -> tuple[float, List[str]]:
    if diff_lines is None:
        return 0.0, []
    factors = []
    if diff_lines <= DIFF_SMALL_MAX:
        score = DIFF_SMALL_POINTS
        factors.append(f"small diff ({diff_lines} lines)")
    elif diff_lines <= DIFF_MEDIUM_MAX:
        score = DIFF_MEDIUM_POINTS
        factors.append(f"medium diff ({diff_lines} lines)")
    elif diff_lines <= DIFF_LARGE_MAX:
        score = DIFF_LARGE_POINTS
        factors.append(f"large diff ({diff_lines} lines)")
    else:
        score = DIFF_HUGE_POINTS
        factors.append(f"very large diff ({diff_lines} lines)")
    return score, factors


def _score_sensitive_paths(file_paths: List[str]) -> tuple[float, List[str]]:
    import re
    factors = []
    score = 0.0
    for pattern in SENSITIVE_PATH_PATTERNS:
        for fp in file_paths:
            if re.search(pattern, fp):
                factors.append(f"touches sensitive path: {fp}")
                score += SENSITIVE_PATH_POINTS
    return score, factors


def _score_ci(db: Session, pr_id: str) -> tuple[float, List[str]]:
    """Look at recent pr_check events for this PR."""
    factors = []
    score = 0.0
    events = db.query(Event).filter(Event.event_type.like("pr_check.%")).all()
    for ev in events:
        payload = ev.normalized_payload.get("payload", {})
        if payload.get("pr_id") != pr_id:
            continue
        conclusion = str(payload.get("conclusion") or payload.get("status") or "").lower()
        if conclusion in ("failure", "failed", "error"):
            factors.append("CI failed")
            score += CI_FAILED_POINTS
            break
        elif conclusion in ("canceled", "cancelled", "timed_out"):
            factors.append("CI flaky/unstable")
            score += CI_FLAKY_POINTS
    return score, factors


def _score_staleness(updated_at: Optional[datetime]) -> tuple[float, List[str]]:
    if not updated_at:
        return 0.0, []
    factors = []
    score = 0.0
    now = datetime.now(timezone.utc)
    delta = now - updated_at.replace(tzinfo=timezone.utc)
    days = delta.days
    if days >= STALE_DAYS_CRITICAL:
        score = STALE_CRITICAL_POINTS
        factors.append(f"stale > {STALE_DAYS_CRITICAL} days ({days}d)")
    elif days >= STALE_DAYS_WARN:
        score = STALE_WARN_POINTS
        factors.append(f"stale > {STALE_DAYS_WARN} days ({days}d)")
    return score, factors


def compute_risk(pr: PullRequest, db: Session) -> tuple[float, List[str]]:
    """Return (risk_score, risk_factors)."""
    total = BASE_RISK
    factors = []

    # diff size: we may not have diff lines stored; try from PR metadata if exists
    diff_lines = None
    # try to get from recent pr events maybe
    # For now, assume not available
    diff_score, diff_factors = _score_diff(diff_lines)
    total += diff_score
    factors.extend(diff_factors)

    # sensitive paths: need file list. Could extract from PR events (pull_requests events may contain files)
    file_paths = []
    # try to get from events of type pr.updated
    events = db.query(Event).filter(Event.event_type.like("pr.%")).all()
    for ev in events:
        payload = ev.normalized_payload.get("payload", {})
        if payload.get("id") == pr.id:
            files = payload.get("files")
            if isinstance(files, list):
                file_paths.extend(files)
    sens_score, sens_factors = _score_sensitive_paths(file_paths)
    total += sens_score
    factors.extend(sens_factors)

    # CI
    ci_score, ci_factors = _score_ci(db, pr.id)
    total += ci_score
    factors.extend(ci_factors)

    # staleness
    stale_score, stale_factors = _score_staleness(pr.updated_at)
    total += stale_score
    factors.extend(stale_factors)

    total = min(total, MAX_RISK)
    return total, factors
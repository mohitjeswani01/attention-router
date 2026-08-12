"""
Scoring constants and pure function to compute urgency for a session.

Priority order (high to low):
1. idle waiting on approval (activity_state == 'waiting_input' or 'blocked') with high idle_seconds
2. ci_failed (any recent pr_check event with conclusion == 'failure')
3. review_requested (PR state changes_requested or review_pending)
4. actively working (low score)
5. simple idle (activity_state == 'idle') – baseline score so it appears in queue
6. healthy (no score, excluded)

Weights are configurable constants at top.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.db.models import Session as SessionModel, Event as EventModel

# ---- Tunable constants -------------------------------------------------
# Base scores for each reason category
SCORE_IDLE_APPROVAL_BASE = 100.0
SCORE_CI_FAILED_BASE = 80.0
SCORE_REVIEW_REQUESTED_BASE = 60.0
SCORE_WORKING_BASE = 10.0  # low, typically not queued
SCORE_IDLE_BASE = 5.0       # baseline for sessions that are simply idle

# Multiplier per minute of idle time (for idle approval)
IDLE_SECONDS_WEIGHT = 0.5  # points per second idle -> 30 per minute

# Thresholds
MIN_IDLE_SECONDS_TO_QUEUE = 30  # only queue if idle > 30s
MAX_URGENCY = 1000.0

# ------------------------------------------------------------------------


def _seconds_since(dt_str: Optional[str]) -> int:
    """Parse ISO UTC string and return seconds since then (now - dt)."""
    if not dt_str:
        return 0
    try:
        # dt_str like "2026-08-12T12:34:56.789Z"
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return int((datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:
        return 0


def compute_urgency(session: SessionModel, recent_events: List[EventModel]) -> tuple[float, str, int]:
    """
    Returns (urgency_score, reason, idle_seconds).
    If the session should not appear in the queue, returns (0.0, "healthy", 0).
    """
    activity = session.activity_state.value if session.activity_state else "idle"
    now = datetime.now(timezone.utc)
    idle_seconds = int((now - session.updated_at.replace(tzinfo=timezone.utc)).total_seconds()) if session.updated_at and activity in ("waiting_input", "blocked") else 0

    # 1. Idle waiting on approval
    if activity in ("waiting_input", "blocked") and idle_seconds >= MIN_IDLE_SECONDS_TO_QUEUE:
        score = SCORE_IDLE_APPROVAL_BASE + idle_seconds * IDLE_SECONDS_WEIGHT
        reason = "idle_on_approval"
        return min(score, MAX_URGENCY), reason, idle_seconds

    # 2. CI failed – look for recent pr_check events with conclusion failure
    for ev in recent_events:
        if ev.event_type.startswith("pr_check.") and ev.normalized_payload:
            payload = ev.normalized_payload.get("payload", {})
            conclusion = payload.get("conclusion") or payload.get("status")
            if str(conclusion).lower() in ("failure", "failed", "error"):
                return SCORE_CI_FAILED_BASE, "ci_failed", 0

    # 3. Review requested – check PR events for changes_requested / review_pending
    for ev in recent_events:
        if ev.event_type.startswith("pr.") and ev.normalized_payload:
            payload = ev.normalized_payload.get("payload", {})
            state = str(payload.get("state") or "").lower()
            if state in ("changes_requested", "review_pending", "awaiting_review"):
                return SCORE_REVIEW_REQUESTED_BASE, "review_requested", 0

    # 4. Actively working / healthy – low score, caller can decide to exclude
    if activity == "active":
        return SCORE_WORKING_BASE, "working", 0

    # 5. Simple idle (not waiting on approval) – low baseline so it appears in queue
    if activity == "idle":
        idle_seconds = int((now - session.updated_at.replace(tzinfo=timezone.utc)).total_seconds()) if session.updated_at else 0
        return SCORE_IDLE_BASE, "idle", idle_seconds

    # Default healthy but not waiting on approval
    return 0.0, "healthy", 0
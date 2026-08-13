#!/usr/bin/env python3
"""
Seed script: inserts a few fake Session rows with different activity_states
so that the attention queue shows a ranked list without needing the AO daemon.

Run from repo root:
    cd backend && python scripts/seed_fake_sessions.py
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import engine, SessionLocal, init_db
from app.db.models import Session as SessionModel, ActivityState, PullRequest, Event, DigestEntry


# Known fake session IDs for idempotent seeding
FAKE_SESSION_IDS = [
    "00000000-0000-0000-0000-000000000001",  # idle, terminated -> ready_to_merge (low risk)
    "00000000-0000-0000-0000-000000000002",  # idle, terminated -> needs_review (high risk)
    "00000000-0000-0000-0000-000000000003",  # waiting_input -> in_progress
    "00000000-0000-0000-0000-000000000004",  # active -> in_progress
]


def seed():
    init_db()
    db: Session = SessionLocal()
    try:
        # Clear existing fake sessions and their related data for idempotency
        for sid in FAKE_SESSION_IDS:
            # Delete in correct order due to FK constraints
            db.query(DigestEntry).join(PullRequest).filter(PullRequest.session_id == sid).delete(synchronize_session=False)
            db.query(Event).filter(Event.session_id == sid).delete(synchronize_session=False)
            db.query(PullRequest).filter(PullRequest.session_id == sid).delete(synchronize_session=False)
            db.query(SessionModel).filter(SessionModel.id == sid).delete(synchronize_session=False)
        db.commit()

        now = datetime.utcnow()

        sessions_data = [
            {
                "id": FAKE_SESSION_IDS[0],
                "project_id": "11111111-1111-1111-1111-111111111111",
                "agent_type": "claude",
                "activity_state": ActivityState.IDLE,
                "status": "completed",
                "pr_url": "https://github.com/myorg/docs-repo/pull/101",
                "created_at": now - timedelta(hours=3),
                "updated_at": now - timedelta(hours=2),  # idle, low risk PR
            },
            {
                "id": FAKE_SESSION_IDS[1],
                "project_id": "22222222-2222-2222-2222-222222222222",
                "agent_type": "codex",
                "activity_state": ActivityState.EXITED,
                "status": "completed",
                "pr_url": "https://github.com/myorg/legacy/pull/103",
                "created_at": now - timedelta(days=11),
                "updated_at": now - timedelta(days=10),  # stale, high risk PR
            },
            {
                "id": FAKE_SESSION_IDS[2],
                "project_id": "33333333-3333-3333-3333-333333333333",
                "agent_type": "claude",
                "activity_state": ActivityState.WAITING_INPUT,
                "status": "needs_input",
                "pr_url": "https://github.com/myorg/app/pull/102",
                "created_at": now - timedelta(hours=2),
                "updated_at": now - timedelta(minutes=10),  # waiting, in_progress
            },
            {
                "id": FAKE_SESSION_IDS[3],
                "project_id": "44444444-4444-4444-4444-444444444444",
                "agent_type": "codex",
                "activity_state": ActivityState.ACTIVE,
                "status": "working",
                "pr_url": None,
                "created_at": now - timedelta(minutes=30),
                "updated_at": now - timedelta(minutes=1),  # active, in_progress
            },
        ]

        for data in sessions_data:
            sess = SessionModel(**data)
            db.add(sess)

        db.commit()
        print(f"Seeded {len(sessions_data)} fake sessions (idempotent).")
        for s in sessions_data:
            print(f"  - {s['id'][:8]} state={s['activity_state'].value} updated={s['updated_at'].isoformat()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
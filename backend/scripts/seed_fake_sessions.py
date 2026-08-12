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
from app.db.models import Session as SessionModel, ActivityState


def seed():
    init_db()
    db: Session = SessionLocal()
    try:
        # Clear existing sessions for a clean demo
        db.query(SessionModel).delete()
        db.commit()

        now = datetime.utcnow()

        sessions_data = [
            {
                "id": str(uuid.uuid4()),
                "project_id": str(uuid.uuid4()),
                "agent_type": "claude",
                "activity_state": ActivityState.WAITING_INPUT,
                "status": "needs_input",
                "pr_url": "https://github.com/org/repo/pull/42",
                "created_at": now - timedelta(hours=2),
                "updated_at": now - timedelta(minutes=10),  # idle 10 min
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": str(uuid.uuid4()),
                "agent_type": "codex",
                "activity_state": ActivityState.BLOCKED,
                "status": "blocked",
                "pr_url": "https://github.com/org/repo/pull/43",
                "created_at": now - timedelta(hours=1),
                "updated_at": now - timedelta(minutes=45),  # idle 45 min
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": str(uuid.uuid4()),
                "agent_type": "claude",
                "activity_state": ActivityState.ACTIVE,
                "status": "working",
                "pr_url": None,
                "created_at": now - timedelta(minutes=30),
                "updated_at": now - timedelta(minutes=1),
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": str(uuid.uuid4()),
                "agent_type": "codex",
                "activity_state": ActivityState.IDLE,
                "status": "idle",
                "pr_url": None,
                "created_at": now - timedelta(hours=3),
                "updated_at": now - timedelta(hours=1),
            },
        ]

        for data in sessions_data:
            sess = SessionModel(**data)
            db.add(sess)

        db.commit()
        print(f"Seeded {len(sessions_data)} fake sessions.")
        for s in sessions_data:
            print(f"  - {s['id'][:8]} state={s['activity_state'].value} updated={s['updated_at'].isoformat()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
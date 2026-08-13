#!/usr/bin/env python3
"""
Seed script: inserts fake Session rows with different activity_states
so that the attention queue shows a ranked list without needing the AO daemon.
Fully idempotent: clears existing seed rows before inserting.

Run from repo root:
    cd backend && python scripts/seed_fake_sessions.py
"""

import asyncio
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.db.models import Session as SessionModel, ActivityState, PullRequest, Event
from app.attention_router.models import AttentionItem
from app.policy_gate.models import ApprovalDecision, PolicyRule
from app.merge_digest.models import DigestEntry
from app.attention_router.queue_service import _recompute_and_upsert
from app.policy_gate.default_policies import seed_default_rules, seed_default_decisions


# Distinct, realistic fake session IDs (no 00000000 prefixes)
FAKE_SESSION_IDS = [
    "a1b2c3d4-1111-4222-8333-000000000001",  # idle -> low urgency
    "b2c3d4e5-2222-4333-8444-000000000002",  # exited -> healthy (not queued)
    "c3d4e5f6-3333-4444-8555-000000000003",  # waiting_input -> idle_on_approval (high urgency)
    "d4e5f6a7-4444-4555-8666-000000000004",  # active -> working
]


def seed():
    init_db()
    db: Session = SessionLocal()
    try:
        # 1. Clear existing attention items, digest entries, approval decisions, events, PRs, and sessions
        db.query(AttentionItem).delete(synchronize_session=False)
        db.query(DigestEntry).delete(synchronize_session=False)
        db.query(ApprovalDecision).delete(synchronize_session=False)
        db.query(Event).filter(Event.session_id.in_(FAKE_SESSION_IDS)).delete(synchronize_session=False)
        db.query(PullRequest).filter(PullRequest.session_id.in_(FAKE_SESSION_IDS)).delete(synchronize_session=False)
        db.query(SessionModel).filter(SessionModel.id.in_(FAKE_SESSION_IDS)).delete(synchronize_session=False)
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

        # Seed policy rules & audit log decisions
        seed_default_rules(db)

        print(f"Seeded {len(sessions_data)} fake sessions (idempotent).")
        for s in sessions_data:
            print(f"  - {s['id'][:8]} state={s['activity_state'].value} updated={s['updated_at'].isoformat()}")

        # Recompute urgency for seeded sessions
        for sid in FAKE_SESSION_IDS:
            asyncio.run(_recompute_and_upsert(sid))

    finally:
        db.close()


if __name__ == "__main__":
    seed()
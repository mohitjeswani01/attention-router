#!/usr/bin/env python3
"""
Seed script for merge_digest demo:
Creates 3 PRs with different risk profiles and associated events.
Run after seed_fake_sessions.py and recompute_urgency.py.
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.db.models import Session as SessionModel, PullRequest as PRModel, Event as EventModel
from app.merge_digest.models import DigestEntry

# Known fake PR numbers for idempotent seeding
FAKE_PR_NUMBERS = [101, 102, 103]

FAKE_SESSION_IDS = [
    "a1b2c3d4-1111-4222-8333-000000000001",  # idle -> ready_to_merge
    "b2c3d4e5-2222-4333-8444-000000000002",  # exited -> needs_review
    "c3d4e5f6-3333-4444-8555-000000000003",  # waiting_input -> in_progress
    "d4e5f6a7-4444-4555-8666-000000000004",  # active -> in_progress
]


def seed():
    init_db()
    db: Session = SessionLocal()
    try:
        # Clear existing fake PRs and their related data for idempotency
        for pr_num in FAKE_PR_NUMBERS:
            existing_pr = db.query(PRModel).filter(PRModel.pr_number == pr_num).first()
            if existing_pr:
                db.query(DigestEntry).filter(DigestEntry.pr_id == existing_pr.id).delete(synchronize_session=False)
                db.query(EventModel).filter(EventModel.session_id == existing_pr.session_id).delete(synchronize_session=False)
                db.query(PRModel).filter(PRModel.id == existing_pr.id).delete(synchronize_session=False)
        db.commit()

        # Get our known sessions
        sessions = {}
        for sid in FAKE_SESSION_IDS:
            sess = db.query(SessionModel).filter(SessionModel.id == sid).first()
            if sess:
                sessions[sess.id] = sess

        if len(sessions) < 3:
            raise RuntimeError("Need at least 3 sessions; run seed_fake_sessions.py first")

        now = datetime.utcnow()

        pr_data = [
            {
                "session": sessions[FAKE_SESSION_IDS[0]],  # IDLE session -> ready_to_merge (low risk)
                "pr_number": 101,
                "repo": "myorg/docs-repo",
                "title": "Update README",
                "state": "open",
                "files": ["README.md", "docs/guide.md"],
                "ci_conclusion": "success",
                "updated_at": now - timedelta(hours=2),  # recent
            },
            {
                "session": sessions[FAKE_SESSION_IDS[2]],  # WAITING_INPUT session -> in_progress
                "pr_number": 102,
                "repo": "myorg/app",
                "title": "Update Dockerfile",
                "state": "open",
                "files": ["Dockerfile", "src/main.py"],
                "ci_conclusion": "failure",
                "updated_at": now - timedelta(days=1),
            },
            {
                "session": sessions[FAKE_SESSION_IDS[1]],  # EXITED session, stale + sensitive -> needs_review
                "pr_number": 103,
                "repo": "myorg/legacy",
                "title": "Refactor auth module",
                "state": "open",
                "files": ["auth/handlers.py", "auth/middleware.py", "config/settings.yaml"],
                "ci_conclusion": "success",
                "updated_at": now - timedelta(days=10),  # stale > 7 days
            },
        ]

        for data in pr_data:
            sess = data["session"]
            pr = PRModel(
                id=str(uuid.uuid4()),
                session_id=sess.id,
                pr_number=data["pr_number"],
                repo=data["repo"],
                title=data["title"],
                state="open",
                created_at=data["updated_at"],
                updated_at=data["updated_at"],
            )
            db.add(pr)
            db.flush()  # get id

            # Add pull_requests CDC event (simulated)
            ev_pr = EventModel(
                id=str(uuid.uuid4()),
                session_id=sess.id,
                event_type="pr.updated",
                raw_payload={"id": pr.id, "number": data["pr_number"], "repo": data["repo"], "files": data["files"]},
                normalized_payload={
                    "id": str(uuid.uuid4()),
                    "event_type": "pr.updated",
                    "session_id": sess.id,
                    "operation": "UPDATE",
                    "table": "pull_requests",
                    "payload": {"id": pr.id, "number": data["pr_number"], "repo": data["repo"], "files": data["files"]},
                    "received_at": now.isoformat() + "Z",
                    "source": "cdc_sse",
                },
                received_at=now,
            )
            db.add(ev_pr)

            # Add pr_check event for CI
            ev_check = EventModel(
                id=str(uuid.uuid4()),
                session_id=sess.id,
                event_type="pr_check.updated",
                raw_payload={"pr_id": pr.id, "conclusion": data["ci_conclusion"]},
                normalized_payload={
                    "id": str(uuid.uuid4()),
                    "event_type": "pr_check.updated",
                    "session_id": sess.id,
                    "operation": "UPDATE",
                    "table": "pr_checks",
                    "payload": {"pr_id": pr.id, "conclusion": data["ci_conclusion"]},
                    "received_at": now.isoformat() + "Z",
                    "source": "cdc_sse",
                },
                received_at=now,
            )
            db.add(ev_check)

        db.commit()
        print(f"Seeded {len(pr_data)} PRs with events (idempotent).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
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


def seed():
    init_db()
    db: Session = SessionLocal()
    try:
        # ensure we have at least 3 sessions
        sessions = db.query(SessionModel).limit(3).all()
        if len(sessions) < 3:
            raise RuntimeError("Need at least 3 sessions; run seed_fake_sessions.py first")

        now = datetime.utcnow()

        pr_data = [
            {
                "session": sessions[0],
                "pr_number": 101,
                "repo": "myorg/docs-repo",
                "title": "Update README",
                "state": "open",
                "files": ["README.md", "docs/guide.md"],
                "ci_conclusion": "success",
                "updated_at": now - timedelta(hours=2),
            },
            {
                "session": sessions[1],
                "pr_number": 102,
                "repo": "myorg/app",
                "title": "Update Dockerfile",
                "state": "open",
                "files": ["Dockerfile", "src/main.py"],
                "ci_conclusion": "failure",
                "updated_at": now - timedelta(days=1),
            },
            {
                "session": sessions[2],
                "pr_number": 103,
                "repo": "myorg/legacy",
                "title": "Refactor auth module",
                "state": "open",
                "files": ["auth/handlers.py", "auth/middleware.py"],
                "ci_conclusion": "success",
                "updated_at": now - timedelta(days=10),  # stale
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
                state=data["state"],
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
        print(f"Seeded {len(pr_data)} PRs with events.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
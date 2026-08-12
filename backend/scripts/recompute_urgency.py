#!/usr/bin/env python3
"""
Recompute urgency for all existing sessions and populate AttentionItem table.
Run after seed_fake_sessions.py.
"""

import asyncio
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.db.models import Session as SessionModel
from app.attention_router.queue_service import _recompute_and_upsert


async def main():
    init_db()
    db: Session = SessionLocal()
    try:
        sessions = db.query(SessionModel).all()
        for sess in sessions:
            await _recompute_and_upsert(sess.id)
        print(f"Recomputed urgency for {len(sessions)} sessions.")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
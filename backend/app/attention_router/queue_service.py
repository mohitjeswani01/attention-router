"""
Queue service: subscribes to event_bus, recomputes urgency for affected sessions,
upserts AttentionItem rows, and provides a DB-backed ranked queue getter.
"""

import asyncio
import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import session_scope
from app.db.models import Session as SessionModel, Event as EventModel
from app.attention_router.models import AttentionItem
from app.attention_router.scoring import compute_urgency
from app.ingestion.event_bus import event_bus

logger = logging.getLogger(__name__)

# How many recent events to consider when scoring a session
RECENT_EVENTS_LIMIT = 20


async def _recompute_and_upsert(session_id: str) -> None:
    """Load session + recent events, compute urgency, upsert AttentionItem."""
    with session_scope() as db:
        sess = db.get(SessionModel, session_id)
        if not sess:
            logger.warning("Session %s not found for scoring", session_id)
            return

        # fetch recent events for this session
        stmt = (
            select(EventModel)
            .where(EventModel.session_id == session_id)
            .order_by(EventModel.received_at.desc())
            .limit(RECENT_EVENTS_LIMIT)
        )
        recent_events = db.execute(stmt).scalars().all()

        urgency, reason, idle_seconds = compute_urgency(sess, recent_events)

        # Only persist if there is a meaningful reason (score > 0)
        if urgency <= 0:
            # Remove any existing attention item for healthy sessions
            existing = db.query(AttentionItem).filter(AttentionItem.session_id == session_id).first()
            if existing:
                db.delete(existing)
                logger.debug("Removed attention item for healthy session %s", session_id)
            return

        item = db.query(AttentionItem).filter(AttentionItem.session_id == session_id).first()
        if item:
            item.urgency_score = urgency
            item.reason = reason
            item.idle_seconds = idle_seconds
            item.resolved = False
            item.resolved_at = None
        else:
            item = AttentionItem(
                session_id=session_id,
                urgency_score=urgency,
                reason=reason,
                idle_seconds=idle_seconds,
            )
            db.add(item)
        logger.info("Upserted attention item for session %s: score=%.1f reason=%s idle=%ds",
                    session_id, urgency, reason, idle_seconds)


async def _event_listener() -> None:
    """Background task that consumes event_bus and triggers recompute."""
    async for event in event_bus.subscribe():
        session_id = event.get("session_id")
        if not session_id:
            continue
        # Only react to relevant tables
        table = event.get("table")
        if table not in ("sessions", "pull_requests", "pr_checks"):
            continue
        try:
            await _recompute_and_upsert(session_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error recomputing urgency for session %s: %s", session_id, exc)


# Public API --------------------------------------------------------------

async def start_queue_service() -> None:
    """Launch the background listener."""
    asyncio.create_task(_event_listener())
    logger.info("Attention queue service started")


def get_ranked_queue(db: Session, limit: int = 50) -> List[AttentionItem]:
    """Return current ranked queue (unresolved items ordered by urgency desc)."""
    stmt = (
        select(AttentionItem)
        .where(AttentionItem.resolved == False)  # noqa: E712
        .order_by(AttentionItem.urgency_score.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def resolve_item(db: Session, item_id: str) -> Optional[AttentionItem]:
    """Mark an attention item as resolved."""
    item = db.get(AttentionItem, item_id)
    if item and not item.resolved:
        item.resolved = True
        item.resolved_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(item)
    return item
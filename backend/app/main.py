from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import init_db, get_db
from app.db.models import Event as EventModel
from app.ingestion.daemon_poller import poller
from app.attention_router.queue_service import start_queue_service
from app.attention_router.router import router as attention_router


app = FastAPI(
    title="Attention Router",
    description="Intelligence layer for Agent Orchestrator: ranked urgency queue, auto-approve engine, risk-scored PR briefing",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    await poller.start()
    await start_queue_service()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await poller.stop()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict:
    return {"status": "ready"}


# Temporary debug endpoint — remove before production
@app.get("/debug/recent-events")
def recent_events(db: Session = Depends(get_db), limit: int = 10):
    stmt = select(EventModel).order_by(desc(EventModel.received_at)).limit(limit)
    events = db.execute(stmt).scalars().all()
    return [
        {
            "id": e.id,
            "session_id": e.session_id,
            "event_type": e.event_type,
            "received_at": e.received_at.isoformat() + "Z",
            "normalized_payload": e.normalized_payload,
        }
        for e in events
    ]


# Router mounts
app.include_router(attention_router, prefix="/api/v1", tags=["attention"])

# Router mounts — imported as no-ops for now since module logic not yet implemented
# TODO: uncomment and implement routers after CTO planning review
# from app.policy_gate.router import router as policy_gate
# from app.merge_digest.router import router as merge_digest
# app.include_router(policy_gate, prefix="/api/v1/policy", tags=["policy"])
# app.include_router(merge_digest, prefix="/api/v1/merge", tags=["merge"])
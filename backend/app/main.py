from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import init_db


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
def on_startup() -> None:
    init_db()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict:
    return {"status": "ready"}


# Router mounts — imported as no-ops for now since module logic not yet implemented
# TODO: uncomment and implement routers after CTO planning review
# from app.attention_router.router import router as attention_router
# from app.policy_gate.router import router as policy_gate
# from app.merge_digest.router import router as merge_digest
# app.include_router(attention_router, prefix="/api/v1/attention", tags=["attention"])
# app.include_router(policy_gate, prefix="/api/v1/policy", tags=["policy"])
# app.include_router(merge_digest, prefix="/api/v1/merge", tags=["merge"])
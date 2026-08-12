from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.attention_router.queue_service import get_ranked_queue, resolve_item
from app.attention_router.models import AttentionItem


router = APIRouter(prefix="/attention", tags=["attention"])


class AttentionItemOut(BaseModel):
    id: str
    session_id: str
    urgency_score: float
    reason: str
    idle_seconds: int
    created_at: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResolveRequest(BaseModel):
    # empty body for now; could add note later
    pass


@router.get("/queue", response_model=List[AttentionItemOut])
def list_queue(db: Session = Depends(get_db), limit: int = 50):
    """Return the current ranked attention queue."""
    items = get_ranked_queue(db, limit=limit)
    return items


@router.post("/{item_id}/resolve", response_model=AttentionItemOut)
def resolve_attention_item(item_id: str, _: ResolveRequest, db: Session = Depends(get_db)):
    """Mark an attention item as resolved (human handled it)."""
    item = resolve_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Attention item not found")
    return item
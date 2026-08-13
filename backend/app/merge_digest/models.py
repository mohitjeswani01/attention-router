import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class DigestEntry(Base):
    __tablename__ = "digest_entries"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: __import__("uuid").uuid4().hex)
    pr_id = Column(UUID(as_uuid=False), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False, default=0.0)
    risk_factors = Column(JSON, nullable=False, default=list)  # list of strings
    summary_text = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    pull_request = relationship("PullRequest")
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ActivityState(str, enum.Enum):
    ACTIVE = "active"
    IDLE = "idle"
    WAITING_INPUT = "waiting_input"
    BLOCKED = "blocked"
    EXITED = "exited"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=False), primary_key=True)
    project_id = Column(UUID(as_uuid=False), nullable=False)
    agent_type = Column(String, nullable=True)
    activity_state = Column(Enum(ActivityState, native_enum=False), nullable=False, default=ActivityState.IDLE)
    status = Column(String, nullable=True)  # computed display status from AO
    pr_url = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("Event", back_populates="session", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=False), primary_key=True)
    session_id = Column(UUID(as_uuid=False), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    raw_payload = Column(JSON, nullable=False)
    normalized_payload = Column(JSON, nullable=False)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    session = relationship("Session", back_populates="events")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(UUID(as_uuid=False), primary_key=True)
    session_id = Column(UUID(as_uuid=False), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False)
    repo = Column(String, nullable=False)
    title = Column(String, nullable=True)
    state = Column(String, nullable=False)  # open, merged, closed
    risk_level = Column(String, nullable=True)  # for merge_digest later
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("Session")
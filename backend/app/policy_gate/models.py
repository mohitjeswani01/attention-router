import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PolicyAction(str, enum.Enum):
    AUTO_APPROVE = "auto_approve"
    ESCALATE = "escalate"


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: __import__("uuid").uuid4().hex)
    name = Column(String, nullable=False)
    condition_type = Column(String, nullable=False)  # command_pattern, file_path_pattern, pr_label
    pattern = Column(String, nullable=False)  # regex or glob
    action = Column(Enum(PolicyAction, native_enum=False), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: __import__("uuid").uuid4().hex)
    session_id = Column(UUID(as_uuid=False), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    pr_id = Column(UUID(as_uuid=False), ForeignKey("pull_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_id = Column(UUID(as_uuid=False), ForeignKey("policy_rules.id", ondelete="SET NULL"), nullable=True)
    decision = Column(String, nullable=False)  # auto_approve, escalate, manual
    reason = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    session = relationship("Session")
    pull_request = relationship("PullRequest")
    rule = relationship("PolicyRule")
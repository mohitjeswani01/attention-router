from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.policy_gate.models import PolicyRule, ApprovalDecision, PolicyAction
from app.policy_gate.rules_engine import evaluate_command, evaluate_file_paths, decide_action
from app.policy_gate.action_executor import execute_decision
from app.policy_gate.default_policies import seed_default_rules

router = APIRouter(prefix="/policy", tags=["policy"])


class PolicyRuleCreate(BaseModel):
    name: str
    condition_type: str
    pattern: str
    action: str
    enabled: bool = True


class PolicyRuleOut(BaseModel):
    id: str
    name: str
    condition_type: str
    pattern: str
    action: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApprovalDecisionOut(BaseModel):
    id: str
    session_id: Optional[str]
    pr_id: Optional[str]
    rule_id: Optional[str]
    decision: str
    reason: Optional[str]
    decided_at: datetime

    class Config:
        from_attributes = True


class EvaluateRequest(BaseModel):
    # For manual testing
    command: Optional[str] = None
    file_paths: Optional[List[str]] = None
    pr_labels: Optional[List[str]] = None


class EvaluateResponse(BaseModel):
    matched_rules: List[PolicyRuleOut]
    decision: Optional[str]


@router.get("/rules", response_model=List[PolicyRuleOut])
def list_rules(db: Session = Depends(get_db)):
    return db.query(PolicyRule).all()


@router.post("/rules", response_model=PolicyRuleOut)
def create_rule(payload: PolicyRuleCreate, db: Session = Depends(get_db)):
    try:
        action = PolicyAction(payload.action)
    except ValueError:
        raise HTTPException(400, "action must be auto_approve or escalate")
    rule = PolicyRule(**payload.dict(), action=action)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(payload: EvaluateRequest, db: Session = Depends(get_db)):
    matched = []
    if payload.command:
        r = evaluate_command(db, payload.command)
        if r:
            matched.append(r)
    if payload.file_paths:
        matched.extend(evaluate_file_paths(db, payload.file_paths))
    if payload.pr_labels:
        r = evaluate_pr_labels(db, payload.pr_labels)
        if r:
            matched.append(r)
    decision = decide_action(matched)
    return EvaluateResponse(matched_rules=matched, decision=decision.value if decision else None)


@router.get("/decisions", response_model=List[ApprovalDecisionOut])
def list_decisions(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(ApprovalDecision).order_by(ApprovalDecision.decided_at.desc()).limit(limit).all()


# Helper to record a decision (used by other modules)
def record_decision(db: Session, *, session_id: Optional[str], pr_id: Optional[str],
                    rule_id: Optional[str], decision: PolicyAction, reason: str) -> ApprovalDecision:
    dec = ApprovalDecision(
        session_id=session_id,
        pr_id=pr_id,
        rule_id=rule_id,
        decision=decision.value,
        reason=reason,
    )
    db.add(dec)
    db.commit()
    db.refresh(dec)
    return dec
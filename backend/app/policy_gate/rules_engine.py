import re
from typing import Optional, List
from sqlalchemy.orm import Session

from app.policy_gate.models import PolicyRule, PolicyAction


def evaluate_command(db: Session, command: str) -> Optional[PolicyRule]:
    """Return first matching rule for a command (auto_approve or escalate)."""
    rules = db.query(PolicyRule).filter(
        PolicyRule.enabled == True,
        PolicyRule.condition_type == "command_pattern"
    ).all()
    for rule in rules:
        if re.search(rule.pattern, command, re.IGNORECASE):
            return rule
    return None


def evaluate_file_paths(db: Session, file_paths: List[str]) -> List[PolicyRule]:
    """Return all matching rules for given file paths."""
    rules = db.query(PolicyRule).filter(
        PolicyRule.enabled == True,
        PolicyRule.condition_type == "file_path_pattern"
    ).all()
    matched = []
    for rule in rules:
        if any(re.search(rule.pattern, fp) for fp in file_paths):
            matched.append(rule)
    return matched


def evaluate_pr_labels(db: Session, labels: List[str]) -> Optional[PolicyRule]:
    """Match PR label rules."""
    rules = db.query(PolicyRule).filter(
        PolicyRule.enabled == True,
        PolicyRule.condition_type == "pr_label"
    ).all()
    for rule in rules:
        if rule.pattern in labels:
            return rule
    return None


def decide_action(rules: List[PolicyRule]) -> PolicyAction:
    """If any rule is ESCALATE, escalate; else if any AUTO_APPROVE, approve; else None."""
    for r in rules:
        if r.action == PolicyAction.ESCALATE:
            return PolicyAction.ESCALATE
    for r in rules:
        if r.action == PolicyAction.AUTO_APPROVE:
            return PolicyAction.AUTO_APPROVE
    return None
import os
import httpx
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import PullRequest as PullRequestModel
from app.policy_gate.models import ApprovalDecision, PolicyAction


GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # set in .env


async def _gh_request(method: str, path: str, json=None):
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not configured")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method, f"{GITHUB_API}{path}", headers=headers, json=json)
        resp.raise_for_status()
        return resp.json()


async def approve_pr(db: Session, pr_id: str, decision: ApprovalDecision) -> None:
    """Approve the PR via GitHub API and post a comment."""
    pr = db.get(PullRequestModel, pr_id)
    if not pr:
        raise ValueError("PullRequest not found")
    # GitHub expects owner/repo and pull number
    # Assuming repo format "owner/repo"
    owner_repo = pr.repo  # expect "owner/repo"
    # Approve review
    await _gh_request("POST", f"/repos/{owner_repo}/pulls/{pr.pr_number}/reviews", json={
        "event": "APPROVE",
        "body": f"Auto-approved by policy rule {decision.rule_id}: {decision.reason}"
    })
    # Optionally add label
    await _gh_request("POST", f"/repos/{owner_repo}/issues/{pr.pr_number}/labels", json={"labels": ["auto-approved"]})


async def escalate_pr(db: Session, pr_id: str, decision: ApprovalDecision) -> None:
    """Add escalation label and comment."""
    pr = db.get(PullRequestModel, pr_id)
    if not pr:
        raise ValueError("PullRequest not found")
    owner_repo = pr.repo
    await _gh_request("POST", f"/repos/{owner_repo}/issues/{pr.pr_number}/labels", json={"labels": ["needs-human-review"]})
    await _gh_request("POST", f"/repos/{owner_repo}/issues/{pr.pr_number}/comments", json={
        "body": f"Escalated by policy rule {decision.rule_id}: {decision.reason}"
    })


async def execute_decision(db: Session, decision: ApprovalDecision) -> None:
    """Run the appropriate GitHub action based on decision."""
    if decision.decision == PolicyAction.AUTO_APPROVE.value and decision.pr_id:
        await approve_pr(db, decision.pr_id, decision)
    elif decision.decision == PolicyAction.ESCALATE.value and decision.pr_id:
        await escalate_pr(db, decision.pr_id, decision)
    # else manual – no action
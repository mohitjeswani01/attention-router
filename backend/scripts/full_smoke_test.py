#!/usr/bin/env python3
"""
Full smoke test for the attention-router backend.
Clears all seeded/fake data, reseeds from scratch, recomputes urgency,
and hits all key business logic directly in-process.
Prints a clean pass/fail summary for each of the three modules.
"""

import asyncio
import sys
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db
from app.db.models import Session as SessionModel, PullRequest, Event
from app.policy_gate.models import PolicyRule, ApprovalDecision, PolicyAction
from app.attention_router.models import AttentionItem
from app.merge_digest.models import DigestEntry
from app.attention_router.scoring import compute_urgency
from app.attention_router.queue_service import _recompute_and_upsert
from app.policy_gate.rules_engine import evaluate_command, evaluate_file_paths, decide_action
from app.policy_gate.default_policies import seed_default_rules
from app.merge_digest.digest_builder import build_digest
from app.merge_digest.risk_scoring import compute_risk


FAKE_SESSION_IDS = [
    "a1b2c3d4-1111-4222-8333-000000000001",
    "b2c3d4e5-2222-4333-8444-000000000002",
    "c3d4e5f6-3333-4444-8555-000000000003",
    "d4e5f6a7-4444-4555-8666-000000000004",
]
FAKE_PR_NUMBERS = [101, 102, 103]


def clear_all_data(db: Session):
    """Clear all fake/seeded data for a clean slate."""
    # Delete in FK-safe order
    db.query(AttentionItem).delete(synchronize_session=False)
    db.query(DigestEntry).delete(synchronize_session=False)
    db.query(ApprovalDecision).delete(synchronize_session=False)
    db.query(Event).filter(Event.session_id.in_(FAKE_SESSION_IDS)).delete(synchronize_session=False)
    db.query(PullRequest).filter(PullRequest.pr_number.in_(FAKE_PR_NUMBERS)).delete(synchronize_session=False)
    db.query(SessionModel).filter(SessionModel.id.in_(FAKE_SESSION_IDS)).delete(synchronize_session=False)
    db.query(PolicyRule).delete(synchronize_session=False)
    db.commit()


def seed_sessions(db: Session):
    """Seed the 4 fake sessions with known IDs."""
    from datetime import datetime, timedelta
    from app.db.models import ActivityState

    now = datetime.utcnow()
    sessions_data = [
        {
            "id": FAKE_SESSION_IDS[0],
            "project_id": "11111111-1111-1111-1111-111111111111",
            "agent_type": "claude",
            "activity_state": ActivityState.IDLE,
            "status": "completed",
            "pr_url": "https://github.com/myorg/docs-repo/pull/101",
            "created_at": now - timedelta(hours=3),
            "updated_at": now - timedelta(hours=2),
        },
        {
            "id": FAKE_SESSION_IDS[1],
            "project_id": "22222222-2222-2222-2222-222222222222",
            "agent_type": "codex",
            "activity_state": ActivityState.EXITED,
            "status": "completed",
            "pr_url": "https://github.com/myorg/legacy/pull/103",
            "created_at": now - timedelta(days=11),
            "updated_at": now - timedelta(days=10),
        },
        {
            "id": FAKE_SESSION_IDS[2],
            "project_id": "33333333-3333-3333-3333-333333333333",
            "agent_type": "claude",
            "activity_state": ActivityState.WAITING_INPUT,
            "status": "needs_input",
            "pr_url": "https://github.com/myorg/app/pull/102",
            "created_at": now - timedelta(hours=2),
            "updated_at": now - timedelta(minutes=10),
        },
        {
            "id": FAKE_SESSION_IDS[3],
            "project_id": "44444444-4444-4444-4444-444444444444",
            "agent_type": "codex",
            "activity_state": ActivityState.ACTIVE,
            "status": "working",
            "pr_url": None,
            "created_at": now - timedelta(minutes=30),
            "updated_at": now - timedelta(minutes=1),
        },
    ]

    for data in sessions_data:
        sess = SessionModel(**data)
        db.add(sess)
    db.commit()


def seed_prs(db: Session):
    """Seed the 3 fake PRs with events."""
    import uuid
    from datetime import datetime, timedelta

    sessions = {s.id: s for s in db.query(SessionModel).filter(SessionModel.id.in_(FAKE_SESSION_IDS)).all()}
    sess_list = [sessions[sid] for sid in FAKE_SESSION_IDS[:3] if sid in sessions]

    if len(sess_list) < 3:
        raise RuntimeError("Expected 3 sessions for PR seeding")

    now = datetime.utcnow()
    pr_data = [
        {
            "session": sess_list[0],
            "pr_number": 101,
            "repo": "myorg/docs-repo",
            "title": "Update README",
            "state": "open",
            "files": ["README.md", "docs/guide.md"],
            "ci_conclusion": "success",
            "updated_at": now - timedelta(hours=2),
        },
        {
            "session": sess_list[2],
            "pr_number": 102,
            "repo": "myorg/app",
            "title": "Update Dockerfile",
            "state": "open",
            "files": ["Dockerfile", "src/main.py"],
            "ci_conclusion": "failure",
            "updated_at": now - timedelta(days=1),
        },
        {
            "session": sess_list[1],
            "pr_number": 103,
            "repo": "myorg/legacy",
            "title": "Refactor auth module",
            "state": "open",
            "files": ["auth/handlers.py", "auth/middleware.py", "config/settings.yaml"],
            "ci_conclusion": "success",
            "updated_at": now - timedelta(days=10),
        },
    ]

    for data in pr_data:
        sess = data["session"]
        pr = PullRequest(
            id=str(uuid.uuid4()),
            session_id=sess.id,
            pr_number=data["pr_number"],
            repo=data["repo"],
            title=data["title"],
            state=data["state"],
            created_at=data["updated_at"],
            updated_at=data["updated_at"],
        )
        db.add(pr)
        db.flush()

        ev_pr = Event(
            id=str(uuid.uuid4()),
            session_id=sess.id,
            event_type="pr.updated",
            raw_payload={"id": pr.id, "number": data["pr_number"], "repo": data["repo"], "files": data["files"]},
            normalized_payload={
                "id": str(uuid.uuid4()),
                "event_type": "pr.updated",
                "session_id": sess.id,
                "operation": "UPDATE",
                "table": "pull_requests",
                "payload": {"id": pr.id, "number": data["pr_number"], "repo": data["repo"], "files": data["files"]},
                "received_at": now.isoformat() + "Z",
                "source": "cdc_sse",
            },
            received_at=now,
        )
        db.add(ev_pr)

        ev_check = Event(
            id=str(uuid.uuid4()),
            session_id=sess.id,
            event_type="pr_check.updated",
            raw_payload={"pr_id": pr.id, "conclusion": data["ci_conclusion"]},
            normalized_payload={
                "id": str(uuid.uuid4()),
                "event_type": "pr_check.updated",
                "session_id": sess.id,
                "operation": "UPDATE",
                "table": "pr_checks",
                "payload": {"pr_id": pr.id, "conclusion": data["ci_conclusion"]},
                "received_at": now.isoformat() + "Z",
                "source": "cdc_sse",
            },
            received_at=now,
        )
        db.add(ev_check)

    db.commit()


def seed_policies(db: Session):
    """Seed default policy rules and audit log decisions."""
    seed_default_rules(db)


async def recompute_all_urgency(db: Session):
    """Recompute urgency for all fake sessions."""
    sessions = db.query(SessionModel).filter(SessionModel.id.in_(FAKE_SESSION_IDS)).all()
    for sess in sessions:
        await _recompute_and_upsert(sess.id)


def test_attention_router(db: Session) -> tuple[bool, str]:
    """Test Attention Router module: compute_urgency and queue service."""
    try:
        sessions = db.query(SessionModel).filter(SessionModel.id.in_(FAKE_SESSION_IDS)).all()
        events = db.query(Event).filter(Event.session_id.in_(FAKE_SESSION_IDS)).all()

        results = []
        for sess in sessions:
            sess_events = [e for e in events if e.session_id == sess.id]
            score, reason, idle_sec = compute_urgency(sess, sess_events)
            results.append((sess.id[:8], sess.activity_state.value, score, reason, idle_sec))

        idle_sess = next(r for r in results if r[1] == "idle")
        exited_sess = next(r for r in results if r[1] == "exited")
        waiting_sess = next(r for r in results if r[1] == "waiting_input")
        active_sess = next(r for r in results if r[1] == "active")

        checks = [
            idle_sess[2] > 0,  # IDLE should have some score
            exited_sess[2] == 0 and exited_sess[3] == "healthy",  # EXITED should be healthy
            waiting_sess[3] == "idle_on_approval",  # WAITING_INPUT should be idle_on_approval
            active_sess[3] == "working",  # ACTIVE should be working
        ]

        if all(checks):
            return True, f"Attention Router: PASS - {results}"
        else:
            return False, f"Attention Router: FAIL - {results} (checks: {checks})"
    except Exception as e:
        return False, f"Attention Router: ERROR - {e}"


def test_policy_gate(db: Session) -> tuple[bool, str]:
    """Test Policy Gate module: rules_engine."""
    try:
        rule_ls = evaluate_command(db, "ls -la")
        rule_rm = evaluate_command(db, "rm -rf /tmp/test")
        rule_cat = evaluate_command(db, "cat file.txt")

        rules_md = evaluate_file_paths(db, ["README.md", "docs/guide.md"])
        rules_docker = evaluate_file_paths(db, ["Dockerfile", "src/main.py"])
        rules_ci = evaluate_file_paths(db, [".github/workflows/ci.yml"])

        action_ls = decide_action([rule_ls]) if rule_ls else None
        action_rm = decide_action([rule_rm]) if rule_rm else None
        action_md = decide_action(rules_md)
        action_docker = decide_action(rules_docker)
        action_ci = decide_action(rules_ci)

        checks = [
            rule_ls and rule_ls.name == "allow_ls",
            rule_rm and rule_rm.name == "escalate_rm_rf",
            rule_cat and rule_cat.name == "allow_cat",
            action_ls == PolicyAction.AUTO_APPROVE,
            action_rm == PolicyAction.ESCALATE,
            action_md == PolicyAction.AUTO_APPROVE,
            action_docker == PolicyAction.ESCALATE,
            action_ci == PolicyAction.ESCALATE,
        ]

        if all(checks):
            return True, "Policy Gate: PASS - all rule evaluations correct"
        else:
            return False, f"Policy Gate: FAIL - checks: {checks}"
    except Exception as e:
        return False, f"Policy Gate: ERROR - {e}"


def test_merge_digest(db: Session) -> tuple[bool, str]:
    """Test Merge Digest module: compute_risk and digest_builder."""
    try:
        prs = db.query(PullRequest).filter(PullRequest.pr_number.in_(FAKE_PR_NUMBERS)).all()
        pr_by_num = {pr.pr_number: pr for pr in prs}

        risk_results = {}
        for num in FAKE_PR_NUMBERS:
            pr = pr_by_num[num]
            score, factors = compute_risk(pr, db)
            risk_results[num] = (score, factors)

        digest = build_digest(db)

        checks = [
            len(digest["ready_to_merge"]) >= 1,
            any(p["pr_number"] == 101 for p in digest["ready_to_merge"]),
            len(digest["in_progress"]) >= 1,
            any(p["pr_number"] == 102 for p in digest["in_progress"]),
            len(digest["needs_review"]) >= 1,
            any(p["pr_number"] == 103 for p in digest["needs_review"]),
            risk_results[101][0] <= 30,  # low risk
            risk_results[103][0] > 30,   # medium/high risk
        ]

        if all(checks):
            return True, f"Merge Digest: PASS - buckets: ready={len(digest['ready_to_merge'])}, review={len(digest['needs_review'])}, progress={len(digest['in_progress'])}"
        else:
            return False, f"Merge Digest: FAIL - checks: {checks}, digest: {digest}, risks: {risk_results}"
    except Exception as e:
        return False, f"Merge Digest: ERROR - {e}"


def main():
    """Run full smoke test."""
    print("=" * 60)
    print("FULL SMOKE TEST - Attention Router Backend")
    print("=" * 60)

    init_db()
    db: Session = SessionLocal()

    try:
        print("\n[1/5] Clearing all seeded data...")
        clear_all_data(db)
        print("    OK")

        print("[2/5] Seeding sessions...")
        seed_sessions(db)
        print("    OK")

        print("[3/5] Seeding PRs and events...")
        seed_prs(db)
        print("    OK")

        print("[4/5] Seeding policy rules and decisions...")
        seed_policies(db)
        print("    OK")

        print("[5/5] Recomputing urgency...")
        asyncio.run(recompute_all_urgency(db))
        print("    OK")

        print("\n" + "=" * 60)
        print("MODULE TESTS")
        print("=" * 60)

        results = []

        print("\nTesting Attention Router...")
        ok, msg = test_attention_router(db)
        results.append(("Attention Router", ok, msg))
        print(f"  {msg}")

        print("\nTesting Policy Gate...")
        ok, msg = test_policy_gate(db)
        results.append(("Policy Gate", ok, msg))
        print(f"  {msg}")

        print("\nTesting Merge Digest...")
        ok, msg = test_merge_digest(db)
        results.append(("Merge Digest", ok, msg))
        print(f"  {msg}")

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        all_pass = True
        for name, ok, msg in results:
            status = "PASS" if ok else "FAIL"
            print(f"  {name}: {status}")
            if not ok:
                all_pass = False

        if all_pass:
            print("\n✓ ALL TESTS PASSED")
            return 0
        else:
            print("\n✗ SOME TESTS FAILED")
            return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
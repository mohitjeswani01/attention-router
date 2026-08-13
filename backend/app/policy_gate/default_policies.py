"""
Default policy rules and sample decisions seeded on first run.
Each rule: (name, condition_type, pattern, action)
"""
from datetime import datetime, timedelta
from app.policy_gate.models import PolicyRule, ApprovalDecision, PolicyAction

DEFAULT_RULES = [
    # Auto-approve read‑only commands
    ("allow_ls", "command_pattern", r"^\s*ls(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    ("allow_cat", "command_pattern", r"^\s*cat(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    ("allow_grep", "command_pattern", r"^\s*grep(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    ("allow_git_status", "command_pattern", r"^\s*git\s+status(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    ("allow_git_diff", "command_pattern", r"^\s*git\s+diff(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    ("allow_git_log", "command_pattern", r"^\s*git\s+log(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    # Lint / format tool runs
    ("allow_black", "command_pattern", r"^\s*black(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    ("allow_ruff", "command_pattern", r"^\s*ruff(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    ("allow_eslint", "command_pattern", r"^\s*eslint(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    ("allow_prettier", "command_pattern", r"^\s*prettier(\s+.*)?$", PolicyAction.AUTO_APPROVE),
    # Doc‑only file changes (by path pattern)
    ("allow_md_files", "file_path_pattern", r".*\.md$", PolicyAction.AUTO_APPROVE),
    ("allow_rst_files", "file_path_pattern", r".*\.rst$", PolicyAction.AUTO_APPROVE),
    ("allow_txt_files", "file_path_pattern", r".*\.txt$", PolicyAction.AUTO_APPROVE),
    # Escalate risky config / secret files
    ("escalate_package_json", "file_path_pattern", r".*package\.json$", PolicyAction.ESCALATE),
    ("escalate_requirements_txt", "file_path_pattern", r".*requirements\.txt$", PolicyAction.ESCALATE),
    ("escalate_dockerfile", "file_path_pattern", r".*Dockerfile$", PolicyAction.ESCALATE),
    ("escalate_env_files", "file_path_pattern", r".*\.env(\..*)?$", PolicyAction.ESCALATE),
    ("escalate_ci_config", "file_path_pattern", r".*\.(github|gitlab|circleci|azure-pipelines)/.*\.ya?ml$", PolicyAction.ESCALATE),
    # Escalate dangerous command patterns
    ("escalate_rm_rf", "command_pattern", r"^\s*rm\s+.*-rf\b", PolicyAction.ESCALATE),
    ("escalate_sudo", "command_pattern", r"^\s*sudo\b", PolicyAction.ESCALATE),
    ("escalate_curl_pipe_sh", "command_pattern", r"curl\s+.*\|\s*(sh|bash)\b", PolicyAction.ESCALATE),
    ("escalate_wget_pipe_sh", "command_pattern", r"wget\s+.*\|\s*(sh|bash)\b", PolicyAction.ESCALATE),
]


def seed_default_rules(db):
    """Insert default rules and sample decisions if tables are empty."""
    if db.query(PolicyRule).first() is None:
        for name, ctype, pattern, action in DEFAULT_RULES:
            rule = PolicyRule(name=name, condition_type=ctype, pattern=pattern, action=action, enabled=True)
            db.add(rule)
        db.commit()

    seed_default_decisions(db)


def seed_default_decisions(db):
    """Insert audit log sample decisions if approval_decisions table is empty."""
    if db.query(ApprovalDecision).first() is not None:
        return

    # Map rule names to rule IDs
    rules = {r.name: r.id for r in db.query(PolicyRule).all()}
    now = datetime.utcnow()

    # Query existing session IDs if present
    from app.db.models import Session as SessionModel, PullRequest as PRModel
    sessions = [s.id for s in db.query(SessionModel).all()]
    prs = {pr.pr_number: pr.id for pr in db.query(PRModel).all()}

    sid1 = sessions[0] if len(sessions) > 0 else "a1b2c3d4-1111-4222-8333-000000000001"
    sid2 = sessions[2] if len(sessions) > 2 else "c3d4e5f6-3333-4444-8555-000000000003"
    sid3 = sessions[3] if len(sessions) > 3 else "d4e5f6a7-4444-4555-8666-000000000004"

    decisions = [
        ApprovalDecision(
            session_id=sid1,
            pr_id=prs.get(101),
            rule_id=rules.get("allow_md_files"),
            decision="auto_approve",
            reason="Matched rule 'allow_md_files': doc changes to README.md auto-approved",
            decided_at=now - timedelta(minutes=15),
        ),
        ApprovalDecision(
            session_id=sid1,
            pr_id=None,
            rule_id=rules.get("allow_ls"),
            decision="auto_approve",
            reason="Matched rule 'allow_ls': command 'ls -la' auto-approved",
            decided_at=now - timedelta(minutes=30),
        ),
        ApprovalDecision(
            session_id=sid2,
            pr_id=prs.get(102),
            rule_id=rules.get("escalate_dockerfile"),
            decision="escalate",
            reason="Matched rule 'escalate_dockerfile': modifications to Dockerfile require human review",
            decided_at=now - timedelta(minutes=45),
        ),
        ApprovalDecision(
            session_id=sid2,
            pr_id=None,
            rule_id=rules.get("escalate_rm_rf"),
            decision="escalate",
            reason="Matched rule 'escalate_rm_rf': command 'rm -rf /tmp/build' requires human approval",
            decided_at=now - timedelta(hours=1, minutes=15),
        ),
        ApprovalDecision(
            session_id=sid3,
            pr_id=None,
            rule_id=rules.get("allow_git_status"),
            decision="auto_approve",
            reason="Matched rule 'allow_git_status': command 'git status' auto-approved",
            decided_at=now - timedelta(hours=2),
        ),
    ]

    for d in decisions:
        # Check FK validity: if session_id is not in sessions table, set it to None to avoid FK constraint error
        if d.session_id and d.session_id not in sessions:
            d.session_id = None
        db.add(d)

    db.commit()
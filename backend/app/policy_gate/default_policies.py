"""
Default policy rules seeded on first run.
Each rule: (name, condition_type, pattern, action)
"""
from app.policy_gate.models import PolicyAction


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
    """Insert default rules if table empty."""
    from app.policy_gate.models import PolicyRule
    if db.query(PolicyRule).first() is None:
        for name, ctype, pattern, action in DEFAULT_RULES:
            rule = PolicyRule(name=name, condition_type=ctype, pattern=pattern, action=action, enabled=True)
            db.add(rule)
        db.commit()
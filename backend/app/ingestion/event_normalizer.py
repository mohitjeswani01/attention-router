import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.config import settings


def _generate_id() -> str:
    return str(uuid.uuid4())


def normalize_session(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw AO session object (from list_sessions or get_session) into the
    normalized payload we store in `Event.normalized_payload` for session snapshots.
    """
    return {
        "id": raw.get("id"),
        "project_id": raw.get("project_id"),
        "agent_type": raw.get("harness") or raw.get("agent_type"),
        "activity_state": raw.get("activity_state"),
        "status": raw.get("status"),  # computed display status from AO
        "pr_url": raw.get("pr_url"),
        "created_at": raw.get("created_at"),
        "updated_at": raw.get("updated_at"),
        "source": "session_snapshot",
        "received_at": datetime.utcnow().isoformat() + "Z",
    }


def normalize_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw CDC/SSE event from AO into our internal normalized shape.

    AO's CDC events (per architecture.md) contain:
      - seq, table_name, row_id, operation, old_data, new_data

    We flatten to a simpler representation:
      - event_type: e.g. "session.created", "session.updated", "pr.updated"
      - session_id: extracted from row_id or new_data
      - payload: the new_data (or old_data for deletes)
    """
    table = raw_event.get("table_name")
    operation = raw_event.get("operation")  # INSERT, UPDATE, DELETE
    row_id = raw_event.get("row_id")
    new_data = raw_event.get("new_data") or {}
    old_data = raw_event.get("old_data") or {}

    # Determine a friendly event_type
    if table == "sessions":
        event_type = f"session.{operation.lower()}"
        session_id = row_id or new_data.get("id") or old_data.get("id")
    elif table == "pull_requests":
        event_type = f"pr.{operation.lower()}"
        session_id = new_data.get("session_id") or old_data.get("session_id")
    elif table == "pr_checks":
        event_type = f"pr_check.{operation.lower()}"
        # session_id will be resolved later in daemon_poller by looking up the PullRequest row via pr_id
        session_id = None
    else:
        event_type = f"{table}.{operation.lower()}"
        session_id = row_id

    return {
        "id": _generate_id(),
        "event_type": event_type,
        "session_id": session_id,
        "operation": operation,
        "table": table,
        "payload": new_data if operation != "DELETE" else old_data,
        "received_at": datetime.utcnow().isoformat() + "Z",
        "source": "cdc_sse",
    }


def normalize_any(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatcher used by the poller: if the object looks like a CDC event (has table_name)
    we treat it as an event, otherwise assume it's a session snapshot.
    """
    if "table_name" in raw and "operation" in raw:
        return normalize_event(raw)
    return normalize_session(raw)
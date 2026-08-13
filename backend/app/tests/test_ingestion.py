import pytest
from unittest.mock import MagicMock, patch, ANY

from app.ingestion.daemon_poller import DaemonPoller
from app.ingestion.event_normalizer import normalize_session, normalize_event


def test_normalize_session_valid():
    raw = {
        "id": "sess-123",
        "project_id": "proj-456",
        "harness": "test-agent",
        "activity_state": "active",
        "status": "running",
        "pr_url": "http://example.com/pr/1",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T01:00:00Z",
    }
    norm = normalize_session(raw)
    assert norm["session_id"] == "sess-123"
    assert norm["id"] == "sess-123"
    assert norm["source"] == "session_snapshot"


def test_normalize_session_missing_id():
    raw = {
        "project_id": "proj-456",
        "harness": "test-agent",
        "activity_state": "idle",
    }
    norm = normalize_session(raw)
    assert norm.get("id") is None
    assert norm.get("session_id") is None


@pytest.mark.asyncio
async def test_process_raw_valid_session_snapshot():
    poller = DaemonPoller()
    raw = {
        "id": "sess-111",
        "project_id": "proj-222",
        "harness": "agent",
        "activity_state": "active",
        "status": "running",
        "pr_url": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T01:00:00Z",
    }

    with patch("app.ingestion.daemon_poller.session_scope") as mock_scope:
        mock_db = MagicMock()
        mock_scope.return_value.__enter__.return_value = mock_db
        mock_db.get.return_value = None

        await poller._process_raw(raw)

        # upsert_session should have been called (adds new Session)
        # and _insert_event should have been called because session_id present
        assert mock_db.add.call_count == 2  # session + event


@pytest.mark.asyncio
async def test_process_raw_invalid_session_snapshot_skips_event():
    poller = DaemonPoller()
    raw = {
        "project_id": "proj-222",
        "harness": "agent",
        "activity_state": "idle",
        # missing id
    }

    with patch("app.ingestion.daemon_poller.session_scope") as mock_scope:
        mock_db = MagicMock()
        mock_scope.return_value.__enter__.return_value = mock_db
        mock_db.get.return_value = None

        await poller._process_raw(raw)

        # upsert_session returns early, no add for Session
        # _insert_event should NOT be called because session_id is None
        assert mock_db.add.call_count == 0


@pytest.mark.asyncio
async def test_process_raw_pr_check_without_session_id_skips_event():
    poller = DaemonPoller()
    # Simulate a CDC pr_check event lacking session_id
    raw = {
        "table_name": "pr_checks",
        "operation": "INSERT",
        "row_id": "check-1",
        "new_data": {"id": "check-1", "pr_id": "pr-1"},
        "old_data": {},
    }

    with patch("app.ingestion.daemon_poller.session_scope") as mock_scope:
        mock_db = MagicMock()
        mock_scope.return_value.__enter__.return_value = mock_db
        # PullRequest not found, so session_id remains None
        mock_db.get.return_value = None

        await poller._process_raw(raw)

        # No event insert because session_id unresolved, and no session upsert
        assert mock_db.add.call_count == 0

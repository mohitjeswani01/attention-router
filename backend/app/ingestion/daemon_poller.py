import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from app.config import settings
from app.db.session import session_scope
from app.db.models import Session as SessionModel, Event as EventModel, PullRequest as PullRequestModel
from app.ingestion.daemon_client import DaemonClient, DaemonClientError
from app.ingestion.event_normalizer import normalize_any
from app.ingestion.event_bus import event_bus

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 10  # seconds


class DaemonPoller:
    """
    Background task that keeps the local DB in sync with the AO daemon.

    Strategy:
    1. Try to consume the SSE stream (`/api/v1/events`) – this is the primary realtime feed.
    2. If the SSE connection drops (any exception), fall back to polling `list_sessions`
       every `_POLL_INTERVAL` seconds.
    3. Every incoming raw event or session snapshot is normalized, persisted, and
       published on the in‑process `event_bus`.
    """

    def __init__(self):
        self._client = DaemonClient()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())
        logger.info("Daemon poller started")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            await self._task
        await self._client.close()
        logger.info("Daemon poller stopped")

    async def _run(self) -> None:
        # Primary loop – try SSE first, on failure fall back to polling loop
        while not self._stop_event.is_set():
            try:
                await self._consume_sse()
            except DaemonClientError as exc:
                logger.warning("SSE stream ended (%s). Falling back to polling.", exc)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.exception("Unexpected error in SSE consumer: %s", exc)

            if self._stop_event.is_set():
                break

            # Back‑off before polling or retrying SSE
            await asyncio.sleep(2)

        # If we exit the while because of stop_event, ensure polling loop not running
        # (the polling loop is only entered when SSE fails permanently)
        # but we keep a simple polling fallback here for completeness.
        await self._polling_loop()

    async def _consume_sse(self) -> None:
        async for raw_event in self._client.stream_events():
            if self._stop_event.is_set():
                break
            await self._process_raw(raw_event)

    async def _polling_loop(self) -> None:
        logger.info("Entering polling fallback (every %ss)", _POLL_INTERVAL)
        while not self._stop_event.is_set():
            try:
                sessions = await self._client.list_sessions()
                for sess in sessions:
                    await self._process_raw(sess)
            except DaemonClientError as exc:
                logger.warning("Polling list_sessions failed: %s", exc)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Unexpected error during polling: %s", exc)

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=_POLL_INTERVAL)
            except asyncio.TimeoutError:
                continue  # normal tick

    async def _process_raw(self, raw: dict) -> None:
        """
        Normalize, persist (Event + upsert Session/PR snapshots), and publish.
        """
        normalized = normalize_any(raw)
        table = normalized.get("table")

        # Persist
        with session_scope() as db:
            # Handle pull_requests table: upsert PullRequest row
            if table == "pull_requests":
                self._upsert_pull_request(db, normalized)
            # Handle pr_checks: try to resolve session_id via PullRequest
            elif table == "pr_checks":
                self._resolve_pr_check_session_id(db, normalized)

            # Always upsert session snapshot if present
            self._upsert_session(db, normalized)
            self._insert_event(db, normalized)

        # Publish for downstream modules
        event_bus.publish(normalized)

    # ------------------------------------------------------------------ DB helpers
    def _upsert_session(self, db, norm: dict) -> None:
        """
        Insert or update the Session row based on the normalized snapshot.
        Only called for session‑type payloads (has session_id and activity_state).
        """
        session_id = norm.get("session_id") or norm.get("id")
        if not session_id:
            return

        sess = db.get(SessionModel, session_id)
        if sess is None:
            sess = SessionModel(id=session_id)
            db.add(sess)

        # Map fields – be defensive with .get
        sess.project_id = norm.get("project_id") or sess.project_id
        sess.agent_type = norm.get("agent_type") or sess.agent_type
        activity = norm.get("activity_state")
        if activity:
            try:
                from app.db.models import ActivityState
                sess.activity_state = ActivityState(activity)
            except ValueError:
                logger.warning("Unknown activity_state %s for session %s", activity, session_id)
        sess.status = norm.get("status") or sess.status
        sess.pr_url = norm.get("pr_url") or sess.pr_url
        # timestamps are handled by DB defaults / onupdate

    def _insert_event(self, db, norm: dict) -> None:
        """
        Insert a new Event row. `norm` already contains the normalized payload.
        """
        event = EventModel(
            id=norm.get("id") or __import__("uuid").uuid4().hex,
            session_id=norm.get("session_id"),
            event_type=norm.get("event_type", "unknown"),
            raw_payload=norm.get("payload", {}),   # store the original payload as raw
            normalized_payload=norm,
            received_at=norm.get("received_at") and __import__("datetime").datetime.fromisoformat(
                norm["received_at"].replace("Z", "+00:00")
            ) or __import__("datetime").datetime.utcnow(),
        )
        db.add(event)

    # ------------------------------------------------------------------ PR helpers
    def _upsert_pull_request(self, db, norm: dict) -> None:
        """Insert or update PullRequest from normalized pull_requests CDC event."""
        payload = norm.get("payload", {})
        pr_id = payload.get("id")
        if not pr_id:
            return
        pr = db.get(PullRequestModel, pr_id)
        if pr is None:
            pr = PullRequestModel(id=pr_id)
            db.add(pr)
        pr.session_id = payload.get("session_id") or pr.session_id
        pr.pr_number = payload.get("number") or pr.pr_number
        pr.repo = payload.get("repo") or pr.repo
        pr.title = payload.get("title") or pr.title
        pr.state = payload.get("state") or pr.state
        # risk_level left for later

    def _resolve_pr_check_session_id(self, db, norm: dict) -> None:
        """If pr_check event has pr_id in payload, look up PullRequest to set session_id."""
        payload = norm.get("payload", {})
        pr_id = payload.get("pr_id") or payload.get("pull_request_id")
        if not pr_id:
            return
        pr = db.get(PullRequestModel, pr_id)
        if pr and pr.session_id:
            norm["session_id"] = pr.session_id
        else:
            # Parent PR not yet persisted; log and leave session_id as None
            logger.debug("PullRequest %s not found for pr_check, session_id unavailable", pr_id)


# Singleton instance
poller = DaemonPoller()
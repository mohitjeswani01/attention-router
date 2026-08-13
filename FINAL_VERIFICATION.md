# Attention Router — Final Verification Checklist & Runbook

This document details the exact verification status of the Attention Router codebase, distinguishing between **automated/in-process verifications already completed** and **manual end-to-end verifications to be performed prior to hackathon judging**.

---

## Part 1 — Already Verified (Automated & In-Process)

The following components have been verified via automated test suites, production build compilers, and direct API response inspection.

### `✓` 1. Backend In-Process Smoke Test
* **Command**:
  ```bash
  cd backend
  PYTHONPATH=. python3 scripts/full_smoke_test.py
  ```
* **Status**: **PASSED** (`3/3` modules verified)
* **Verified Outcomes**:
  * Clears database tables cleanly without foreign key violations.
  * Seeds 4 fake sessions with distinct UUIDs (`a1b2c3d4...`, `b2c3d4e5...`, `c3d4e5f6...`, `d4e5f6a7...`).
  * Calculates urgency scores (`idle_on_approval` = `400.0`, `working` = `10.0`, `idle` = `5.0`, `exited` = `0.0`).
  * Evaluates command and file path policy rules against decision engine.
  * Generates Merge Digest risk scores and populates `ready_to_merge`, `needs_review`, and `in_progress` buckets.

### `✓` 2. Database Migration & Schema Setup
* **Command**:
  ```bash
  cd backend
  alembic upgrade head
  ```
* **Status**: **PASSED**
* **Verified Outcomes**:
  * Creates all 8 required tables: `sessions`, `events`, `pull_requests`, `attention_items`, `policy_rules`, `approval_decisions`, `digest_entries`, `alembic_version`.

### `✓` 3. Frontend Next.js Production Build
* **Command**:
  ```bash
  cd frontend
  npx next build
  ```
* **Status**: **PASSED**
* **Verified Outcomes**:
  * Compiled 100% successfully with `0` TypeScript type errors and `0` ESLint warnings.
  * Generated 7 static pages (`/`, `/_not-found`, `/queue`, `/policies`, `/digest`).

### `✓` 4. Backend REST API Endpoints
* **Commands**:
  ```bash
  curl -s http://localhost:8000/api/v1/attention/queue | python3 -m json.tool
  curl -s http://localhost:8000/api/v1/policy/decisions | python3 -m json.tool
  curl -s http://localhost:8000/api/v1/digest/today | python3 -m json.tool
  ```
* **Status**: **PASSED**
* **Verified Outcomes**:
  * `/attention/queue`: Returns 3 unresolved attention items ordered by urgency score descending.
  * `/policy/decisions`: Returns 5 audit log entries (`auto_approve` and `escalate`) with timestamps and rule details.
  * `/digest/today`: Returns executive summary headline and 3 PR buckets with risk factors.

---

## Part 2 — Pending Manual Verification (Pre-Demo Owner Runbook)

Perform these steps before recording the demo video or presenting to judges.

### Item 1 — Local Full-Stack Live Run

1. **Exact Command**:
   * Terminal 1 (Backend):
     ```bash
     cd backend
     PYTHONPATH=. python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
     ```
   * Terminal 2 (Frontend):
     ```bash
     cd frontend
     npm run dev
     ```
2. **Expected Output**:
   * Terminal 1 shows `Uvicorn running on http://0.0.0.0:8000`.
   * Terminal 2 shows `Ready in ...` on `http://localhost:3000`.
3. **Failure Signs**:
   * Port 8000 or 3000 already in use, or database connection refused.
4. **Remediation**:
   * Ensure PostgreSQL is running (`pg_isready`). Kill any stale uvicorn/next processes using `lsof -i :8000` / `lsof -i :3000`.

---

### Item 2 — Frontend UI Tab Walkthrough

1. **Exact UI Action**:
   * Open `http://localhost:3000` in Google Chrome / Brave.
   * Click **"View Live Queue"** button $\to$ navigates to `/queue`.
   * Click **`02 Policy Gate`** in header $\to$ navigates to `/policies`.
   * Click **`03 Merge Digest`** in header $\to$ navigates to `/digest`.
2. **Expected Output**:
   * `/queue` displays ranked sessions in left sidebar, selected session detail in middle, metadata in right rail.
   * `/policies` displays Auto Approved / Escalated counts, Policy Rules sidebar, and Audit Log cards.
   * `/digest` displays serif-italic summary, 3 columns, and expandable PR risk breakdown.
3. **Failure Signs**:
   * Blank red error banner or blank screen on any tab.
4. **Remediation**:
   * Confirm backend is running and run seed scripts:
     ```bash
     cd backend
     PYTHONPATH=. python3 scripts/seed_fake_sessions.py
     PYTHONPATH=. python3 scripts/seed_merge_digest.py
     ```

---

### Item 3 — Attention Item Resolution Flow

1. **Exact UI Action**:
   * Navigate to `http://localhost:3000/queue`.
   * Select top-ranked session `c3d4e5f6`.
   * Click the pink-to-cyan gradient button **"Mark as Resolved"**.
2. **Expected Output**:
   * Button shows loading spinner *"Resolving..."*, then item `c3d4e5f6` is removed from the queue. Next item automatically selects.
3. **Failure Signs**:
   * Button remains disabled or error pops up.
4. **Remediation**:
   * Check backend console logs for HTTP 500 or 404 on `POST /api/v1/attention/{item_id}/resolve`.

---

### Item 4 — Optional Live AO Daemon Integration Test

1. **Exact UI Action**:
   * Ensure Agent Orchestrator (AO) desktop app or CLI daemon is running at `http://127.0.0.1:3001`.
   * Verify daemon health:
     ```bash
     curl -s http://127.0.0.1:3001/healthz
     ```
   * Trigger an agent prompt in AO or run `ao spawn`.
2. **Expected Output**:
   * Attention Router's `daemon_poller.py` receives event via SSE stream `/api/v1/events` and recalculates queue.
3. **Failure Signs**:
   * `ConnectionRefusedError` in backend logs.
4. **Remediation**:
   * If AO daemon is not running during the demo, Attention Router uses its DB-backed seed data seamlessly. The UI and endpoints remain fully functional without the live daemon.

---

### Item 5 — Optional GitHub API Token Test

1. **Exact Action**:
   * Add `GITHUB_TOKEN=ghp_xxx` to `backend/.env`.
   * Restart backend server.
2. **Expected Output**:
   * `github_enrichment.py` fetches live commit/check run statuses for PRs.
3. **Failure Signs**:
   * GitHub API rate limit (403) or bad credentials (401).
4. **Remediation**:
   * If `GITHUB_TOKEN` is unset, Attention Router gracefully falls back to simulated/seeded PR check conclusions without throwing exceptions.

# Attention Router

> **Agent Orchestrator tells you what your agents are doing.**  
> **Attention Router tells you what *YOU* need to pay attention to.**

The intelligence and decision layer built for [Agent Orchestrator (AO)](https://github.com/Untrivial-ai/agent-orchestrator). Attention Router transforms unstructured event streams from multi-agent coding sessions into a ranked urgency queue, a deterministic policy gate for automated approvals, and an executive merge readiness briefing.

---

## The Gap

[Agent Orchestrator (AO)](https://github.com/Untrivial-ai/agent-orchestrator) is exceptional at orchestrating coding agents, managing isolated workspaces, tracking session lifecycles, and monitoring PR/CI state. However, AO's scope intentionally leaves three critical operational gaps open when scaling to fleets of autonomous agents:

> *"AO coordinates execution, but does not decide human priority, auto-approve routine commands, or quantify merge risk before pull requests land."*

Attention Router maps directly to these three documented boundaries:

| AO Scope Boundary | Attention Router Solution | Core Mechanism |
| :--- | :--- | :--- |
| **Does not prioritize human attention** | **`01` — Attention Queue** | Ranks blocked and failing agent sessions into a real-time urgency queue based on calculated blocker weights and live idle duration. |
| **Does not auto-approve safe actions** | **`02` — Policy Gate** | Evaluates agent command executions and file modifications against deterministic safety rules, auto-approving read-only operations while escalating high-risk edits. |
| **Does not risk-score PRs before merge** | **`03` — Merge Readiness Digest** | Quantifies PR risk scores based on file sensitivity, CI conclusions, and staleness, bucketing pull requests into actionable merge briefings. |

> **Attention Router is not a replacement for Agent Orchestrator — it is the intelligence layer above it.**

---

## Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │    Agent Orchestrator (AO Daemon)    │
                      │        http://127.0.0.1:3001         │
                      └──────────────────┬───────────────────┘
                                         │
                         Primary Signal  │ Real-time SSE / CDC Stream
                                         │ (/api/v1/events)
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    Attention Router Ingestion        │
                      │  (Event Normalizer & Async Bus)      │
                      └──────────┬────────────────┬──────────┘
                                 │                │
           Secondary Enrichment  │                │
            (GitHub REST API)    ▼                │
                      ┌──────────────────┐        │
                      │ SCM / PR Context │        │
                      └──────────┬───────┘        │
                                 │                │
                                 ▼                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          DECISION ENGINE LAYER                            │
├───────────────────────┬───────────────────────────┬───────────────────────┤
│ 01 — Attention Queue  │     02 — Policy Gate      │ 03 — Merge Digest     │
│                       │                           │                       │
│ Ranks sessions by     │ Auto-approves safe tool   │ Scores PR risk and    │
│ calculated urgency    │ calls; escalates risky    │ groups PRs into       │
│ score & idle duration │ commands & sensitive paths│ readiness buckets     │
└───────────┬───────────┴─────────────┬─────────────┴───────────┬───────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      ▼
                      ┌──────────────────────────────────────┐
                      │   Next.js 14 Dark Canvas Frontend    │
                      │     (Evidence & Citation UI)         │
                      └──────────────────────────────────────┘
```

### Signal Hierarchy
1. **Primary Signal — AO Local Loopback Daemon**: Subscribes directly to AO's Server-Sent Events (SSE) / Change-Data-Capture stream (`GET /api/v1/events`) at `http://127.0.0.1:3001`. Tracks raw session states (`active`, `idle`, `waiting_input`, `blocked`, `exited`) and agent activity hooks.
2. **Secondary Enrichment — GitHub API**: Enriches SCM events (PR labels, diff file lists, check run conclusions) to provide deep context without treating external APIs as the source of truth for local agent states.

---

## Core Modules

### `01` — Attention Queue (`/queue`)
Transforms a list of active sessions into a single ranked queue so human supervisors never waste time deciding where to look first.

* **Urgency Scoring Algorithm**:
  $$\text{Urgency Score} = \text{Base Score}(\text{Reason}) + (\text{Idle Seconds} \times \text{Weight})$$
* **Priority Hierarchy**:
  1. `idle_on_approval` (Base Score: `100.0` + `0.5 pts/sec`): Agent is blocked waiting on human input or permission. Highest priority.
  2. `ci_failed` (Base Score: `80.0`): Recent test suite or build failure detected on session PR.
  3. `review_requested` (Base Score: `60.0`): PR status transitioned to `changes_requested` or `review_pending`.
  4. `working` (Base Score: `10.0`): Agent is actively executing tasks. Visibility only.
  5. `idle` (Base Score: `5.0`): Baseline score for unblocked inactive sessions.
  6. `healthy` (Score: `0.0`): Exited/completed sessions automatically excluded from the queue.
* **Evidence Citation Language**: Displays explicit numbered citation blocks `[1]` `[2]` breakdown explaining exact score factors (e.g., *"Session waiting on approval for 10m (+300 pts)"*).
* **Actionable Resolution**: One-click "Mark as Resolved" action to clear handled items.

---

### `02` — Policy Gate (`/policies`)
A deterministic policy engine that eliminates human approval fatigue by automatically clearing low-risk agent operations while enforcing strict human-in-the-loop governance over sensitive modifications.

* **Command Pattern Rules**:
  * **Auto-Approve**: Read-only shell commands (`ls`, `cat`, `grep`, `git status`, `git diff`, `git log`) and linters/formatters (`black`, `ruff`, `eslint`, `prettier`).
  * **Escalate**: Destructive commands (`rm -rf`), root escalation (`sudo`), or unvetted remote scripts (`curl | bash`).
* **File Path Sensitivity Rules**:
  * **Auto-Approve**: Documentation files (`*.md`, `*.rst`, `*.txt`).
  * **Escalate**: Core configuration files (`package.json`, `requirements.txt`), Dockerfiles (`Dockerfile`), secrets (`.env`), and CI workflows (`.github/workflows/*.yml`).
* **Audit Trail**: Every evaluation generates an immutable `ApprovalDecision` record with timestamps, matched rule IDs, decisions (`auto_approve` vs `escalate`), and rationale.

---

### `03` — Merge Readiness Digest (`/digest`)
Synthesizes pull request statuses, CI test check conclusions, and agent activity histories into a daily executive briefing.

* **Risk Scoring Model**:
  Computes a composite risk score ($0 - 100$) by evaluating:
  * Touch points on sensitive file paths (`auth/`, `config/`, `Dockerfile`, etc.)
  * CI check run conclusions (`failure`, `success`, `pending`)
  * Session staleness (PRs open $> 7$ days without update)
* **Categorized Readiness Buckets**:
  * **Ready to Merge**: Low risk ($\le 30$), passing CI, recent activity.
  * **Needs Review**: High risk ($> 30$), sensitive path edits, or stale duration.
  * **In Progress**: Active agent sessions currently iterating on code.
* **Serif-Italic Executive Summary**: Automatically formats plain-English summary headlines highlighting exactly which PRs require human attention today.

---

## Technical Stack

### Backend
* **Language & Runtime**: Python 3.12
* **Web Framework**: FastAPI (Async ASGI)
* **Database & ORM**: PostgreSQL 16+, SQLAlchemy 2.0 (Declarative Unified Mapping)
* **Migrations**: Alembic
* **HTTP Client**: HTTPX (Async HTTP for AO daemon & GitHub enrichment)
* **Validation**: Pydantic v2 & `pydantic-settings`

### Frontend
* **Framework**: Next.js 14 (App Router, Server & Client Components)
* **Language**: TypeScript (Strict Mode)
* **Styling**: Tailwind CSS 3 with Custom CSS Variables
* **Design System & Aesthetics**:
  * Near-black dark canvas (`#0a0a0b`)
  * Modern typography pairing: **Inter** for UI, **Lora Italic** for serif pull-quotes/headlines, **JetBrains Mono** for technical IDs and code paths
  * Selective pink-to-cyan gradient CTA accents (`from-[#ec4899] to-[#06b6d4]`)
  * Numbered citation tags `[1]` `[2]` and shimmer pulse loading states

---

## Database Schema (`8` Tables)

1. `sessions` — Durable records of AO agent sessions (`id`, `project_id`, `agent_type`, `activity_state`, `status`, `pr_url`).
2. `events` — Normalized event log ingested from AO SSE stream (`session_id`, `event_type`, `raw_payload`, `normalized_payload`).
3. `pull_requests` — SCM pull request facts linked to sessions (`pr_number`, `repo`, `title`, `state`, `risk_level`).
4. `attention_items` — Ranked urgency queue items (`session_id`, `urgency_score`, `reason`, `idle_seconds`, `resolved`).
5. `policy_rules` — Configured policy engine rules (`name`, `condition_type`, `pattern`, `action`, `enabled`).
6. `approval_decisions` — Audit log of rule evaluation outcomes (`session_id`, `pr_id`, `rule_id`, `decision`, `reason`).
7. `digest_entries` — Daily risk-scored PR briefing cache (`pr_id`, `risk_score`, `risk_factors`, `summary_text`).
8. `alembic_version` — Database schema migration tracking.

---

## API Endpoint Reference

### Attention Queue
* `GET /api/v1/attention/queue?limit=50` — Fetch current ranked urgency queue (unresolved items, ordered by urgency score descending).
* `POST /api/v1/attention/{item_id}/resolve` — Mark an attention item as resolved.

### Policy Gate
* `GET /api/v1/policy/rules` — List all configured policy rules.
* `POST /api/v1/policy/rules` — Create a new policy rule.
* `POST /api/v1/policy/evaluate` — Evaluate a command string, file path list, or PR labels against active rules.
* `GET /api/v1/policy/decisions?limit=50` — Retrieve the decision audit log (newest first).

### Merge Digest
* `GET /api/v1/digest/today` — Fetch today's merge digest (ready to merge, needs review, in progress, summary).
* `GET /api/v1/digest/pr/{pr_id}` — Retrieve detailed risk factor analysis for a specific PR.

### Health & Debug
* `GET /healthz` — Service health check (`{"status": "ok"}`).
* `GET /readyz` — Readiness check (`{"status": "ready"}`).
* `GET /debug/recent-events` — Inspect recent normalized event log.

---

## Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+ & npm
* PostgreSQL running locally on port 5432 (default user/pass: `postgres/postgres`, database: `attention_router`)

### 1. Clone & Set Up Backend

```bash
git clone https://github.com/mohitjeswani01/attention-router.git
cd attention-router/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or copy .env.example)
cp .env.example .env
```

### 2. Database Migration & Seed

Make sure PostgreSQL is running and the `attention_router` database exists:

```bash
# Create database (if not exists)
createdb -U postgres attention_router 2>/dev/null || true

# Run migrations
alembic upgrade head

# Seed fake sessions, policy rules, decisions, and PRs (Idempotent)
PYTHONPATH=. python3 scripts/seed_fake_sessions.py
PYTHONPATH=. python3 scripts/seed_merge_digest.py
```

### 3. Start Backend Server

```bash
cd backend
PYTHONPATH=. python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Backend API will be available at `http://localhost:8000`.

### 4. Start Frontend Application

In a new terminal:

```bash
cd attention-router/frontend

# Install dependencies (already pre-packaged, or npm install)
npm install

# Start Next.js development server
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## Verification & Testing

### 1. Backend In-Process Smoke Test
Run the consolidated backend smoke test suite which validates data clearing, session seeding, urgency recomputation, rule evaluation, and digest building:

```bash
cd backend
PYTHONPATH=. python3 scripts/full_smoke_test.py
```
*Expected Output*:
```
============================================================
FULL SMOKE TEST - Attention Router Backend
============================================================
[1/5] Clearing all seeded data...               OK
[2/5] Seeding sessions...                       OK
[3/5] Seeding PRs and events...                 OK
[4/5] Seeding policy rules and decisions...     OK
[5/5] Recomputing urgency...                    OK

MODULE TESTS:
  Attention Router: PASS
  Policy Gate: PASS
  Merge Digest: PASS
✓ ALL TESTS PASSED
```

### 2. Frontend Production Build Verification
Verify TypeScript type checking and Next.js page generation:

```bash
cd frontend
npx next build
```
*Expected Output*: `✓ Generating static pages (7/7)` with zero build or lint errors.

---

## Agent Orchestrator (AO) Integration

Attention Router is architected around AO's local loopback daemon architecture:

* **Loopback Daemon Endpoint**: Defaults to `http://127.0.0.1:3001` (configured via `AO_PORT` or `settings.ao_daemon_base_url`).
* **Real-time Event Stream (`/api/v1/events`)**: Attention Router's `daemon_poller.py` consumes AO's Change-Data-Capture (CDC) Server-Sent Events stream. When sessions transition states (`waiting_input`, `blocked`, `exited`), Attention Router immediately recalculates urgency scores without polling overhead.
* **State Normalization**: Translates AO's raw session facts and computed display statuses into normalized urgency categories (`idle_on_approval`, `ci_failed`, `review_requested`, `working`, `idle`).

---

## Ideal Hackathon Demo Walkthrough

1. **`00` Landing Page (`/`)**: Highlighting the thesis: *"AO tracks what agents do — Attention Router tracks what YOU need to pay attention to."*
2. **Click "View Live Queue" $\to$ `01` Attention Queue (`/queue`)**:
   * Inspect the ranked session list in the left sidebar.
   * Select `c3d4e5f6` (score: `400.0`, status: `Awaiting Approval`).
   * Review evidence citation blocks `[1]` `[2]` explaining the calculated idle time penalty.
   * Click **"Mark as Resolved"** to unblock the queue.
3. **Switch to `02` Policy Gate (`/policies`)**:
   * Review summary counters (`Auto Approved`, `Escalated`, `Total Decisions`).
   * Inspect configured Policy Rules on the left (`allow_ls`, `escalate_dockerfile`, `escalate_rm_rf`).
   * Trace the Audit Log on the right with cited rationale.
4. **Switch to `03` Merge Digest (`/digest`)**:
   * Read the plain-English executive headline summarizing merge status.
   * Examine the 3 columns (`Ready to Merge`, `Needs Review`, `In Progress`).
   * Click PR `#103` (`Refactor auth module`) to expand risk factor breakdown (sensitive path touchpoints & 10-day staleness penalty).

---

## Design Philosophy

* **Calm & Evidence-Dense**: Replaces generic cards with data-rich evidence blocks and small numbered citation tags.
* **Monochrome Canvas with Accent Focus**: Dark canvas (`#0a0a0b`) ensures low visual fatigue; bright pink-to-cyan gradients are strictly reserved for primary call-to-action buttons.
* **Typographic Contrast**: Clean sans-serif for UI labels, elegant serif *italic* pull-quote headlines for context, and monospace for IDs, commit hashes, and file paths.

---

## Roadmap & Verification Boundaries

* **Backend Implementation**: Fully implemented with 8 database tables, SQLAlchemy models, Alembic migrations, and REST APIs.
* **Frontend Implementation**: Fully implemented 3-tab Next.js 14 application with responsive layout and real-time backend API integration.
* **In-Process Verification**: Verified via `full_smoke_test.py` and `npx next build`.
* **Verification Boundaries (Pending Live Owner Testing)**: End-to-end live event streaming from a running Agent Orchestrator Electron desktop application and live GitHub OAuth token execution flow are pending final manual verification by the project owner.

---

## Hackathon Attribution

Built specifically for **The Orchestra — Agent Orchestrator Hackathon**.

* **Repository**: [github.com/mohitjeswani01/attention-router](https://github.com/mohitjeswani01/attention-router)
* **Upstream Project**: [Untrivial-ai/agent-orchestrator](https://github.com/Untrivial-ai/agent-orchestrator)

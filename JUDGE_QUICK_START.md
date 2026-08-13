# Attention Router — Judge Quick-Start Guide (60-Second Overview)

> **Hackathon**: The Orchestra — Agent Orchestrator Hackathon  
> **Repository**: [github.com/mohitjeswani01/attention-router](https://github.com/mohitjeswani01/attention-router)  
> **Upstream Integration**: [Untrivial-ai/agent-orchestrator](https://github.com/Untrivial-ai/agent-orchestrator)

---

## 1. The Core Insight

Agent Orchestrator (AO) excels at executing autonomous coding agents, managing isolated workspaces, and tracking session state. However, when managing fleets of 5–10+ concurrent agents, human attention becomes the primary bottleneck. 

**Attention Router is the decision and intelligence layer above AO.** It ingests raw AO event streams and transforms them into prioritized human actions.

```
Agent Orchestrator (Execution & State) ──► Attention Router (Decision & Urgency) ──► Human Action
```

---

## 2. The 3 Modules

1. **`01` Attention Queue (`/queue`)**: Ranks agent sessions into a single urgency queue (`idle_on_approval` > `ci_failed` > `review_requested` > `working` > `idle`) with mathematical score factor breakdowns `[1]` `[2]`.
2. **`02` Policy Gate (`/policies`)**: Rules engine that auto-approves safe read-only operations (`ls`, `cat`, `eslint`, `*.md`) while escalating high-risk changes (`rm -rf`, `Dockerfile`, `.env`, `sudo`).
3. **`03` Merge Digest (`/digest`)**: Quantifies PR risk scores ($0-100$) based on file path sensitivity, CI conclusions, and staleness, bucketing PRs into `Ready to Merge`, `Needs Review`, and `In Progress`.

---

## 3. Quick-Start (Run Locally in 2 Commands)

### Step 1: Start Backend (Port 8000)
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
PYTHONPATH=. python3 scripts/seed_fake_sessions.py
PYTHONPATH=. python3 scripts/seed_merge_digest.py
PYTHONPATH=. python3 -m uvicorn app.main:app --port 8000
```

### Step 2: Start Frontend (Port 3000)
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## 4. Key Verification Command

To verify backend logic, database tables, and decision engine in 5 seconds:
```bash
cd backend
PYTHONPATH=. python3 scripts/full_smoke_test.py
```
*Expected Output*: `✓ ALL TESTS PASSED` (`3/3` modules pass).

---

## 5. Judge Walkthrough Click Path

1. **`http://localhost:3000` (`/`)**: View landing page thesis & module cards. Click **"View Live Queue"**.
2. **`/queue`**: Click top session `c3d4e5f6` (Score `400.0` - Awaiting Approval). Examine citation blocks `[1]` `[2]`. Click **"Mark as Resolved"**.
3. **`/policies`**: View Auto Approved (`3`) vs Escalated (`2`) summary counters & immutable Audit Log.
4. **`/digest`**: Read executive summary headline. Click PR `#103` (`Refactor auth module`) to view risk factor breakdown (`auth/` touchpoints + 10-day staleness).

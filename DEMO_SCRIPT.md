# Attention Router — 2.5 Minute Hackathon Demo Script

> **Target Duration**: 2 minutes 30 seconds  
> **Presenter**: Solo Hackathon Presenter  
> **Core Narrative**: Agent Orchestrator manages agent execution. Attention Router decides where human attention goes.

---

## `0:00` — Problem Statement & High-Level Thesis

* **Screen**: Open browser at `http://localhost:3000` (`/` Landing Page).
* **Action**: Hover cursor over the hero headline *"The missing intelligence layer for autonomous agent fleets."*
* **What to Say**:
  > "When you scale autonomous coding agents with Agent Orchestrator, execution isn't your bottleneck anymore — **human attention is**.  
  > If you have 5 or 10 agents running concurrently, you quickly end up with notification noise. Which agent is stuck waiting for input? Which PR has failing CI? Which pull request is safe to merge right now?  
  > AO tracks all the raw state — but it doesn't prioritize your time. We built **Attention Router** to solve that."

---

## `0:20` — Agent Orchestrator Context & Gap Mapping

* **Screen**: Landing page preview cards (`01`, `02`, `03`).
* **Action**: Scroll down slightly to highlight the three module cards.
* **What to Say**:
  > "AO's own documentation highlights three explicit boundaries: it doesn't prioritize human attention, it doesn't auto-approve safe commands, and it doesn't risk-score PRs before merge.  
  > Attention Router maps 1-to-1 to those exact gaps across three unified modules on a single event pipeline."

---

## `0:40` — Module 01: Attention Queue

* **Screen**: Click **"View Live Queue"** or navigate to `http://localhost:3000/queue`.
* **Action**:
  1. Point to the left sidebar ranked session list.
  2. Click the top-ranked item `c3d4e5f6` (score: `400.0`, status: `Awaiting Approval`).
  3. Highlight the SVG urgency score ring and the evidence citation blocks `[1]` `[2]`.
  4. Click **"Mark as Resolved"**.
* **What to Say**:
  > "First, the **Attention Queue**. Instead of scanning terminal windows, Attention Router ingests AO's local event stream and calculates an urgency score for every session.  
  > Notice session `c3d4e5f6` is ranked at the very top with an urgency score of 400. Why? Because it's waiting on human approval for over 10 minutes. The evidence blocks `[1]` and `[2]` break down the exact mathematical score calculation.  
  > Lower down, active sessions get lower scores, and completed sessions are excluded automatically. As soon as I handle the issue and click **'Mark as Resolved'**, the queue re-ranks instantly."

---

## `1:10` — Module 02: Policy Gate

* **Screen**: Click tab **`02 Policy Gate`** (`/policies`).
* **Action**:
  1. Point to the top summary counters (`Auto Approved`, `Escalated`, `Total Decisions`).
  2. Hover over a safe rule (`allow_ls`) and a risky rule (`escalate_dockerfile`).
  3. Scroll through the Audit Log on the right.
* **What to Say**:
  > "Next, **Policy Gate**. Developers get approval fatigue if agents ask permission for every single command.  
  > Policy Gate is a deterministic rules engine. Safe read-only commands like `ls`, `cat`, or linting runs are automatically approved. But if an agent touches a `Dockerfile`, a `.env` file, or tries running `rm -rf`, Policy Gate escalates it for human sign-off.  
  > Every evaluation is recorded in this audit log with a full citation explaining why it was auto-approved or escalated."

---

## `1:40` — Module 03: Merge Readiness Digest

* **Screen**: Click tab **`03 Merge Digest`** (`/digest`).
* **Action**:
  1. Read the serif-italic summary headline at the top.
  2. Point across the three columns: `Ready to Merge`, `Needs Review`, `In Progress`.
  3. Click PR `#103` (`Refactor auth module`) to open the expanded risk factor drawer.
* **What to Say**:
  > "Finally, the **Merge Readiness Digest**. When multiple agents open pull requests, how do you know what to merge first?  
  > Attention Router evaluates PR diffs, CI test conclusions, and session age to compute a risk score from 0 to 100.  
  > Look at PR `#101` — doc update, passing CI — it's in **Ready to Merge**.  
  > But PR `#103` has a high risk score of 85. When I click it, Attention Router shows me exactly why: it touches sensitive auth handlers, modifies `settings.yaml`, and has been stale for 10 days.  
  > In 5 seconds, an engineering manager knows exactly which PR needs their eyes."

---

## `2:10` — Synthesis & Technical Architecture

* **Screen**: Return to header logo or tab navigation.
* **Action**: Hover over the green `live` indicator dot in the top right header.
* **What to Say**:
  > "Under the hood, Attention Router runs on FastAPI and PostgreSQL, subscribing directly to Agent Orchestrator's local loopback daemon and Change-Data-Capture stream.  
  > The frontend is built in Next.js 14 with a high-contrast, evidence-first visual style — no noise, just actionable decisions."

---

## `2:25` — Closing Line

* **Action**: Pause on the Attention Queue view (`/queue`).
* **What to Say**:
  > **"Agent Orchestrator orchestrates agents. Attention Router orchestrates human attention."**  
  > "Thank you!"

---

## Presenter Checklist & Demo Tips

- [ ] **Database Pre-seeded**: Run `PYTHONPATH=. python3 scripts/seed_fake_sessions.py && PYTHONPATH=. python3 scripts/seed_merge_digest.py` before starting the demo.
- [ ] **Servers Running**: Confirm backend is running on `http://localhost:8000` and frontend on `http://localhost:3000`.
- [ ] **Browser Resolution**: Set browser window to 1080p (1920x1080) for optimal visual layout.
- [ ] **Pacing**: Speak at a steady, confident pace. Do not rush through the citation blocks or risk factor breakdown.

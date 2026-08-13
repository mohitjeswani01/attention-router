# Agent Orchestrator Gap Mapping

This document details the exact alignment between Agent Orchestrator's documented boundaries and Attention Router's decision layer.

## Upstream Project
- **Repository**: [Untrivial-ai/agent-orchestrator](https://github.com/Untrivial-ai/agent-orchestrator)
- **Local Loopback Endpoint**: `http://127.0.0.1:3001`
- **Primary Event Channel**: `/api/v1/events` (CDC / SSE Stream)

## Direct Feature & Gap Mapping

| AO Feature / Scope Boundary | Attention Router Module | Implementation Details |
|---|---|---|
| **Session Lifecycle & Workspace Orchestration**: AO spawns agent containers, manages workspace isolation, and tracks session activity states (`active`, `idle`, `waiting_input`, `blocked`, `exited`). | **`01` Attention Queue** (`/queue`) | Consumes raw `activity_state` and event logs. Computes a live urgency score using base weights + idle penalties to surface blocked agents first. |
| **Command Execution & Activity Hooks**: AO exposes hooks for agent shell tool calls and command invocations. | **`02` Policy Gate** (`/policies`) | Intercepts tool calls and evaluates command patterns (regex/glob) and file paths to auto-approve safe read/format calls while escalating destructive or secret edits. |
| **SCM & PR State Tracking**: AO tracks PR creation, commit updates, and check run statuses across sessions. | **`03` Merge Readiness Digest** (`/digest`) | Evaluates PR file path sensitivity, CI check conclusions, and session age to generate composite risk scores ($0-100$) and plain-English executive merge briefings. |

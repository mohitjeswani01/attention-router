# Agent Orchestrator Daemon Integration Notes

## Local Clone Status
**FOUND** at `/home/jeswa/ao-source` (WSL path: `\\wsl.localhost\Ubuntu\home\jeswa\ao-source`)

## Daemon Base URL/Port
- **Default**: `http://127.0.0.1:3001`
- **Configurable via**: `AO_PORT` env var (default 3001)
- **Handshake file**: `~/.ao/running.json` (configurable via `AO_RUN_FILE`)
- **Binds only to loopback** (`127.0.0.1`) — no network exposure

## HTTP Routes (from `docs/cli/README.md`)

### Health & Control
| Route | Method | Purpose | Notes |
|-------|--------|---------|-------|
| `/healthz` | GET | Health check | Used by `ao start` to wait for daemon ready |
| `/readyz` | GET | Readiness check | |
| `/shutdown` | POST | Graceful shutdown | Called by `ao stop` |

### Sessions
| Route | Method | Purpose | CLI Command |
|-------|--------|---------|-------------|
| `/api/v1/sessions` | GET | List all sessions | `ao session ls` |
| `/api/v1/sessions` | POST | Spawn new session | `ao spawn` |
| `/api/v1/sessions/{id}` | GET | Get session details | `ao session get <id>` |
| `/api/v1/sessions/{id}` | PATCH | Rename session | `ao session rename <id> <name>` |
| `/api/v1/sessions/{id}/kill` | POST | Kill session | `ao session kill <id>` |
| `/api/v1/sessions/{id}/restore` | POST | Restore session | `ao session restore <id>` |
| `/api/v1/sessions/{id}/switch-agent` | POST | Switch agent/harness | `ao session switch-agent <id> <target>` |
| `/api/v1/sessions/{id}/agent-switches` | GET | List agent switches | `ao session agent-switch ls <id>` |
| `/api/v1/sessions/{id}/agent-switches/{switchId}/handoff` | POST | Submit handoff | `ao session handoff submit` |
| `/api/v1/sessions/cleanup` | POST | Cleanup terminated sessions | `ao session cleanup` |
| `/api/v1/sessions/{id}/pr/claim` | POST | Claim PR for session | `ao session claim-pr <id> <pr-ref>` |
| `/api/v1/sessions/{id}/send` | POST | Send input to session | `ao send` |
| `/api/v1/sessions/{id}/preview` | POST | Preview session output | `ao preview [url]` |
| `/api/v1/sessions/{id}/preview/server` | POST/GET/DELETE | Preview server control | `ao preview start/status/stop` |
| `/api/v1/sessions/{id}/activity` | POST | Activity hook (hidden) | `ao hooks <agent> <event>` |

### Projects
| Route | Method | Purpose | CLI Command |
|-------|--------|---------|-------------|
| `/api/v1/projects` | GET | List projects | `ao project ls` |
| `/api/v1/projects` | POST | Add project | `ao project add` |
| `/api/v1/projects/{id}` | GET | Get project | `ao project get <id>` |
| `/api/v1/projects/{id}/config` | PUT | Set project config | `ao project set-config <id>` |
| `/api/v1/projects/{id}` | DELETE | Remove project | `ao project rm <id>` |

### Agents
| Route | Method | Purpose | CLI Command |
|-------|--------|---------|-------------|
| `/api/v1/agents` | GET | List agent catalog | `ao agent ls` |
| `/api/v1/agents/refresh` | POST | Refresh agent catalog | `ao agent ls --refresh` |

### Orchestrators
| Route | Method | Purpose | CLI Command |
|-------|--------|---------|-------------|
| `/api/v1/orchestrators` | GET | List orchestrators | `ao orchestrator ls` |

### Browser
| Route | Method | Purpose | CLI Command |
|-------|--------|---------|-------------|
| `/api/v1/browser/status` | GET | Browser status | `ao browser status` |
| `/api/v1/browser/commands` | POST | Browser commands | `ao browser <cmd>` |

### Events (SSE)
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/v1/events` | GET | Server-Sent Events stream (CDC broadcaster) |

### PR & Review Routes (mentioned but not fully documented in CLI table)
- `ao pr merge` → likely `POST /api/v1/sessions/{id}/pr/merge` or similar
- `ao pr resolve-comments` → likely `POST /api/v1/sessions/{id}/pr/resolve-comments`
- `ao review ls` → likely `GET /api/v1/sessions/{id}/reviews`
- `ao review trigger/execute/restart` → likely `POST /api/v1/sessions/{id}/reviews/{reviewId}/trigger`
- `ao review cancel/stop` → likely `POST /api/v1/sessions/{id}/reviews/{reviewId}/cancel`
- `ao review submit` → likely `POST /api/v1/sessions/{id}/reviews/{reviewId}/submit`

## Response Shapes (from architecture.md)

### Session (core durable facts)
```json
{
  "id": "string",
  "project_id": "string",
  "harness": "string",
  "session_mode": "tui|chat",
  "runtime_handle_id": "string|null",
  "provider_conversation_id": "string|null",
  "controller_generation": "string",
  "activity_state": "active|idle|waiting_input|blocked|exited",
  "is_terminated": "boolean",
  "metadata": "object"
}
```

### Display Status (computed at read time, NOT stored)
Precedence: `merged` → `terminated` → `needs_input` → PR pipeline (`ci_failed`, `draft`, `changes_requested`, `merge_conflict`, `mergeable`, `approved`, `review_pending`, `pr_open`) → `working` → `no_signal` → `idle`

### PR Facts
```json
{
  "id": "string",
  "session_id": "string",
  "number": "integer",
  "state": "string",
  "title": "string",
  "draft": "boolean",
  "mergeable": "boolean"
}
```

### PR Checks
```json
{
  "id": "string",
  "pr_id": "string",
  "name": "string",
  "status": "string",
  "conclusion": "string"
}
```

### CDC Event (from change_log)
```json
{
  "seq": "bigint",
  "table_name": "string",
  "row_id": "string",
  "operation": "INSERT|UPDATE|DELETE",
  "old_data": "jsonb|null",
  "new_data": "jsonb|null"
}
```

## Key Architectural Notes for Integration
1. **Display status is computed, not stored** — our Attention Router must call the daemon's session endpoints and derive urgency from `activity_state`, `is_terminated`, and PR facts
2. **CDC/SSE is the event pipeline** — subscribe to `/api/v1/events` for real-time updates
3. **`activity_state = blocked`** means agent is waiting on permission/approval — **automation must never inject input**
4. **`activity_state = waiting_input`** means agent at empty prompt awaiting instruction
5. **PR pipeline states** (from SCM Observer): `ci_failed`, `ci_pending`, `changes_requested`, `merge_conflict`, `mergeable`, `approved`, `review_pending`, `pr_open`, `draft`
6. **Session modes**: `tui` (terminal) or `chat` (runtime-less) — affects how feedback is routed
7. **Daemon is the single source of truth** — CLI is thin, all logic in daemon
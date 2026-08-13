# Attention Router — System Architecture

## Overview

Attention Router is built as an asynchronous decision pipeline sitting on top of Agent Orchestrator (AO).

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
└───────────┬───────────┴─────────────┬─────────────┴───────────┬───────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      ▼
                      ┌──────────────────────────────────────┐
                      │   Next.js 14 Dark Canvas Frontend    │
                      └──────────────────────────────────────┘
```

## Data Pipeline & Ingestion

1. **Daemon Ingestion**: `daemon_poller.py` connects to AO loopback at `http://127.0.0.1:3001` and subscribes to `/api/v1/events`.
2. **Event Normalization**: `event_normalizer.py` converts raw CDC payloads into normalized domain events (`pr.updated`, `pr_check.updated`, `session.activity_changed`).
3. **Async Event Bus**: `event_bus.py` broadcasts events to background scoring subscribers.
4. **Queue Scoring Service**: `queue_service.py` recomputes urgency scores and upserts `AttentionItem` records.
5. **Policy Engine**: `rules_engine.py` evaluates active `PolicyRule` records against commands and file paths.
6. **Digest Builder**: `digest_builder.py` & `risk_scoring.py` evaluate PR diffs and CI statuses to generate daily digests.

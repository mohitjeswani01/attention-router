"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchQueue, resolveItem } from "@/lib/api";
import type { AttentionItem } from "@/lib/api";
import AttentionQueueItem from "@/components/AttentionQueueItem";
import { getReasonStyle } from "@/components/AttentionQueueItem";
import IdleTimeCounter from "@/components/IdleTimeCounter";

// ── Scoring explanation helper ──────────────────────────────────────────

function explainScore(item: AttentionItem): string[] {
  const explanations: string[] = [];
  switch (item.reason) {
    case "idle_on_approval":
      explanations.push(
        `Session has been waiting for human approval for ${humanizeDetail(item.idle_seconds)}.`
      );
      explanations.push(
        `Base score of 100 + ${(item.idle_seconds * 0.5).toFixed(0)} points from idle time (0.5 pts/sec).`
      );
      explanations.push(
        "This is the highest-priority category — the agent is blocked and cannot proceed."
      );
      break;
    case "ci_failed":
      explanations.push("A recent CI/PR check returned a failure or error status.");
      explanations.push("Base score of 80 — needs human investigation to unblock.");
      break;
    case "review_requested":
      explanations.push("A pull request review has been requested or changes were requested.");
      explanations.push("Base score of 60 — review feedback is pending.");
      break;
    case "working":
      explanations.push("The agent is actively working. Low urgency.");
      explanations.push("Base score of 10 — included for visibility only.");
      break;
    case "idle":
      explanations.push(
        `Session has been idle for ${humanizeDetail(item.idle_seconds)} without a specific blocker.`
      );
      explanations.push("Base score of 5 — lowest priority, no action required.");
      break;
    default:
      explanations.push("No specific urgency classification.");
  }
  return explanations;
}

function humanizeDetail(seconds: number): string {
  if (seconds < 60) return `${seconds} seconds`;
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m} minute${m !== 1 ? "s" : ""}`;
  const h = Math.floor(m / 60);
  const rm = m % 60;
  return `${h}h ${rm}m`;
}

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
}

// ── Skeleton components ────────────────────────────────────────────────

function SidebarSkeleton() {
  return (
    <div className="space-y-0">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="px-4 py-3 border-b border-white/[0.04]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="skeleton w-5 h-3" />
              <div className="skeleton w-16 h-4" />
            </div>
            <div className="skeleton w-8 h-3" />
          </div>
          <div className="mt-1.5">
            <div className="skeleton w-24 h-5 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="p-6 space-y-6">
      <div className="skeleton w-32 h-8" />
      <div className="skeleton w-full h-4" />
      <div className="skeleton w-3/4 h-4" />
      <div className="space-y-3 mt-8">
        <div className="skeleton w-full h-20 rounded-lg" />
        <div className="skeleton w-full h-20 rounded-lg" />
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────

export default function QueuePage() {
  const [queue, setQueue] = useState<AttentionItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolving, setResolving] = useState(false);

  const load = useCallback(async () => {
    try {
      const items = await fetchQueue();
      setQueue(items);
      setError(null);
      // Auto-select first if nothing selected
      if (items.length > 0 && !selectedId) {
        setSelectedId(items[0].id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    load();
    // Poll every 5 seconds
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  const selected = queue.find((item) => item.id === selectedId) || null;

  const handleResolve = async () => {
    if (!selected) return;
    setResolving(true);
    try {
      await resolveItem(selected.id);
      setSelectedId(null);
      await load();
    } catch {
      // Silently fail — will refresh
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="flex-1 flex min-h-0">
      {/* ── Left Sidebar: Ranked Queue List ─────────────────── */}
      <aside className="w-72 shrink-0 border-r border-white/[0.06] bg-[#0c0c0d] flex flex-col">
        <div className="px-4 py-3 border-b border-white/[0.06]">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium text-white/40 uppercase tracking-widest">
              Queue
            </h2>
            <span className="font-mono text-[11px] text-white/20 tabular-nums">
              {queue.length} items
            </span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <SidebarSkeleton />
          ) : error ? (
            <div className="p-4">
              <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                <p className="text-[11px] font-mono text-red-400/80">
                  {error}
                </p>
                <button
                  onClick={load}
                  className="mt-2 text-[11px] text-red-400 hover:text-red-300 underline"
                >
                  retry
                </button>
              </div>
            </div>
          ) : queue.length === 0 ? (
            <div className="p-6 text-center">
              <div className="w-8 h-8 mx-auto mb-3 rounded-full bg-emerald-500/10 flex items-center justify-center">
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
              </div>
              <p className="text-sm text-white/40">Queue is clear</p>
              <p className="text-[11px] text-white/20 mt-1 font-serif italic">
                All agents are operating normally
              </p>
            </div>
          ) : (
            queue.map((item, i) => (
              <AttentionQueueItem
                key={item.id}
                item={item}
                index={i}
                isSelected={item.id === selectedId}
                onClick={() => setSelectedId(item.id)}
              />
            ))
          )}
        </div>
      </aside>

      {/* ── Main Panel: Selected Item Detail ─────────────────── */}
      <section className="flex-1 min-w-0 flex flex-col bg-[#0a0a0b]">
        {loading ? (
          <DetailSkeleton />
        ) : !selected ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-white/20 text-sm">
                {queue.length > 0
                  ? "Select an item from the queue"
                  : "No items require attention"}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 max-w-3xl animate-fade-in-up">
              {/* Urgency Score */}
              <div className="flex items-start gap-5 mb-8">
                {/* Score circle */}
                <div className="relative w-20 h-20 shrink-0">
                  <svg
                    viewBox="0 0 80 80"
                    className="w-20 h-20 -rotate-90"
                  >
                    <circle
                      cx="40"
                      cy="40"
                      r="34"
                      fill="none"
                      stroke="rgba(255,255,255,0.06)"
                      strokeWidth="4"
                    />
                    <circle
                      cx="40"
                      cy="40"
                      r="34"
                      fill="none"
                      stroke="url(#urgency-gradient)"
                      strokeWidth="4"
                      strokeLinecap="round"
                      strokeDasharray={`${(Math.min(selected.urgency_score, 1000) / 1000) * 213.6} 213.6`}
                    />
                    <defs>
                      <linearGradient id="urgency-gradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#ec4899" />
                        <stop offset="100%" stopColor="#06b6d4" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="font-mono text-lg font-semibold text-white tabular-nums">
                      {selected.urgency_score.toFixed(0)}
                    </span>
                  </div>
                </div>

                <div className="min-w-0 pt-1">
                  <div className="flex items-center gap-3">
                    {(() => {
                      const style = getReasonStyle(selected.reason);
                      return (
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ring-1 ring-inset ${style.bg}`}>
                          <span className={`w-2 h-2 rounded-full ${style.dot}`} />
                          {style.label}
                        </span>
                      );
                    })()}
                    {selected.idle_seconds > 0 && (
                      <span className="text-white/30 text-xs">
                        idle for{" "}
                        <IdleTimeCounter
                          idleSeconds={selected.idle_seconds}
                          className="text-white/50"
                        />
                      </span>
                    )}
                  </div>
                  <h1 className="mt-2 font-serif italic text-xl text-white/70">
                    Session requires attention
                  </h1>
                  <p className="font-mono text-[13px] text-white/30 mt-1">
                    {selected.session_id}
                  </p>
                </div>
              </div>

              {/* Why this is ranked here — evidence blocks */}
              <div className="space-y-3 animate-fade-in-up-delay-1">
                <h3 className="text-[11px] uppercase tracking-widest text-white/30 font-medium">
                  Why this is ranked here
                </h3>

                <div className="space-y-2">
                  {explainScore(selected).map((explanation, i) => (
                    <div
                      key={i}
                      className="flex gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]"
                    >
                      <span className="citation-tag shrink-0">{i + 1}</span>
                      <p className="text-sm text-white/60 leading-relaxed">
                        {explanation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Resolve action */}
              <div className="mt-8 animate-fade-in-up-delay-2">
                <button
                  onClick={handleResolve}
                  disabled={resolving}
                  className="btn-gradient disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {resolving ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" opacity="0.3" />
                        <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                      </svg>
                      Resolving…
                    </span>
                  ) : (
                    "Mark as Resolved"
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* ── Right Rail: Session Metadata ──────────────────────── */}
      <aside className="w-64 shrink-0 border-l border-white/[0.06] bg-[#0c0c0d] overflow-y-auto">
        <div className="px-4 py-3 border-b border-white/[0.06]">
          <h2 className="text-xs font-medium text-white/40 uppercase tracking-widest">
            Metadata
          </h2>
        </div>

        {selected ? (
          <div className="p-4 space-y-4 animate-fade-in-up">
            <MetadataField label="Item ID" value={selected.id} mono />
            <MetadataField label="Session ID" value={selected.session_id} mono />
            <MetadataField
              label="Urgency Score"
              value={selected.urgency_score.toFixed(1)}
              mono
            />
            <MetadataField label="Reason" value={selected.reason} mono />
            <MetadataField
              label="Idle Time"
              value={`${selected.idle_seconds}s`}
              mono
            />
            <MetadataField
              label="Created At"
              value={formatTimestamp(selected.created_at)}
            />
            <MetadataField
              label="Resolved"
              value={selected.resolved ? "Yes" : "No"}
            />
            {selected.resolved_at && (
              <MetadataField
                label="Resolved At"
                value={formatTimestamp(selected.resolved_at)}
              />
            )}
          </div>
        ) : (
          <div className="p-4">
            <p className="text-[11px] text-white/20">
              Select a queue item to view metadata
            </p>
          </div>
        )}
      </aside>
    </div>
  );
}

// ── Metadata field component ───────────────────────────────────────────

function MetadataField({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-widest text-white/25 mb-0.5">
        {label}
      </dt>
      <dd
        className={`text-[13px] text-white/60 break-all ${
          mono ? "font-mono" : ""
        }`}
      >
        {value}
      </dd>
    </div>
  );
}

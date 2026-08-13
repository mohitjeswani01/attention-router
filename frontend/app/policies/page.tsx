"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchPolicyRules, fetchDecisions } from "@/lib/api";
import type { PolicyRule, ApprovalDecision } from "@/lib/api";
import PolicyRuleCard from "@/components/PolicyRuleCard";

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

function SkeletonRule() {
  return (
    <div className="px-4 py-3 border-b border-white/[0.04]">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-baseline gap-2.5 min-w-0">
          <div className="skeleton w-5 h-3" />
          <div className="min-w-0">
            <div className="skeleton w-24 h-4" />
            <div className="skeleton w-32 h-3 mt-0.5" />
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div className="skeleton w-20 h-5 rounded-full" />
          <div className="skeleton w-2 h-2 rounded-full" />
        </div>
      </div>
    </div>
  );
}

function SkeletonDecision() {
  return (
    <div className="flex gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
      <div className="citation-tag shrink-0" style={{ background: "rgba(255,255,255,0.06)" }} />
      <div className="flex-1 space-y-1">
        <div className="skeleton w-3/4 h-4" />
        <div className="skeleton w-1/2 h-3" />
      </div>
    </div>
  );
}

export default function PoliciesPage() {
  const [rules, setRules] = useState<PolicyRule[]>([]);
  const [decisions, setDecisions] = useState<ApprovalDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [rulesData, decisionsData] = await Promise.all([
        fetchPolicyRules(),
        fetchDecisions(100),
      ]);
      setRules(rulesData);
      setDecisions(decisionsData);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [load]);

  // Compute summary stats
  const autoApproveCount = decisions.filter((d) => d.decision === "auto_approve").length;
  const escalateCount = decisions.filter((d) => d.decision === "escalate").length;

  return (
    <div className="flex-1 flex flex-col min-h-0 p-6 max-w-[1600px] mx-auto w-full">
      {/* ── Header with summary stats ───────────────────────────── */}
      <div className="mb-6 animate-fade-in-up">
        <div className="flex items-baseline justify-between gap-4 flex-wrap">
          <div>
            <h1 className="font-serif italic text-2xl text-white/70">Policy Gate</h1>
            <p className="text-sm text-white/30 mt-1 font-serif italic">
              Rules engine and audit log for automated approval decisions
            </p>
          </div>
          <div className="flex items-center gap-6 shrink-0">
            <div className="text-center">
              <div className="font-mono text-2xl font-semibold text-emerald-400 tabular-nums">
                {autoApproveCount}
              </div>
              <div className="text-[11px] text-white/30 uppercase tracking-wide">Auto Approved</div>
            </div>
            <div className="w-px h-8 bg-white/[0.08]" />
            <div className="text-center">
              <div className="font-mono text-2xl font-semibold text-amber-400 tabular-nums">
                {escalateCount}
              </div>
              <div className="text-[11px] text-white/30 uppercase tracking-wide">Escalated</div>
            </div>
            <div className="w-px h-8 bg-white/[0.08]" />
            <div className="text-center">
              <div className="font-mono text-2xl font-semibold text-white/60 tabular-nums">
                {decisions.length}
              </div>
              <div className="text-[11px] text-white/30 uppercase tracking-wide">Total Decisions</div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Main Content Grid ───────────────────────────────────── */}
      <div className="flex gap-6 min-h-0">
        {/* Left: Policy Rules */}
        <aside className="w-80 shrink-0 flex flex-col bg-[#0c0c0d] border border-white/[0.06] rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-white/[0.06]">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-medium text-white/40 uppercase tracking-widest">
                Policy Rules
              </h2>
              <span className="font-mono text-[11px] text-white/20 tabular-nums">
                {rules.length}
              </span>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => <SkeletonRule key={i} />)
            ) : error ? (
              <div className="p-4">
                <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                  <p className="text-[11px] font-mono text-red-400/80">{error}</p>
                  <button onClick={load} className="mt-2 text-[11px] text-red-400 hover:text-red-300 underline">
                    retry
                  </button>
                </div>
              </div>
            ) : rules.length === 0 ? (
              <div className="p-6 text-center">
                <div className="w-8 h-8 mx-auto mb-3 rounded-full bg-amber-500/10 flex items-center justify-center">
                  <span className="font-mono text-sm text-amber-400">⚙</span>
                </div>
                <p className="text-sm text-white/40">No policy rules configured</p>
                <p className="text-[11px] text-white/20 mt-1 font-serif italic">
                  Add rules via the backend API
                </p>
              </div>
            ) : (
              rules.map((rule, i) => <PolicyRuleCard key={rule.id} rule={rule} index={i} />)
            )}
          </div>
        </aside>

        {/* Right: Audit Log */}
        <section className="flex-1 min-w-0 flex flex-col bg-[#0c0c0d] border border-white/[0.06] rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-white/[0.06]">
            <h2 className="text-xs font-medium text-white/40 uppercase tracking-widest">
              Audit Log — Newest First
            </h2>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => <SkeletonDecision key={i} />)
            ) : error ? (
              <div className="p-4">
                <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                  <p className="text-[11px] font-mono text-red-400/80">{error}</p>
                  <button onClick={load} className="mt-2 text-[11px] text-red-400 hover:text-red-300 underline">
                    retry
                  </button>
                </div>
              </div>
            ) : decisions.length === 0 ? (
              <div className="p-6 text-center">
                <div className="w-8 h-8 mx-auto mb-3 rounded-full bg-neutral-500/10 flex items-center justify-center">
                  <span className="font-mono text-sm text-neutral-400">📋</span>
                </div>
                <p className="text-sm text-white/40">No decisions recorded yet</p>
                <p className="text-[11px] text-white/20 mt-1 font-serif italic">
                  Decisions will appear here as rules are evaluated
                </p>
              </div>
            ) : (
              decisions.map((decision, i) => (
                <div
                  key={decision.id}
                  className="flex gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04] transition-colors animate-fade-in-up"
                  style={{ animationDelay: `${i * 15}ms` }}
                >
                  <span className="citation-tag shrink-0">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm text-white/70 leading-relaxed">
                        {decision.reason || <span className="text-white/20 font-serif italic">No reason provided</span>}
                      </p>
                      <span
                        className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ring-1 ring-inset ${
                          decision.decision === "auto_approve"
                            ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20"
                            : "bg-amber-500/10 text-amber-400 ring-amber-500/20"
                        }`}
                      >
                        {decision.decision}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1.5 text-[11px] text-white/30">
                      {decision.rule_id && (
                        <span className="flex items-center gap-1">
                          <span className="font-mono text-white/20">rule:</span>
                          <span className="font-mono text-white/40">{decision.rule_id.slice(0, 8)}…</span>
                        </span>
                      )}
                      {decision.session_id && (
                        <span className="flex items-center gap-1">
                          <span className="font-mono text-white/20">session:</span>
                          <span className="font-mono text-white/40">{decision.session_id.slice(0, 12)}…</span>
                        </span>
                      )}
                      {decision.pr_id && (
                        <span className="flex items-center gap-1">
                          <span className="font-mono text-white/20">pr:</span>
                          <span className="font-mono text-white/40">#{decision.pr_id}</span>
                        </span>
                      )}
                      <time className="font-mono" dateTime={decision.decided_at}>
                        {formatTimestamp(decision.decided_at)}
                      </time>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
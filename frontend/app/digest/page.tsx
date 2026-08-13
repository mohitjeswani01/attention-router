"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchDigest, fetchPRDetail } from "@/lib/api";
import type { DigestResponse, DigestPR, PRRiskDetail } from "@/lib/api";
import DigestCard from "@/components/DigestCard";

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

function SkeletonDigestCard() {
  return (
    <button className="w-full text-left px-4 py-3 border border-white/[0.06] rounded-lg bg-white/[0.02]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2">
            <div className="skeleton w-10 h-4 shrink-0" />
            <div className="skeleton w-32 h-4 truncate" />
          </div>
          <div className="skeleton w-24 h-3 mt-1" />
        </div>
        <div className="skeleton w-28 h-6 rounded-full shrink-0" />
      </div>
      <div className="flex flex-wrap gap-1.5 mt-2">
        <div className="skeleton w-20 h-5 rounded-full" />
        <div className="skeleton w-20 h-5 rounded-full" />
      </div>
    </button>
  );
}

function SkeletonSummary() {
  return (
    <div className="space-y-3">
      <div className="skeleton w-3/4 h-10" />
      <div className="skeleton w-1/2 h-10" />
    </div>
  );
}

export default function DigestPage() {
  const [digest, setDigest] = useState<DigestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPR, setExpandedPR] = useState<string | null>(null);
  const [detail, setDetail] = useState<PRRiskDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchDigest();
      setDigest(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 60000);
    return () => clearInterval(interval);
  }, [load]);

  const handlePRClick = async (prId: string) => {
    if (expandedPR === prId) {
      setExpandedPR(null);
      setDetail(null);
      return;
    }
    setDetailLoading(true);
    setExpandedPR(prId);
    try {
      const data = await fetchPRDetail(prId);
      setDetail(data);
    } catch {
      // Keep expanded but show error in detail
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex min-h-0 p-6 max-w-[1600px] mx-auto w-full">
        <div className="w-full space-y-8 animate-fade-in-up">
          <SkeletonSummary />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-3">
                <div className="skeleton w-20 h-5" />
                {Array.from({ length: 3 }).map((_, j) => (
                  <SkeletonDigestCard key={j} />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex min-h-0 p-6 max-w-[1600px] mx-auto w-full">
        <div className="w-full max-w-2xl mx-auto text-center animate-fade-in-up">
          <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-6">
            <p className="text-[11px] font-mono text-red-400/80">{error}</p>
            <button onClick={load} className="mt-4 text-sm text-red-400 hover:text-red-300 underline">
              retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!digest) {
    return null;
  }

  const sections = [
    { key: "ready_to_merge", label: "Ready to Merge", icon: "✓", color: "text-emerald-400", bg: "bg-emerald-500/10" },
    { key: "needs_review", label: "Needs Review", icon: "⚠", color: "text-amber-400", bg: "bg-amber-500/10" },
    { key: "in_progress", label: "In Progress", icon: "⟳", color: "text-cyan-400", bg: "bg-cyan-500/10" },
  ] as const;

  return (
    <div className="flex-1 flex min-h-0 p-6 max-w-[1600px] mx-auto w-full">
      <div className="w-full space-y-8 animate-fade-in-up">
        {/* ── Summary Headline ───────────────────────────────────── */}
        <header className="animate-fade-in-up">
          <div className="flex items-center gap-3 mb-4">
            <span className="font-mono text-sm text-white/20">03</span>
            <h1 className="font-serif italic text-3xl md:text-4xl text-white/70 leading-tight">
              Merge Digest
            </h1>
          </div>
          <div className="prose prose-invert max-w-none text-white/60 text-lg md:text-xl leading-relaxed font-serif italic">
            {digest.summary || <span className="text-white/20">No summary available</span>}
          </div>
          <div className="mt-4 flex items-center gap-4 text-[11px] text-white/30">
            <time className="font-mono" dateTime={new Date().toISOString()}>
              Generated {new Date().toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
            </time>
            <span className="w-px h-4 bg-white/[0.08]" />
            <span className="font-mono">
              {digest.ready_to_merge.length + digest.needs_review.length + digest.in_progress.length} PRs tracked
            </span>
          </div>
        </header>

        {/* ── Three Buckets ──────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {sections.map((section) => {
            const prs = digest[section.key as keyof DigestResponse] as DigestPR[];
            return (
              <section
                key={section.key}
                className="flex flex-col bg-[#0c0c0d] border border-white/[0.06] rounded-xl overflow-hidden"
              >
                {/* Section Header */}
                <div className="px-4 py-3 border-b border-white/[0.06] bg-white/[0.02]">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center justify-center w-6 h-6 rounded text-[11px] font-mono ${section.bg} ${section.color}`}
                    >
                      {section.icon}
                    </span>
                    <h2 className="text-sm font-medium text-white/80">{section.label}</h2>
                    <span className="ml-auto font-mono text-[11px] text-white/30 tabular-nums">
                      {prs.length}
                    </span>
                  </div>
                </div>

                {/* PR List */}
                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                  {prs.length === 0 ? (
                    <div className="p-6 text-center">
                      <p className="text-sm text-white/30 font-serif italic">
                        {section.key === "ready_to_merge" && "All clear — nothing ready yet"}
                        {section.key === "needs_review" && "No PRs awaiting review"}
                        {section.key === "in_progress" && "No active work in progress"}
                      </p>
                    </div>
                  ) : (
                    prs.map((pr) => (
                      <DigestCard
                        key={pr.pr_id}
                        pr={pr}
                        onClick={() => handlePRClick(pr.pr_id)}
                      />
                    ))
                  )}

                  {/* Inline expanded detail */}
                  {prs.map((pr) =>
                    expandedPR === pr.pr_id ? (
                      <div
                        key={`detail-${pr.pr_id}`}
                        className="animate-fade-in-up mt-2 p-4 rounded-lg bg-white/[0.02] border border-white/[0.08]"
                      >
                        {detailLoading ? (
                          <div className="space-y-3">
                            <div className="skeleton w-1/3 h-4" />
                            <div className="skeleton w-full h-4" />
                            <div className="skeleton w-full h-4" />
                          </div>
                        ) : detail && detail.pr_id === pr.pr_id ? (
                          <div className="space-y-4">
                            <div className="flex items-start justify-between gap-4">
                              <div className="min-w-0">
                                <div className="flex items-baseline gap-2 mb-1">
                                  <span className="font-mono text-[13px] text-white/50 shrink-0">
                                    #{detail.pr_number}
                                  </span>
                                  <span className="text-sm text-white/80 truncate">{detail.title}</span>
                                </div>
                                <p className="font-mono text-[11px] text-white/25">{detail.repo}</p>
                              </div>
                              <RiskBadge score={detail.risk_score} />
                            </div>

                            <div className="text-white/60 text-sm leading-relaxed font-serif italic border-t border-white/[0.06] pt-4">
                              {detail.summary}
                            </div>

                            {detail.risk_factors.length > 0 && (
                              <div className="flex flex-wrap gap-1.5">
                                {detail.risk_factors.map((factor) => (
                                  <span
                                    key={factor}
                                    className="px-2 py-0.5 rounded text-[10px] font-mono bg-white/[0.04] text-white/30 ring-1 ring-inset ring-white/[0.06]"
                                  >
                                    {factor}
                                  </span>
                                ))}
                              </div>
                            )}

                            <div className="flex items-center gap-3 text-[11px] text-white/25 pt-2 border-t border-white/[0.04]">
                              <span className="font-mono">Generated:</span>
                              <time className="font-mono" dateTime={detail.generated_at}>
                                {formatTimestamp(detail.generated_at)}
                              </time>
                            </div>
                          </div>
                        ) : (
                          <p className="text-sm text-white/30">Failed to load detail</p>
                        )}
                      </div>
                    ) : null
                  )}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Local RiskBadge to avoid circular import (DigestCard already imports it)
import RiskBadge from "@/components/RiskBadge";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-6xl mx-auto w-full text-center my-auto min-h-[calc(100vh-3.5rem)]">
      {/* ── Badge / Tag ────────────────────────────────────────── */}
      <div className="animate-fade-in-up mb-4 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
        <span className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-[#ec4899] to-[#06b6d4]" />
        <span className="font-mono text-[11px] text-white/40 tracking-wider uppercase">
          00 · Agent Orchestrator Intelligence Layer
        </span>
      </div>

      {/* ── Hero Headline ──────────────────────────────────────── */}
      <h1 className="animate-fade-in-up-delay-1 text-4xl md:text-5xl lg:text-6xl font-medium tracking-tight text-white/90 max-w-4xl mx-auto leading-[1.15]">
        The missing intelligence layer for{" "}
        <span className="font-serif italic text-transparent bg-clip-text bg-gradient-to-r from-[#ec4899] to-[#06b6d4]">
          autonomous agent fleets.
        </span>
      </h1>

      {/* ── Core Insight Paragraph ─────────────────────────────── */}
      <p className="animate-fade-in-up-delay-2 mt-5 text-base md:text-lg text-white/50 max-w-2xl mx-auto leading-relaxed">
        Agent Orchestrator tracks raw session, PR, and CI events — but cannot prioritize human attention, auto-approve safe operations, or quantify merge risk. Attention Router provides that missing decision layer.
      </p>

      {/* ── Primary CTA Button ──────────────────────────────────── */}
      <div className="animate-fade-in-up-delay-3 mt-8">
        <Link
          href="/queue"
          className="btn-gradient inline-flex items-center gap-2 text-sm font-medium px-6 py-3 rounded-lg shadow-lg hover:shadow-pink-500/20 transition-all duration-200"
        >
          <span>View Live Queue</span>
          <span className="font-mono text-xs opacity-70">→</span>
        </Link>
      </div>

      {/* ── Three Module Preview Cards ──────────────────────────── */}
      <div className="animate-fade-in-up-delay-3 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-5xl w-full mt-12 text-left">
        {/* Card 1: Attention Queue */}
        <Link
          href="/queue"
          className="group p-5 rounded-xl bg-[#0c0c0d] border border-white/[0.06] hover:border-white/[0.15] hover:bg-white/[0.02] transition-all duration-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[11px] text-white/30">01</span>
            <span className="text-white/20 group-hover:text-white/60 group-hover:translate-x-0.5 transition-all text-xs font-mono">
              →
            </span>
          </div>
          <h2 className="text-sm font-medium text-white/80 group-hover:text-white transition-colors">
            Attention Queue
          </h2>
          <p className="text-xs text-white/40 mt-1.5 leading-relaxed">
            Real-time ranked queue prioritizing blocked agents and CI failures over idle background sessions.
          </p>
        </Link>

        {/* Card 2: Policy Gate */}
        <Link
          href="/policies"
          className="group p-5 rounded-xl bg-[#0c0c0d] border border-white/[0.06] hover:border-white/[0.15] hover:bg-white/[0.02] transition-all duration-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[11px] text-white/30">02</span>
            <span className="text-white/20 group-hover:text-white/60 group-hover:translate-x-0.5 transition-all text-xs font-mono">
              →
            </span>
          </div>
          <h2 className="text-sm font-medium text-white/80 group-hover:text-white transition-colors">
            Policy Gate
          </h2>
          <p className="text-xs text-white/40 mt-1.5 leading-relaxed">
            Deterministic rules engine auto-approving safe read-only operations and escalating risky file edits.
          </p>
        </Link>

        {/* Card 3: Merge Digest */}
        <Link
          href="/digest"
          className="group p-5 rounded-xl bg-[#0c0c0d] border border-white/[0.06] hover:border-white/[0.15] hover:bg-white/[0.02] transition-all duration-200"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[11px] text-white/30">03</span>
            <span className="text-white/20 group-hover:text-white/60 group-hover:translate-x-0.5 transition-all text-xs font-mono">
              →
            </span>
          </div>
          <h2 className="text-sm font-medium text-white/80 group-hover:text-white transition-colors">
            Merge Digest
          </h2>
          <p className="text-xs text-white/40 mt-1.5 leading-relaxed">
            Risk-scored daily PR briefings bucketing pull requests by merge readiness and critical risk factors.
          </p>
        </Link>
      </div>
    </div>
  );
}

import type { DigestPR } from "@/lib/api";
import RiskBadge from "./RiskBadge";

interface DigestCardProps {
  pr: DigestPR;
  onClick?: () => void;
}

export default function DigestCard({ pr, onClick }: DigestCardProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left px-4 py-3 border border-white/[0.06] rounded-lg hover:bg-white/[0.03] hover:border-white/[0.1] transition-all duration-150 group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-[13px] text-white/50 shrink-0">
              #{pr.pr_number}
            </span>
            <span className="text-sm text-white/80 truncate">{pr.title}</span>
          </div>
          <p className="font-mono text-[11px] text-white/25 mt-1">{pr.repo}</p>
        </div>
        <RiskBadge score={pr.risk_score} className="shrink-0" />
      </div>

      {/* Risk factors */}
      {pr.risk_factors.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {pr.risk_factors.map((factor) => (
            <span
              key={factor}
              className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-white/[0.04] text-white/30 ring-1 ring-inset ring-white/[0.06]"
            >
              {factor}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}

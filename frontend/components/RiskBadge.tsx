interface RiskBadgeProps {
  score: number;
  className?: string;
}

function getRiskLevel(score: number): { label: string; color: string } {
  if (score >= 0.8) return { label: "Critical", color: "bg-red-500/10 text-red-400 ring-red-500/20" };
  if (score >= 0.6) return { label: "High", color: "bg-orange-500/10 text-orange-400 ring-orange-500/20" };
  if (score >= 0.4) return { label: "Medium", color: "bg-amber-500/10 text-amber-400 ring-amber-500/20" };
  if (score >= 0.2) return { label: "Low", color: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20" };
  return { label: "Minimal", color: "bg-neutral-500/10 text-neutral-400 ring-neutral-500/20" };
}

export default function RiskBadge({ score, className = "" }: RiskBadgeProps) {
  const { label, color } = getRiskLevel(score);
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium ring-1 ring-inset ${color} ${className}`}
    >
      <span className="font-mono tabular-nums">{(score * 100).toFixed(0)}</span>
      <span className="text-[10px] opacity-60">·</span>
      {label}
    </span>
  );
}

export { getRiskLevel };

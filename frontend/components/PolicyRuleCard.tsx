import type { PolicyRule } from "@/lib/api";

interface PolicyRuleCardProps {
  rule: PolicyRule;
  index: number;
}

export default function PolicyRuleCard({ rule, index }: PolicyRuleCardProps) {
  const isAutoApprove = rule.action === "auto_approve";

  return (
    <div className="px-4 py-3 border-b border-white/[0.04] group hover:bg-white/[0.02] transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-baseline gap-2.5 min-w-0">
          <span className="text-[10px] font-mono text-white/20 tabular-nums shrink-0">
            {String(index + 1).padStart(2, "0")}
          </span>
          <div className="min-w-0">
            <p className="text-sm text-white/80 truncate">{rule.name}</p>
            <p className="font-mono text-[11px] text-white/30 mt-0.5 truncate">
              {rule.condition_type}: {rule.pattern}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Action pill */}
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ring-1 ring-inset ${
              isAutoApprove
                ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20"
                : "bg-amber-500/10 text-amber-400 ring-amber-500/20"
            }`}
          >
            {isAutoApprove ? "auto_approve" : "escalate"}
          </span>

          {/* Enabled indicator */}
          <div
            className={`w-2 h-2 rounded-full ${
              rule.enabled ? "bg-emerald-500" : "bg-neutral-600"
            }`}
            title={rule.enabled ? "Enabled" : "Disabled"}
          />
        </div>
      </div>
    </div>
  );
}

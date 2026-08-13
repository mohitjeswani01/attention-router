"use client";

import type { AttentionItem } from "@/lib/api";
import IdleTimeCounter from "./IdleTimeCounter";

interface AttentionQueueItemProps {
  item: AttentionItem;
  isSelected: boolean;
  index: number;
  onClick: () => void;
}

const REASON_STYLES: Record<string, { dot: string; bg: string; label: string }> = {
  idle_on_approval: {
    dot: "bg-amber-500",
    bg: "bg-amber-500/10 text-amber-400 ring-amber-500/20",
    label: "Awaiting Approval",
  },
  ci_failed: {
    dot: "bg-red-500",
    bg: "bg-red-500/10 text-red-400 ring-red-500/20",
    label: "CI Failed",
  },
  review_requested: {
    dot: "bg-blue-400",
    bg: "bg-blue-400/10 text-blue-300 ring-blue-400/20",
    label: "Review Requested",
  },
  working: {
    dot: "bg-emerald-500",
    bg: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20",
    label: "Working",
  },
  idle: {
    dot: "bg-neutral-500",
    bg: "bg-neutral-500/10 text-neutral-400 ring-neutral-500/20",
    label: "Idle",
  },
};

function getReasonStyle(reason: string) {
  return (
    REASON_STYLES[reason] || {
      dot: "bg-neutral-600",
      bg: "bg-neutral-600/10 text-neutral-500 ring-neutral-600/20",
      label: reason,
    }
  );
}

export default function AttentionQueueItem({
  item,
  isSelected,
  index,
  onClick,
}: AttentionQueueItemProps) {
  const style = getReasonStyle(item.reason);
  const shortId = item.session_id.slice(0, 8);

  return (
    <button
      onClick={onClick}
      className={`
        group w-full text-left px-4 py-3 border-b border-white/[0.04]
        transition-all duration-150 relative
        ${
          isSelected
            ? "bg-white/[0.06]"
            : "hover:bg-white/[0.03]"
        }
      `}
    >
      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute left-0 top-3 bottom-3 w-[2px] bg-gradient-to-b from-[#ec4899] to-[#06b6d4] rounded-r" />
      )}

      <div className="flex items-start justify-between gap-3">
        {/* Left: rank + id */}
        <div className="flex items-baseline gap-2.5 min-w-0">
          <span className="text-[10px] font-mono text-white/20 tabular-nums shrink-0">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="font-mono text-[13px] text-white/80 tracking-tight truncate">
            {shortId}
          </span>
        </div>

        {/* Right: idle time */}
        {item.idle_seconds > 0 && (
          <IdleTimeCounter
            idleSeconds={item.idle_seconds}
            className="text-white/40 shrink-0"
          />
        )}
      </div>

      {/* Status pill */}
      <div className="mt-1.5 flex items-center gap-1.5">
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium ring-1 ring-inset ${style.bg}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
          {style.label}
        </span>
      </div>
    </button>
  );
}

export { REASON_STYLES, getReasonStyle };

"use client";

import { useEffect, useState } from "react";

interface IdleTimeCounterProps {
  idleSeconds: number;
  /** When the attention item was created — used to live-tick the counter */
  createdAt?: string;
  className?: string;
}

function humanize(totalSeconds: number): string {
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  if (m < 60) return s > 0 ? `${m}m ${s}s` : `${m}m`;
  const h = Math.floor(m / 60);
  const rm = m % 60;
  if (h < 24) return rm > 0 ? `${h}h ${rm}m` : `${h}h`;
  const d = Math.floor(h / 24);
  const rh = h % 24;
  return rh > 0 ? `${d}d ${rh}h` : `${d}d`;
}

export default function IdleTimeCounter({
  idleSeconds,
  className = "",
}: IdleTimeCounterProps) {
  const [elapsed, setElapsed] = useState(idleSeconds);

  useEffect(() => {
    setElapsed(idleSeconds);
    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [idleSeconds]);

  return (
    <span
      className={`font-mono text-xs tabular-nums tracking-tight ${className}`}
    >
      {humanize(elapsed)}
    </span>
  );
}

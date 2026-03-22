"use client";
import { clsx } from "clsx";

interface Props {
  confidence: number; // 0-1
  size?: "sm" | "md";
}

export function ConfidenceBadge({ confidence, size = "md" }: Props) {
  const pct = Math.round(confidence * 100);
  const color =
    pct >= 80 ? "text-emerald-400 bg-emerald-900/20 border-emerald-700/30" :
    pct >= 60 ? "text-amber-400 bg-amber-900/15 border-amber-700/25" :
    "text-red-400 bg-red-900/15 border-red-700/25";

  return (
    <span className={clsx(
      "inline-flex items-center gap-1 rounded border font-medium",
      size === "sm" ? "text-[9px] px-1 py-0" : "text-[10px] px-1.5 py-0.5",
      color
    )}>
      {pct}% confidence
    </span>
  );
}

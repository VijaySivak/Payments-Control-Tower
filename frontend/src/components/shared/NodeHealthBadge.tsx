"use client";
import type { NodeHealthStatus } from "@/lib/types";

const STYLES: Record<NodeHealthStatus, string> = {
  HEALTHY: "bg-emerald-500/10 text-emerald-400",
  DEGRADED: "bg-amber-500/10 text-amber-400",
  CRITICAL: "bg-red-500/15 text-red-400",
  OFFLINE: "bg-slate-500/20 text-slate-400",
};

const DOT: Record<NodeHealthStatus, string> = {
  HEALTHY: "bg-emerald-400",
  DEGRADED: "bg-amber-400",
  CRITICAL: "bg-red-400",
  OFFLINE: "bg-slate-500",
};

export function NodeHealthBadge({ status, className = "" }: { status: NodeHealthStatus; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${STYLES[status]} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${DOT[status]}`} />
      {status}
    </span>
  );
}

"use client";
import type { ActionStatus } from "@/lib/types";

const ACTION_STATUS_STYLES: Record<ActionStatus, string> = {
  OPEN: "bg-red-500/10 text-red-400",
  TRIAGED: "bg-amber-500/10 text-amber-400",
  IN_PROGRESS: "bg-blue-500/10 text-blue-400",
  MITIGATED: "bg-purple-500/10 text-purple-400",
  RESOLVED: "bg-emerald-500/10 text-emerald-400",
};

const ACTION_STATUS_LABELS: Record<ActionStatus, string> = {
  OPEN: "Open",
  TRIAGED: "Triaged",
  IN_PROGRESS: "In Progress",
  MITIGATED: "Mitigated",
  RESOLVED: "Resolved",
};

interface ActionStatusBadgeProps {
  status: ActionStatus;
  className?: string;
}

export function ActionStatusBadge({ status, className = "" }: ActionStatusBadgeProps) {
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold ${ACTION_STATUS_STYLES[status] ?? "bg-slate-500/10 text-slate-400"} ${className}`}>
      {ACTION_STATUS_LABELS[status] ?? status}
    </span>
  );
}

"use client";
import { AlertTriangle, Clock } from "lucide-react";

interface SLABadgeProps {
  breach: boolean;
  breachSeconds?: number;
  recovered?: boolean;
  className?: string;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(0)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

export function SLABadge({ breach, breachSeconds, recovered, className = "" }: SLABadgeProps) {
  if (!breach) {
    return (
      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 ${className}`}>
        <Clock className="w-2.5 h-2.5" />
        SLA OK
      </span>
    );
  }
  if (recovered) {
    return (
      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-500/10 text-blue-400 ${className}`}>
        <Clock className="w-2.5 h-2.5" />
        SLA Recovered
      </span>
    );
  }
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-red-500/15 text-red-400 ${className}`}>
      <AlertTriangle className="w-2.5 h-2.5" />
      SLA Breach{breachSeconds ? ` +${formatDuration(breachSeconds)}` : ""}
    </span>
  );
}

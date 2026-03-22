"use client";
import { clsx } from "clsx";
import { Brain, AlertTriangle, CheckCircle2, Clock, Zap } from "lucide-react";
import type { AISummary } from "@/lib/types";

interface Props {
  summary: AISummary;
}

const URGENCY_STYLE: Record<string, { border: string; icon: JSX.Element; badge: string }> = {
  IMMEDIATE: {
    border: "border-red-700/50 bg-red-900/15",
    icon: <AlertTriangle className="w-4 h-4 text-red-400" />,
    badge: "bg-red-500/20 text-red-300 border-red-500/30",
  },
  HIGH: {
    border: "border-amber-700/40 bg-amber-900/10",
    icon: <Zap className="w-4 h-4 text-amber-400" />,
    badge: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  },
  MEDIUM: {
    border: "border-yellow-700/30 bg-yellow-900/8",
    icon: <Clock className="w-4 h-4 text-yellow-400" />,
    badge: "bg-yellow-500/15 text-yellow-300 border-yellow-500/25",
  },
  LOW: {
    border: "border-white/15 bg-white/5",
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
    badge: "bg-white/8 text-slate-300 border-white/15",
  },
};

export function AISummaryBanner({ summary }: Props) {
  const style = URGENCY_STYLE[summary.urgency] ?? URGENCY_STYLE.MEDIUM;

  return (
    <div className={clsx("rounded-xl border px-4 py-4 space-y-3", style.border)}>
      {/* Header row */}
      <div className="flex items-start gap-3">
        <div className="flex items-center gap-2 flex-shrink-0 mt-0.5">
          <Brain className="w-4 h-4 text-violet-400" />
          {style.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-[10px] font-bold text-violet-400 uppercase">AI Analysis</span>
            <span className={clsx("text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase", style.badge)}>
              {summary.urgency.replace(/_/g, " ")}
            </span>
            <span className="text-[10px] text-slate-500 ml-auto">
              Risk: <span className="font-bold text-slate-300">{summary.risk_level}</span>
            </span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed">{summary.operator_summary}</p>
        </div>
      </div>

      {/* 3-part drill-down */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1 border-t border-white/8">
        <div>
          <p className="text-[10px] font-bold text-red-400 uppercase mb-1">What Went Wrong</p>
          <p className="text-xs text-slate-300">{summary.what_went_wrong}</p>
        </div>
        <div>
          <p className="text-[10px] font-bold text-amber-400 uppercase mb-1">Why It Happened</p>
          <p className="text-xs text-slate-400">{summary.why_it_happened}</p>
        </div>
        <div>
          <p className="text-[10px] font-bold text-emerald-400 uppercase mb-1">What To Do</p>
          <p className="text-xs text-slate-300">{summary.what_to_do}</p>
        </div>
      </div>

      {/* Key facts + confidence */}
      <div className="flex items-center gap-3 flex-wrap pt-1 border-t border-white/8">
        <div className="flex flex-wrap gap-1.5 flex-1">
          {summary.key_facts.map((f, i) => (
            <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">{f}</span>
          ))}
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className="text-[10px] text-slate-500">Confidence</span>
          <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div className="h-full bg-violet-500 rounded-full" style={{ width: `${summary.confidence * 100}%` }} />
          </div>
          <span className="text-[10px] font-bold text-violet-300">{(summary.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}

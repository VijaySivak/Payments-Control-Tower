"use client";
import { useState } from "react";
import { clsx } from "clsx";
import { ChevronDown, ChevronRight, Zap, Clock, User, AlertTriangle } from "lucide-react";
import type { Recommendation } from "@/lib/types";

interface Props {
  recommendations: Recommendation[];
  compact?: boolean;
}

const PRIORITY_CHIP: Record<string, string> = {
  CRITICAL: "bg-red-500/20 text-red-300 border border-red-500/30",
  HIGH: "bg-amber-500/20 text-amber-300 border border-amber-500/30",
  MEDIUM: "bg-yellow-500/15 text-yellow-300 border border-yellow-500/25",
  LOW: "bg-white/5 text-slate-400 border border-white/10",
};

const URGENCY_COLOR: Record<string, string> = {
  IMMEDIATE: "text-red-400",
  WITHIN_1H: "text-amber-400",
  WITHIN_24H: "text-yellow-400",
  MONITOR: "text-slate-400",
};

const OWNER_ICON: Record<string, string> = {
  COMPLIANCE: "🔒",
  OPS: "🔧",
  TECH: "💻",
  TREASURY: "💰",
  AUTOMATIC: "⚡",
};

export function RecommendationList({ recommendations, compact = false }: Props) {
  const [expanded, setExpanded] = useState<string | null>(compact ? null : recommendations[0]?.recommendation_id ?? null);

  if (!recommendations.length) {
    return (
      <p className="text-xs text-slate-500 italic py-2">No recommendations available</p>
    );
  }

  return (
    <div className="space-y-2">
      {recommendations.map((rec, i) => {
        const isOpen = expanded === rec.recommendation_id;
        return (
          <div
            key={rec.recommendation_id}
            className={clsx(
              "rounded-xl border overflow-hidden transition",
              isOpen ? "border-blue-500/30 bg-blue-900/8" : "border-white/10 bg-white/3 hover:border-white/20"
            )}
          >
            <button
              onClick={() => setExpanded(isOpen ? null : rec.recommendation_id)}
              className="w-full flex items-center gap-3 px-4 py-3 text-left"
            >
              <span className="text-slate-500 text-xs font-bold w-4">{i + 1}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-0.5">
                  <span className={clsx("text-[10px] font-bold px-1.5 py-0.5 rounded uppercase", PRIORITY_CHIP[rec.priority] ?? PRIORITY_CHIP.LOW)}>
                    {rec.priority}
                  </span>
                  <span className={clsx("text-[10px] font-medium", URGENCY_COLOR[rec.execution_urgency] ?? "text-slate-400")}>
                    {rec.execution_urgency.replace(/_/g, " ")}
                  </span>
                  <span className="text-[10px] text-slate-500 ml-auto">
                    {OWNER_ICON[rec.recommended_owner]} {rec.recommended_owner}
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-200 truncate">{rec.title}</p>
              </div>
              {isOpen ? <ChevronDown className="w-4 h-4 text-slate-500 flex-shrink-0" /> : <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0" />}
            </button>

            {isOpen && (
              <div className="px-4 pb-4 pt-1 space-y-3 border-t border-white/8">
                <p className="text-xs text-slate-300 leading-relaxed">{rec.description}</p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-500 uppercase mb-1">Rationale</p>
                    <p className="text-xs text-slate-400">{rec.rationale}</p>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <p className="text-[10px] font-semibold text-slate-500 uppercase mb-0.5">Estimated Impact</p>
                      <p className="text-xs text-emerald-300">{rec.estimated_impact}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-semibold text-slate-500 uppercase mb-0.5">Estimated Effort</p>
                      <p className="text-xs text-slate-300">{rec.estimated_effort}</p>
                    </div>
                  </div>
                </div>

                {rec.preconditions.length > 0 && (
                  <div>
                    <p className="text-[10px] font-semibold text-slate-500 uppercase mb-1">Preconditions</p>
                    <ul className="space-y-0.5">
                      {rec.preconditions.map((p, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                          <span className="w-1 h-1 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                          {p}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {rec.risk_notes && (
                  <div className="px-3 py-2 rounded-lg bg-amber-900/15 border border-amber-700/25">
                    <div className="flex items-start gap-1.5">
                      <AlertTriangle className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-amber-300">{rec.risk_notes}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-2 pt-1">
                  <span className="text-[10px] text-slate-500">Confidence:</span>
                  <div className="flex-1 max-w-[120px] h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${rec.confidence_score * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-400">{(rec.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

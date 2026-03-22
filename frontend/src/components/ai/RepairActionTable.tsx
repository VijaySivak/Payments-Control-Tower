"use client";
import { clsx } from "clsx";
import { ShieldAlert, ShieldCheck, Users, Zap } from "lucide-react";
import type { RepairAction } from "@/lib/types";

interface Props {
  actions: RepairAction[];
}

const RISK_COLOR: Record<string, string> = {
  HIGH: "text-red-400 bg-red-900/20 border-red-700/30",
  MEDIUM: "text-amber-400 bg-amber-900/15 border-amber-700/25",
  LOW: "text-emerald-400 bg-emerald-900/15 border-emerald-700/25",
};

const ACTION_TYPE_LABEL: Record<string, string> = {
  RETRY_STAGE: "Retry Stage",
  REROUTE_PAYMENT: "Reroute",
  ESCALATE_TO_OPERATIONS: "Escalate to Ops",
  REQUEST_DATA_FIX: "Request Data Fix",
  MARK_FALSE_POSITIVE: "Mark False Positive",
  HOLD_AND_MONITOR: "Hold & Monitor",
  FORCE_RECONCILIATION_RECHECK: "Force Recon Recheck",
  SWITCH_CORRIDOR: "Switch Corridor",
  PRIORITIZE_FOR_MANUAL_HANDLING: "Prioritize Manual",
};

export function RepairActionTable({ actions }: Props) {
  if (!actions.length) {
    return <p className="text-xs text-slate-500 italic py-2">No repair actions available</p>;
  }

  return (
    <div className="space-y-2">
      {actions.map((action) => (
        <div
          key={action.action_id}
          className="rounded-xl border border-white/10 bg-white/3 px-4 py-3 space-y-2"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-0.5">
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white/8 text-slate-400 border border-white/10">
                  {ACTION_TYPE_LABEL[action.action_type] ?? action.action_type}
                </span>
                <span className={clsx("text-[10px] font-bold px-1.5 py-0.5 rounded border", RISK_COLOR[action.risk_level] ?? RISK_COLOR.LOW)}>
                  {action.risk_level} RISK
                </span>
                {action.requires_human_approval && (
                  <span className="flex items-center gap-1 text-[10px] text-violet-300 bg-violet-900/20 border border-violet-500/25 px-1.5 py-0.5 rounded">
                    <Users className="w-2.5 h-2.5" /> Human Approval Required
                  </span>
                )}
              </div>
              <p className="text-sm font-semibold text-white">{action.title}</p>
            </div>
            <div className="flex-shrink-0 text-right">
              <p className="text-[10px] text-slate-500">Success est.</p>
              <p className={clsx("text-sm font-bold",
                action.estimated_success_probability >= 0.7 ? "text-emerald-400" :
                action.estimated_success_probability >= 0.5 ? "text-amber-400" : "text-red-400"
              )}>
                {(action.estimated_success_probability * 100).toFixed(0)}%
              </p>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">{action.description}</p>

          {action.execution_notes && (
            <div className={clsx(
              "px-3 py-2 rounded-lg text-xs border",
              action.execution_notes.startsWith("[ADVISORY") || action.execution_notes.startsWith("[SIMULATED")
                ? "text-violet-300 bg-violet-900/10 border-violet-700/20"
                : "text-slate-400 bg-white/4 border-white/8"
            )}>
              {action.execution_notes}
            </div>
          )}

          {action.blocking_conditions.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-red-400 uppercase mb-1">Blocking Conditions</p>
              <ul className="space-y-0.5">
                {action.blocking_conditions.map((c, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                    <span className="w-1 h-1 rounded-full bg-red-500 mt-1.5 flex-shrink-0" />
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

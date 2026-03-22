"use client";
import { useState } from "react";
import { clsx } from "clsx";
import { ChevronDown, ChevronRight, CheckCircle2, XCircle, SkipForward, Cpu, Shield } from "lucide-react";
import type { AgentTrace, AgentOutput, PolicyDecision } from "@/lib/types";
import { formatDate } from "@/lib/formatters";

interface Props {
  trace: AgentTrace;
}

const STATUS_ICON = {
  SUCCESS: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
  ERROR: <XCircle className="w-3.5 h-3.5 text-red-400" />,
  SKIPPED: <SkipForward className="w-3.5 h-3.5 text-slate-500" />,
};

const STATUS_BG: Record<string, string> = {
  SUCCESS: "border-emerald-700/30 bg-emerald-900/8",
  ERROR: "border-red-700/30 bg-red-900/8",
  SKIPPED: "border-white/10 bg-white/3 opacity-60",
};

function AgentCard({ agent }: { agent: AgentOutput }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={clsx("rounded-lg border overflow-hidden", STATUS_BG[agent.status] ?? STATUS_BG.SKIPPED)}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-white/4"
      >
        {STATUS_ICON[agent.status as keyof typeof STATUS_ICON] ?? STATUS_ICON.SKIPPED}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-200">{agent.agent_name}</span>
            <span className="text-[10px] text-slate-500">{agent.duration_ms}ms</span>
          </div>
          <p className="text-[10px] text-slate-400 truncate">{agent.output_summary}</p>
        </div>
        {open ? <ChevronDown className="w-3 h-3 text-slate-500" /> : <ChevronRight className="w-3 h-3 text-slate-500" />}
      </button>
      {open && (
        <div className="px-3 pb-3 pt-1 space-y-2 border-t border-white/8">
          {agent.key_findings.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-slate-500 uppercase mb-1">Key Findings</p>
              <ul className="space-y-0.5">
                {agent.key_findings.map((f, i) => (
                  <li key={i} className="text-[10px] text-slate-300 flex items-start gap-1.5">
                    <span className="text-blue-400 mt-0.5">›</span> {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {agent.data_consumed.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[10px] text-slate-500">Data consumed:</span>
              {agent.data_consumed.map((d, i) => (
                <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 border border-white/8 text-slate-500">{d}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AgentTracePanel({ trace }: Props) {
  const [showTrace, setShowTrace] = useState(false);
  const [showPolicies, setShowPolicies] = useState(false);

  const successCount = trace.agents_run.filter(a => a.status === "SUCCESS").length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-violet-400" />
            <span className="text-sm font-semibold text-white">Agent Execution Trace</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-900/30 text-violet-300 border border-violet-500/25">
              {trace.mode}
            </span>
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {successCount}/{trace.agents_run.length} agents succeeded · {trace.total_duration_ms}ms total
          </p>
        </div>
        <div className="text-[10px] text-slate-500 text-right">
          <p>ID: {trace.execution_id.slice(0, 8)}...</p>
          <p>{formatDate(trace.completed_at)}</p>
        </div>
      </div>

      {/* Agent pipeline */}
      <div className="space-y-1.5">
        {trace.agents_run.map((agent, i) => (
          <AgentCard key={i} agent={agent} />
        ))}
      </div>

      {/* Guardrail notes */}
      {trace.guardrail_notes.length > 0 && (
        <div className="px-3 py-2 rounded-xl bg-amber-900/10 border border-amber-700/25">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Shield className="w-3.5 h-3.5 text-amber-400" />
            <p className="text-xs font-semibold text-amber-300">Policy / Guardrail Notes</p>
          </div>
          <ul className="space-y-1">
            {trace.guardrail_notes.map((n, i) => (
              <li key={i} className="text-xs text-amber-200/80">{n}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Policy decisions */}
      {trace.policy_decisions.filter(d => d.triggered).length > 0 && (
        <div>
          <button
            onClick={() => setShowPolicies(!showPolicies)}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 mb-2"
          >
            <Shield className="w-3 h-3" />
            Policy Decisions ({trace.policy_decisions.filter(d => d.triggered).length} triggered)
            {showPolicies ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>
          {showPolicies && (
            <div className="space-y-1.5">
              {trace.policy_decisions.filter(d => d.triggered).map((d, i) => (
                <div key={i} className="px-3 py-2 rounded-lg bg-white/4 border border-white/8">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[10px] font-bold text-slate-400">{d.rule_name}</span>
                    <span className="text-[10px] px-1 py-0.5 rounded bg-amber-900/20 text-amber-400 border border-amber-700/20">{d.action_taken}</span>
                  </div>
                  <p className="text-[10px] text-slate-400">{d.reason}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Full reasoning trace */}
      <div>
        <button
          onClick={() => setShowTrace(!showTrace)}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 mb-2"
        >
          Full Reasoning Trace
          {showTrace ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        </button>
        {showTrace && (
          <div className="bg-[#050c1a] rounded-xl border border-white/8 p-3 max-h-48 overflow-y-auto">
            {trace.reasoning_trace.map((line, i) => (
              <p key={i} className="text-[10px] text-slate-400 font-mono leading-5">{line}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

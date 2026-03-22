"use client";
import { useState } from "react";
import { clsx } from "clsx";
import { ChevronDown, ChevronRight, Search, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import type { RCAResult, ReasoningStep } from "@/lib/types";

interface Props {
  rca: RCAResult;
  compact?: boolean;
}

const PRIORITY_COLOR: Record<string, string> = {
  CRITICAL: "text-red-400 bg-red-900/20 border-red-700/40",
  HIGH: "text-amber-400 bg-amber-900/20 border-amber-700/40",
  MEDIUM: "text-yellow-400 bg-yellow-900/20 border-yellow-700/30",
  LOW: "text-slate-300 bg-white/5 border-white/15",
};

const CATEGORY_COLOR: Record<string, string> = {
  COMPLIANCE: "text-purple-300 bg-purple-900/20",
  ROUTING: "text-blue-300 bg-blue-900/20",
  VALIDATION: "text-amber-300 bg-amber-900/20",
  FX: "text-cyan-300 bg-cyan-900/20",
  SETTLEMENT: "text-orange-300 bg-orange-900/20",
  OPERATIONAL: "text-slate-300 bg-slate-800/60",
};

function StepCard({ step, index }: { step: ReasoningStep; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-white/8 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-3 py-2 hover:bg-white/4 transition text-left"
      >
        <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 text-[10px] font-bold flex items-center justify-center flex-shrink-0">
          {step.step_number}
        </span>
        <span className="flex-1 text-xs font-medium text-slate-300">{step.label}</span>
        {open ? <ChevronDown className="w-3 h-3 text-slate-500" /> : <ChevronRight className="w-3 h-3 text-slate-500" />}
      </button>
      {open && (
        <div className="px-3 pb-3 pt-1 space-y-2 bg-white/2">
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-medium mb-0.5">Observation</p>
            <p className="text-xs text-slate-300">{step.observation}</p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-medium mb-0.5">Evidence</p>
            <p className="text-xs text-slate-400">{step.evidence}</p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase font-medium mb-0.5">Conclusion</p>
            <p className="text-xs text-emerald-300">{step.conclusion}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export function RCASummaryCard({ rca, compact = false }: Props) {
  const [showSteps, setShowSteps] = useState(!compact);
  const [showAlts, setShowAlts] = useState(false);
  const [showEvidence, setShowEvidence] = useState(!compact);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className={clsx("rounded-xl border px-4 py-3", PRIORITY_COLOR[rca.resolution_priority] ?? PRIORITY_COLOR.MEDIUM)}>
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className={clsx("text-[10px] font-bold px-2 py-0.5 rounded uppercase", CATEGORY_COLOR[rca.issue_category] ?? "text-slate-300 bg-white/5")}>
                {rca.issue_category}
              </span>
              <span className="text-[10px] text-slate-500">Stage: {rca.impacted_stage}</span>
              {rca.impacted_node && <span className="text-[10px] text-slate-500">Node: {rca.impacted_node}</span>}
              <span className="ml-auto text-[10px] font-semibold">Confidence: {(rca.confidence_score * 100).toFixed(0)}%</span>
            </div>
            <p className="text-sm font-semibold">{rca.primary_issue}</p>
          </div>
        </div>
      </div>

      {/* Root cause */}
      <div className="px-4 py-3 bg-white/4 rounded-xl border border-white/10">
        <p className="text-[10px] font-semibold text-slate-500 uppercase mb-1">Root Cause</p>
        <p className="text-sm text-slate-200 leading-relaxed">{rca.likely_root_cause}</p>
      </div>

      {/* Customer + Ops impact */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="px-3 py-2 rounded-lg bg-white/4 border border-white/8">
          <p className="text-[10px] font-semibold text-blue-400 uppercase mb-1">Customer Impact</p>
          <p className="text-xs text-slate-300">{rca.customer_impact_summary}</p>
        </div>
        <div className="px-3 py-2 rounded-lg bg-white/4 border border-white/8">
          <p className="text-[10px] font-semibold text-amber-400 uppercase mb-1">Operations Impact</p>
          <p className="text-xs text-slate-300">{rca.operations_impact_summary}</p>
        </div>
      </div>

      {/* Contributing factors */}
      {rca.contributing_factors.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-slate-400 mb-2">Contributing Factors</p>
          <ul className="space-y-1">
            {rca.contributing_factors.map((f, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                <span className="w-1 h-1 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Supporting evidence */}
      {rca.supporting_evidence.length > 0 && (
        <div>
          <button
            onClick={() => setShowEvidence(!showEvidence)}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 mb-2"
          >
            <Info className="w-3 h-3" />
            Supporting Evidence ({rca.supporting_evidence.length})
            {showEvidence ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>
          {showEvidence && (
            <div className="flex flex-wrap gap-1.5">
              {rca.supporting_evidence.map((e, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">
                  {e}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Reasoning steps */}
      {rca.reasoning_steps.length > 0 && (
        <div>
          <button
            onClick={() => setShowSteps(!showSteps)}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 mb-2"
          >
            <Search className="w-3 h-3" />
            Reasoning Steps ({rca.reasoning_steps.length})
            {showSteps ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>
          {showSteps && (
            <div className="space-y-1.5">
              {rca.reasoning_steps.map((step, i) => (
                <StepCard key={i} step={step} index={i} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Next checks */}
      {rca.recommended_next_checks.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-slate-400 mb-2">Recommended Next Checks</p>
          <ol className="space-y-1">
            {rca.recommended_next_checks.map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                <span className="text-[10px] font-bold text-slate-500 w-4 flex-shrink-0">{i + 1}.</span>
                {c}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Alternative hypotheses */}
      {rca.alternative_hypotheses.length > 0 && (
        <div>
          <button
            onClick={() => setShowAlts(!showAlts)}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 mb-2"
          >
            <CheckCircle2 className="w-3 h-3" />
            Alternative Hypotheses Considered
            {showAlts ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>
          {showAlts && (
            <div className="space-y-2">
              {rca.alternative_hypotheses.map((alt, i) => (
                <div key={i} className="px-3 py-2 rounded-lg bg-white/3 border border-white/8">
                  <p className="text-xs text-slate-400 line-through">{alt.hypothesis}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">Rejected: {alt.reason_rejected}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

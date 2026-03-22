"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { paymentsApi, aiApi } from "@/lib/api/payments";
import { Panel } from "@/components/shared/Panel";
import { SectionHeader } from "@/components/shared/SectionHeader";
import { StageBadge, StatusBadge, SeverityBadge, AnomalyTypeBadge } from "@/components/shared/Badge";
import { SLABadge } from "@/components/shared/SLABadge";
import { formatCurrency, formatDate, formatDuration } from "@/lib/formatters";
import type { AnomalyType, PaymentType, SimulationResponse, ReplayComparisonResponse } from "@/lib/types";
import { Play, RefreshCw, Zap, AlertTriangle, RotateCcw, ChevronRight, Activity, FlaskConical, GitCompare, Brain } from "lucide-react";
import type { AIPackage } from "@/lib/types";
import { clsx } from "clsx";

const ANOMALY_INJECT_OPTIONS: Array<{ value: AnomalyType | ""; label: string }> = [
  { value: "", label: "None (clean payment)" },
  { value: "SANCTIONS_FALSE_POSITIVE", label: "Sanctions False Positive" },
  { value: "GATEWAY_TIMEOUT", label: "Gateway Timeout" },
  { value: "VALIDATION_ERROR", label: "Validation Error" },
  { value: "FX_DELAY", label: "FX Rate Delay" },
  { value: "MISSING_INTERMEDIARY", label: "Missing Intermediary" },
  { value: "SETTLEMENT_DELAY", label: "Settlement Delay" },
  { value: "RECONCILIATION_MISMATCH", label: "Reconciliation Mismatch" },
];

const PAYMENT_TYPES: PaymentType[] = ["SWIFT", "WIRE", "ACH", "SEPA", "RTGS", "INSTANT"];

const PRESET_CORRIDORS = [
  { source: "US", dest: "GB", label: "US → UK" },
  { source: "GB", dest: "SG", label: "UK → Singapore" },
  { source: "DE", dest: "JP", label: "Germany → Japan" },
  { source: "SG", dest: "IN", label: "Singapore → India" },
  { source: "US", dest: "AE", label: "US → UAE" },
  { source: "AU", dest: "US", label: "Australia → US" },
];

export default function ReplayPage() {
  const router = useRouter();
  const [simulating, setSimulating] = useState(false);
  const [replaying, setReplaying] = useState(false);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [comparison, setComparison] = useState<ReplayComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [replayId, setReplayId] = useState("");
  const [advancedMode, setAdvancedMode] = useState(false);
  const [advancedReplayMode, setAdvancedReplayMode] = useState(false);
  const [aiPackage, setAiPackage] = useState<AIPackage | null>(null);
  const [aiLoading, setAiLoading] = useState(false);

  const [form, setForm] = useState({
    source_country: "",
    destination_country: "",
    amount: "",
    payment_type: "" as PaymentType | "",
    inject_anomaly: "" as AnomalyType | "",
    priority: "" as string,
    force_scenario: "" as string,
    inject_delay_node: "" as string,
  });

  const handleSimulate = async () => {
    setSimulating(true);
    setError(null);
    setResult(null);
    setComparison(null);
    try {
      const req = {
        source_country: form.source_country || undefined,
        destination_country: form.destination_country || undefined,
        amount: form.amount ? parseFloat(form.amount) : undefined,
        payment_type: (form.payment_type || undefined) as PaymentType | undefined,
        inject_anomaly: (form.inject_anomaly || undefined) as AnomalyType | undefined,
      };
      if (advancedMode) {
        const res = await paymentsApi.simulateAdvanced({
          ...req,
          priority: (form.priority || undefined) as any,
          force_scenario: form.force_scenario || undefined,
          inject_delay_node: form.inject_delay_node || undefined,
        });
        setResult(res);
      } else {
        const res = await paymentsApi.simulate(req);
        setResult(res);
        if (res.anomaly) {
          fetchAIPackage(res.payment.id);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setSimulating(false);
    }
  };

  const fetchAIPackage = async (paymentId: string) => {
    setAiLoading(true);
    setAiPackage(null);
    try {
      const pkg = await aiApi.paymentAIPackage(paymentId);
      setAiPackage(pkg);
    } catch {
      // AI analysis is optional — silently ignore
    } finally {
      setAiLoading(false);
    }
  };

  const handleReplay = async () => {
    if (!replayId.trim()) return;
    setReplaying(true);
    setError(null);
    setResult(null);
    setComparison(null);
    try {
      if (advancedReplayMode) {
        const res = await paymentsApi.replayAdvanced(replayId.trim());
        setComparison(res);
      } else {
        const res = await paymentsApi.replay(replayId.trim());
        setResult(res);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Replay failed");
    } finally {
      setReplaying(false);
    }
  };

  const applyPreset = (source: string, dest: string) => {
    setForm((f) => ({ ...f, source_country: source, destination_country: dest }));
  };

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-6 space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white">Simulation & Replay</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Simulate new payment scenarios or replay existing payment journeys
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Simulation form */}
        <Panel>
          <div className="flex items-center justify-between mb-5">
            <SectionHeader title="Simulate New Payment" icon={Play} />
            <button
              onClick={() => setAdvancedMode(!advancedMode)}
              className={clsx(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition",
                advancedMode
                  ? "bg-violet-500/20 border-violet-500/50 text-violet-300"
                  : "bg-white/5 border-white/10 text-slate-400 hover:text-slate-200"
              )}
            >
              <FlaskConical className="w-3 h-3" />
              Advanced
            </button>
          </div>

          {/* Corridor presets */}
          <div className="mb-4">
            <label className="text-xs text-slate-400 mb-2 block">Quick Corridors</label>
            <div className="flex flex-wrap gap-2">
              {PRESET_CORRIDORS.map(({ source, dest, label }) => (
                <button
                  key={label}
                  onClick={() => applyPreset(source, dest)}
                  className={clsx(
                    "px-2.5 py-1 text-xs rounded-lg border transition",
                    form.source_country === source && form.destination_country === dest
                      ? "border-blue-500 bg-blue-500/15 text-blue-300"
                      : "border-white/15 bg-white/5 text-slate-400 hover:border-white/30 hover:text-slate-200"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Source Country</label>
                <input
                  type="text"
                  placeholder="e.g. US"
                  value={form.source_country}
                  onChange={(e) => setForm((f) => ({ ...f, source_country: e.target.value.toUpperCase() }))}
                  className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Destination Country</label>
                <input
                  type="text"
                  placeholder="e.g. GB"
                  value={form.destination_country}
                  onChange={(e) => setForm((f) => ({ ...f, destination_country: e.target.value.toUpperCase() }))}
                  className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Amount (USD)</label>
                <input
                  type="number"
                  placeholder="e.g. 50000"
                  value={form.amount}
                  onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                  className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Payment Type</label>
                <select
                  value={form.payment_type}
                  onChange={(e) => setForm((f) => ({ ...f, payment_type: e.target.value as PaymentType | "" }))}
                  className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50"
                >
                  <option value="">Random</option>
                  {PAYMENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-1 block">Inject Anomaly</label>
              <select
                value={form.inject_anomaly}
                onChange={(e) => setForm((f) => ({ ...f, inject_anomaly: e.target.value as AnomalyType | "" }))}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50"
              >
                {ANOMALY_INJECT_OPTIONS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            {/* Advanced mode fields */}
            {advancedMode && (
              <div className="space-y-3 pt-3 border-t border-violet-500/20">
                <p className="text-[10px] font-semibold text-violet-400 uppercase tracking-wide">Advanced Parameters</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">Priority</label>
                    <select
                      value={form.priority}
                      onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
                      className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-violet-500/50"
                    >
                      <option value="">Default</option>
                      {["LOW","MEDIUM","HIGH","CRITICAL"].map((p) => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">Force Scenario</label>
                    <select
                      value={form.force_scenario}
                      onChange={(e) => setForm((f) => ({ ...f, force_scenario: e.target.value }))}
                      className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-violet-500/50"
                    >
                      <option value="">None</option>
                      <option value="sla_breach">SLA Breach</option>
                      <option value="escalation">Escalation</option>
                      <option value="high_retry">High Retry</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Inject Delay Node</label>
                  <input
                    type="text"
                    placeholder="e.g. CORRESPONDENT_JP"
                    value={form.inject_delay_node}
                    onChange={(e) => setForm((f) => ({ ...f, inject_delay_node: e.target.value }))}
                    className="w-full bg-[#0c1629] border border-violet-500/20 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-violet-500/50"
                  />
                </div>
              </div>
            )}

            <button
              onClick={handleSimulate}
              disabled={simulating}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:opacity-60 rounded-lg text-sm font-medium text-white transition"
            >
              {simulating ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Simulating...</>
              ) : (
                <><Play className="w-4 h-4" /> Run Simulation</>
              )}
            </button>
          </div>
        </Panel>

        {/* Replay form */}
        <Panel>
          <div className="flex items-center justify-between mb-5">
            <SectionHeader title="Replay Existing Payment" icon={RotateCcw} />
            <button
              onClick={() => setAdvancedReplayMode(!advancedReplayMode)}
              className={clsx(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition",
                advancedReplayMode
                  ? "bg-violet-500/20 border-violet-500/50 text-violet-300"
                  : "bg-white/5 border-white/10 text-slate-400 hover:text-slate-200"
              )}
            >
              <GitCompare className="w-3 h-3" />
              Compare Mode
            </button>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            {advancedReplayMode
              ? "Compare Mode: re-simulates the payment and generates a side-by-side comparison of outcomes, timings, and anomaly delta."
              : "Enter a Payment ID to re-simulate its exact scenario with the same seed parameters and failure injections."}
          </p>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Payment ID</label>
              <input
                type="text"
                placeholder="e.g. pay_abc123..."
                value={replayId}
                onChange={(e) => setReplayId(e.target.value)}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50 font-mono"
              />
            </div>
            <button
              onClick={handleReplay}
              disabled={replaying || !replayId.trim()}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:bg-violet-900 disabled:opacity-60 rounded-lg text-sm font-medium text-white transition"
            >
              {replaying ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Replaying...</>
              ) : (
                <><RotateCcw className="w-4 h-4" /> Replay Payment</>
              )}
            </button>
          </div>

          {/* Scenario guides */}
          <div className="mt-6 pt-5 border-t border-white/10">
            <p className="text-xs font-medium text-slate-400 mb-3">Failure Scenario Guide</p>
            <div className="space-y-2">
              {[
                { scenario: "Sanctions screen hold", description: "Inject SANCTIONS_FALSE_POSITIVE to simulate a compliance hold requiring manual review" },
                { scenario: "Multi-hop route failure", description: "Use US→IN corridor with MISSING_INTERMEDIARY for correspondent bank failure" },
                { scenario: "FX liquidity crunch", description: "Inject FX_DELAY on SEPA corridor to simulate rate lock timeout" },
                { scenario: "Settlement break", description: "Inject RECONCILIATION_MISMATCH to trigger recon investigation workflow" },
              ].map(({ scenario, description }) => (
                <div key={scenario} className="rounded-lg bg-white/4 border border-white/8 px-3 py-2">
                  <p className="text-xs font-medium text-slate-300">{scenario}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </Panel>
      </div>

      {/* Error display */}
      {error && (
        <div className="px-4 py-3 bg-red-900/20 border border-red-700/40 rounded-xl text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Comparison result (advanced replay) */}
      {comparison && (
        <Panel>
          <div className="flex items-center justify-between mb-5">
            <SectionHeader title="Replay Comparison" icon={GitCompare} subtitle={comparison.outcome_summary} />
            <div className="flex items-center gap-2">
              {comparison.status_changed && <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/20">Status Changed</span>}
              {comparison.anomaly_changed && <span className="text-[10px] px-2 py-0.5 rounded bg-red-500/15 text-red-400 border border-red-500/20">Anomaly Changed</span>}
              {comparison.path_changed && <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/20">Path Changed</span>}
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {[{ label: "Original", payment: comparison.original, anomaly: comparison.original_anomaly, obs: comparison.original_observability },
              { label: "Replayed", payment: comparison.replayed, anomaly: comparison.replayed_anomaly, obs: comparison.replayed_observability }]
              .map(({ label, payment, anomaly, obs }) => (
                <div key={label} className="space-y-3">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">{label}</p>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { k: "Reference", v: payment.payment_reference },
                      { k: "Status", v: payment.current_status },
                      { k: "Stage", v: payment.current_stage },
                      { k: "Proc. Time", v: obs.total_processing_seconds != null ? formatDuration(obs.total_processing_seconds) : "—" },
                    ].map(({ k, v }) => (
                      <div key={k} className="bg-white/5 rounded-lg px-3 py-2">
                        <p className="text-[10px] text-slate-400">{k}</p>
                        <p className="text-xs font-semibold text-white font-mono">{v}</p>
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <StageBadge stage={payment.current_stage} />
                    <StatusBadge status={payment.current_status} />
                    <SLABadge breach={obs.sla_breach} recovered={obs.recovered} />
                    {anomaly && <><AnomalyTypeBadge type={anomaly.type} /><SeverityBadge severity={anomaly.severity} /></>}
                  </div>
                  {anomaly && (
                    <div className="px-3 py-2 bg-amber-900/15 border border-amber-700/30 rounded-lg">
                      <p className="text-xs font-semibold text-amber-300">{anomaly.title}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{anomaly.description}</p>
                    </div>
                  )}
                </div>
              ))}
          </div>
          {comparison.timing_delta_seconds != null && (
            <div className="mt-4 pt-4 border-t border-white/10 flex items-center gap-2">
              <span className="text-xs text-slate-400">Timing delta:</span>
              <span className={clsx("text-xs font-bold", comparison.timing_delta_seconds > 0 ? "text-amber-400" : "text-emerald-400")}>
                {comparison.timing_delta_seconds > 0 ? "+" : ""}{formatDuration(Math.abs(comparison.timing_delta_seconds))}
              </span>
              <button onClick={() => router.push(`/payments/${comparison.replayed_payment_id}`)} className="ml-auto text-xs text-blue-400 hover:text-blue-300">
                View replayed payment →
              </button>
            </div>
          )}
        </Panel>
      )}

      {/* Simulation result */}
      {result && (
        <Panel>
          <SectionHeader title="Simulation Result" icon={Activity} className="mb-5" />
          <div className="space-y-5">
            {/* Summary */}
            <div className="px-4 py-3 bg-white/5 rounded-xl border border-white/10">
              <p className="text-sm text-slate-200">{result.summary}</p>
            </div>

            {/* Payment overview */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: "Reference", value: result.payment.payment_reference },
                { label: "Amount", value: formatCurrency(result.payment.amount, result.payment.source_currency) },
                { label: "Route", value: `${result.payment.source_country} → ${result.payment.destination_country}` },
                { label: "Type", value: result.payment.payment_type },
              ].map(({ label, value }) => (
                <div key={label} className="bg-white/5 rounded-lg px-3 py-2">
                  <p className="text-[10px] text-slate-400">{label}</p>
                  <p className="text-sm font-semibold text-white mt-0.5 font-mono">{value}</p>
                </div>
              ))}
            </div>

            {/* Status badges */}
            <div className="flex items-center gap-2 flex-wrap">
              <StageBadge stage={result.payment.current_stage} />
              <StatusBadge status={result.payment.current_status} />
              {result.anomaly && (
                <>
                  <AnomalyTypeBadge type={result.anomaly.type} />
                  <SeverityBadge severity={result.anomaly.severity} />
                </>
              )}
            </div>

            {/* Anomaly details */}
            {result.anomaly && (
              <div className="border border-amber-700/30 bg-amber-900/10 rounded-xl px-4 py-3">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-amber-300">{result.anomaly.title}</p>
                    <p className="text-xs text-slate-400 mt-1">{result.anomaly.description}</p>
                    {result.anomaly.recommended_action && (
                      <p className="text-xs text-blue-300 mt-2">
                        → {result.anomaly.recommended_action}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Event stream */}
            <div>
              <p className="text-xs font-medium text-slate-400 mb-2">
                Event Stream ({result.events.length} events)
              </p>
              <div className="space-y-1 max-h-64 overflow-y-auto">
                {result.events.map((event, i) => (
                  <div key={i} className="flex items-start gap-2.5 py-1.5 px-3 rounded-lg hover:bg-white/4">
                    <span className={clsx(
                      "w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0",
                      event.status === "COMPLETED" ? "bg-emerald-500" :
                      event.status === "FAILED" ? "bg-red-500" :
                      event.status === "ON_HOLD" ? "bg-yellow-500" : "bg-blue-500"
                    )} />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs text-slate-300">{event.message}</span>
                    </div>
                    <StageBadge stage={event.stage} />
                    <span className="text-[10px] text-slate-600 flex-shrink-0">{formatDate(event.timestamp)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Scenario Analysis */}
            {aiLoading && (
              <div className="flex items-center gap-2 py-3 px-4 bg-violet-900/10 border border-violet-700/25 rounded-xl">
                <Brain className="w-4 h-4 text-violet-400 animate-pulse" />
                <span className="text-xs text-slate-400">Running AI scenario analysis...</span>
              </div>
            )}

            {aiPackage && (
              <div className="rounded-xl border border-violet-700/30 bg-violet-900/8 overflow-hidden">
                <div className="px-4 py-3 border-b border-white/8 flex items-center gap-2">
                  <Brain className="w-3.5 h-3.5 text-violet-400" />
                  <span className="text-xs font-semibold text-violet-300">AI Scenario Analysis</span>
                  <span className="text-[10px] text-slate-500 ml-auto">Confidence: {(aiPackage.rca.confidence_score * 100).toFixed(0)}%</span>
                </div>
                <div className="px-4 py-3 space-y-3">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase mb-1">AI Summary</p>
                    <p className="text-xs text-slate-200">{aiPackage.ai_summary.what_went_wrong}</p>
                    <p className="text-xs text-blue-400/80 mt-1 italic">→ {aiPackage.ai_summary.what_to_do}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase mb-1">Root Cause</p>
                    <p className="text-xs text-slate-300">{aiPackage.rca.likely_root_cause}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {aiPackage.rca.contributing_factors.slice(0, 3).map((f, i) => (
                        <span key={i} className="text-[9px] px-2 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">{f}</span>
                      ))}
                    </div>
                  </div>
                  {aiPackage.recommendations.length > 0 && (
                    <div>
                      <p className="text-[10px] font-semibold text-slate-400 uppercase mb-1">Top Recommendation</p>
                      <p className="text-xs text-slate-300">{aiPackage.recommendations[0].title}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">{aiPackage.recommendations[0].rationale}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Navigate to detail */}
            <button
              onClick={() => router.push(`/payments/${result.payment.id}`)}
              className="flex items-center gap-2 px-4 py-2 bg-white/8 hover:bg-white/12 border border-white/15 rounded-lg text-sm text-slate-200 transition"
            >
              View Full Payment Detail <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </Panel>
      )}
    </div>
  );
}

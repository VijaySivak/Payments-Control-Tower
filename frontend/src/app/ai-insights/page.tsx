"use client";
import { useRouter } from "next/navigation";
import { useApi } from "@/hooks/useApi";
import { controlTowerApi, aiApi } from "@/lib/api/payments";
import { Panel } from "@/components/shared/Panel";
import { SectionHeader } from "@/components/shared/SectionHeader";
import { MetricCard } from "@/components/shared/MetricCard";
import { NodeHealthBadge } from "@/components/shared/NodeHealthBadge";
import type { NodeHealthStatus } from "@/lib/types";
import {
  BrainCircuit, Zap, Shield,
  Cpu, GitBranch, ChevronRight, Activity,
  Timer, MapPin, Brain, Target, RefreshCw,
} from "lucide-react";
import { clsx } from "clsx";

const STATUS_STYLE: Record<string, string> = {
  DEGRADED: "bg-red-900/20 border-red-700/30 text-red-400",
  ELEVATED: "bg-amber-900/15 border-amber-700/25 text-amber-400",
  NORMAL: "bg-emerald-900/10 border-emerald-700/20 text-emerald-400",
};

export default function AIInsightsPage() {
  const router = useRouter();

  // Legacy Phase 2 data
  const { data: overview } = useApi(controlTowerApi.overview, []);
  const { data: exceptionPatterns } = useApi(controlTowerApi.exceptionPatterns, []);
  const { data: delayHotspots } = useApi(controlTowerApi.delayHotspots, []);
  const { data: nodeHealth } = useApi(controlTowerApi.nodeHealth, []);

  // Phase 3 AI data
  const { data: operatorSummary } = useApi(aiApi.operatorSummary, []);
  const { data: priorityQueue } = useApi(() => aiApi.priorityQueue(12), []);
  const { data: systemInsights } = useApi(aiApi.systemAnomalyInsights, []);
  const { data: corridorRisks } = useApi(aiApi.corridorRiskInsights, []);
  const { data: nodeWatchlist } = useApi(aiApi.nodeRiskWatchlist, []);

  const degradedNodes = nodeHealth?.filter((n) => n.health_status !== "HEALTHY") ?? [];
  const typeFreqData = exceptionPatterns?.type_frequencies.slice(0, 6).map((t) => ({
    name: t.type.replace(/_/g, " ").substring(0, 18),
    count: t.count,
  })) ?? [];

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/20 to-violet-600/20 border border-violet-500/30">
          <Brain className="w-6 h-6 text-violet-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white">AI Operations Console</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Explainable AI — RCA · Recommendations · Corridor Risk · Priority Triage
          </p>
        </div>
        <div className="ml-auto px-3 py-1 rounded-full bg-violet-900/30 border border-violet-700/40 text-xs text-violet-300 font-medium">
          Phase 3 Live
        </div>
      </div>

      {/* Operator AI Summary Banner */}
      {operatorSummary && (
        <div className={clsx(
          "rounded-xl border px-5 py-4 space-y-3",
          operatorSummary.system_status === "DEGRADED" ? "border-red-700/40 bg-red-900/10" :
          operatorSummary.system_status === "ELEVATED" ? "border-amber-700/35 bg-amber-900/8" :
          "border-emerald-700/30 bg-emerald-900/8"
        )}>
          <div className="flex items-start gap-3">
            <Brain className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1.5">
                <span className="text-[10px] font-bold text-violet-400 uppercase tracking-wide">AI Operator Summary</span>
                <span className={clsx(
                  "text-[10px] font-bold px-2 py-0.5 rounded border uppercase",
                  STATUS_STYLE[operatorSummary.system_status] ?? STATUS_STYLE.NORMAL
                )}>
                  {operatorSummary.system_status}
                </span>
                <span className="text-[10px] text-slate-500 ml-auto">Confidence: {(operatorSummary.ai_confidence * 100).toFixed(0)}%</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed">{operatorSummary.headline}</p>
            </div>
          </div>
          {(operatorSummary.key_alerts.length > 0 || operatorSummary.recommended_actions.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3 border-t border-white/8">
              <div>
                <p className="text-[10px] font-semibold text-red-400 uppercase mb-1.5">Key Alerts</p>
                <ul className="space-y-1">
                  {operatorSummary.key_alerts.slice(0, 3).map((a, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5"><span className="w-1 h-1 rounded-full bg-red-500 mt-1.5 flex-shrink-0" />{a}</li>
                  ))}
                  {operatorSummary.key_alerts.length === 0 && <li className="text-xs text-slate-500 italic">No active alerts</li>}
                </ul>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-amber-400 uppercase mb-1.5">Recommended Actions</p>
                <ul className="space-y-1">
                  {operatorSummary.recommended_actions.slice(0, 3).map((a, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5"><span className="w-1 h-1 rounded-full bg-amber-500 mt-1.5 flex-shrink-0" />{a}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-[10px] font-semibold text-emerald-400 uppercase mb-1.5">Positive Signals</p>
                <ul className="space-y-1">
                  {operatorSummary.positive_signals.slice(0, 3).map((s, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5"><span className="w-1 h-1 rounded-full bg-emerald-500 mt-1.5 flex-shrink-0" />{s}</li>
                  ))}
                  {operatorSummary.positive_signals.length === 0 && <li className="text-xs text-slate-500 italic">Monitoring</li>}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
        <MetricCard label="Priority Queue" value={priorityQueue?.length ?? "—"} icon={Target} variant="warning" subValue="Needs attention" />
        <MetricCard label="Critical Signals" value={systemInsights?.filter(i => i.severity === "CRITICAL" || i.severity === "HIGH").length ?? "—"} icon={Zap} variant="critical" />
        <MetricCard label="SLA Breaches" value={overview?.sla_breach_count ?? "—"} icon={Timer} variant={overview && overview.sla_breach_count > 5 ? "critical" : "warning"} />
        <MetricCard label="At-Risk Nodes" value={nodeWatchlist?.length ?? degradedNodes.length} icon={Cpu} variant={nodeWatchlist && nodeWatchlist.length > 0 ? "critical" : "success"} />
        <MetricCard label="Corridors" value={corridorRisks?.length ?? "—"} icon={Activity} subValue="Monitored" />
        <MetricCard label="Success Rate" value={overview ? `${overview.success_rate}%` : "—"} icon={Shield} variant="success" />
      </div>

      {/* Priority Queue + System Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Panel noPad>
          <div className="px-5 py-3 border-b border-white/10 flex items-center justify-between">
            <SectionHeader title="Operator Priority Queue" icon={Target} subtitle="Most urgent payments requiring attention" />
            <button onClick={() => router.push("/payments")} className="text-xs text-blue-400 hover:text-blue-300">View all →</button>
          </div>
          <div className="divide-y divide-white/5 max-h-80 overflow-y-auto">
            {priorityQueue?.slice(0, 10).map((item) => (
              <div key={item.payment_id} onClick={() => router.push(`/payments/${item.payment_id}`)}
                className="px-5 py-3 flex items-start gap-3 hover:bg-white/4 cursor-pointer group transition">
                <span className={clsx("w-2 h-2 rounded-full mt-1.5 flex-shrink-0",
                  item.urgency === "CRITICAL" ? "bg-red-500" : item.urgency === "HIGH" ? "bg-amber-500" : "bg-yellow-400")} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-mono text-slate-300">{item.payment_reference}</span>
                    {item.sla_breach && <span className="text-[9px] px-1 py-0.5 rounded bg-red-900/20 text-red-400 border border-red-700/25">SLA</span>}
                    <span className="ml-auto text-[10px] font-bold text-slate-400">{item.priority_score.toFixed(0)}</span>
                  </div>
                  <p className="text-[10px] text-slate-500 truncate">{item.reason}</p>
                  <p className="text-[10px] text-blue-400/80 mt-0.5 truncate italic">→ {item.recommended_action}</p>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400 mt-1" />
              </div>
            ))}
            {!priorityQueue?.length && <div className="px-5 py-8 text-center text-sm text-slate-500">No priority items at this time</div>}
          </div>
        </Panel>

        <Panel noPad>
          <div className="px-5 py-3 border-b border-white/10">
            <SectionHeader title="System Anomaly Intelligence" icon={BrainCircuit} subtitle="AI-grouped exception patterns" />
          </div>
          <div className="divide-y divide-white/5 max-h-80 overflow-y-auto">
            {systemInsights?.map((insight) => (
              <div key={insight.insight_id} className="px-5 py-3">
                <div className="flex items-start gap-2 mb-1">
                  <span className={clsx("text-[10px] font-bold mt-0.5",
                    insight.severity === "CRITICAL" ? "text-red-400" : insight.severity === "HIGH" ? "text-amber-400" : "text-yellow-400"
                  )}>● {insight.severity}</span>
                  <p className="text-xs font-semibold text-white flex-1">{insight.title}</p>
                  <span className="text-[10px] text-slate-500">{(insight.confidence * 100).toFixed(0)}%</span>
                </div>
                <p className="text-[10px] text-slate-400 mb-1">{insight.description}</p>
                <p className="text-[10px] text-blue-400/80 italic">→ {insight.recommended_action}</p>
              </div>
            ))}
            {!systemInsights?.length && <div className="px-5 py-8 text-center text-sm text-slate-500">No system insights available</div>}
          </div>
        </Panel>
      </div>

      {/* Corridor Risk + Node Watchlist */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Panel noPad>
          <div className="px-5 py-3 border-b border-white/10">
            <SectionHeader title="Corridor Risk Intelligence" icon={GitBranch} subtitle="AI-ranked corridors by operational risk" />
          </div>
          <div className="divide-y divide-white/5 max-h-72 overflow-y-auto">
            {corridorRisks?.map((cr) => (
              <div key={cr.corridor} className="px-5 py-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono font-semibold text-white">{cr.corridor}</span>
                  <span className={clsx("text-[10px] font-bold ml-auto",
                    cr.risk_level === "CRITICAL" ? "text-red-400" : cr.risk_level === "HIGH" ? "text-amber-400" : cr.risk_level === "MEDIUM" ? "text-yellow-400" : "text-emerald-400")}>
                    {cr.risk_level}
                  </span>
                  <span className="text-[10px] font-bold text-slate-400">{cr.risk_score.toFixed(0)}/100</span>
                </div>
                <div className="w-full bg-white/8 rounded-full h-1 mb-1.5">
                  <div className={clsx("h-1 rounded-full",
                    cr.risk_level === "CRITICAL" ? "bg-red-500" : cr.risk_level === "HIGH" ? "bg-amber-500" : cr.risk_level === "MEDIUM" ? "bg-yellow-400" : "bg-emerald-400"
                  )} style={{ width: `${Math.min(cr.risk_score, 100)}%` }} />
                </div>
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-[10px] text-slate-500">{cr.primary_issue}</span>
                  <span className="text-[10px] text-slate-600 ml-auto">{cr.anomaly_count} anomalies · {cr.sla_breach_count} SLA</span>
                </div>
                <p className="text-[10px] text-blue-400/80 mt-0.5 italic">→ {cr.recommended_action}</p>
              </div>
            ))}
            {!corridorRisks?.length && <div className="px-5 py-8 text-center text-sm text-slate-500">No corridor risk data</div>}
          </div>
        </Panel>

        <Panel noPad>
          <div className="px-5 py-3 border-b border-white/10">
            <SectionHeader title="Node Risk Watchlist" icon={Cpu} subtitle="At-risk intermediary nodes" />
          </div>
          <div className="divide-y divide-white/5 max-h-72 overflow-y-auto">
            {nodeWatchlist?.map((node) => (
              <div key={node.node_id} className="px-5 py-3">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-white">{node.bank_name}</span>
                      <NodeHealthBadge status={node.health_status as NodeHealthStatus} />
                    </div>
                    <span className="text-[10px] text-slate-500">{node.country} · {node.node_type}</span>
                  </div>
                  <div className="text-right">
                    <span className={clsx("text-sm font-bold",
                      node.risk_score >= 40 ? "text-red-400" : node.risk_score >= 20 ? "text-amber-400" : "text-yellow-400")}>
                      {node.risk_score.toFixed(0)}
                    </span>
                    <p className="text-[10px] text-slate-500">risk score</p>
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 mb-0.5">{node.risk_reason}</p>
                <div className="flex gap-3 text-[10px] text-slate-500">
                  <span>{node.avg_latency_ms.toFixed(0)}ms</span>
                  <span>{node.anomaly_count} anomalies</span>
                  <span>{node.delay_count} delays</span>
                </div>
              </div>
            ))}
            {!nodeWatchlist?.length && <div className="px-5 py-8 text-center text-sm text-slate-500">All nodes within normal parameters</div>}
          </div>
        </Panel>
      </div>

      {/* Delay Hotspots */}
      {delayHotspots && (
        <Panel noPad>
          <div className="px-5 py-3 border-b border-white/10">
            <SectionHeader title="Delay Hotspots" icon={MapPin} subtitle="Top countries, corridors, and stage bottlenecks" />
          </div>
          <div className="px-5 py-4 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-[10px] font-semibold text-slate-500 uppercase mb-2">Top Countries by Delay</p>
              <div className="space-y-1.5">
                {delayHotspots.ranked_countries.slice(0, 6).map((c, i) => (
                  <div key={c.country} className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-600 w-3">{i + 1}</span>
                    <span className="text-xs text-slate-300 w-8 font-mono">{c.country}</span>
                    <div className="flex-1 bg-white/8 rounded-full h-1">
                      <div className="h-1 rounded-full bg-amber-500/70" style={{ width: `${(c.delay_count / Math.max(delayHotspots.ranked_countries[0]?.delay_count ?? 1, 1)) * 100}%` }} />
                    </div>
                    <span className="text-[10px] text-amber-400 tabular-nums w-4">{c.delay_count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-slate-500 uppercase mb-2">Top Corridors</p>
              <div className="space-y-1.5">
                {delayHotspots.ranked_corridors.slice(0, 6).map((c) => (
                  <div key={c.corridor} className="flex items-center justify-between gap-2">
                    <span className="text-xs font-mono text-slate-300">{c.corridor}</span>
                    <span className="text-[10px] text-amber-400">{c.delay_count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-slate-500 uppercase mb-2">Stage Bottlenecks</p>
              <div className="flex flex-wrap gap-2">
                {delayHotspots.stage_hotspots.slice(0, 8).map((s) => (
                  <div key={s.stage} className="flex items-center gap-1.5 px-2 py-1 bg-white/5 rounded-lg border border-white/8">
                    <span className="text-[10px] font-mono text-slate-300">{s.stage}</span>
                    <span className="text-[9px] text-amber-400 font-bold">{s.bottleneck_count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Panel>
      )}

      {/* Recurring signatures */}
      {exceptionPatterns && exceptionPatterns.recurring_signatures.length > 0 && (
        <Panel noPad>
          <div className="px-5 py-3 border-b border-white/10">
            <SectionHeader title="Recurring Exception Signatures" icon={RefreshCw} subtitle="Patterns seen more than once — prime candidates for automation" />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/8">
                  {["Type", "Code", "Stage", "Corridor", "Severity", "Recurrences"].map((h) => (
                    <th key={h} className="text-left px-5 py-2 text-[10px] font-medium text-slate-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {exceptionPatterns.recurring_signatures.map((sig, i) => (
                  <tr key={i} className="hover:bg-white/4 transition">
                    <td className="px-5 py-2 text-slate-300">{sig.type.replace(/_/g, " ")}</td>
                    <td className="px-5 py-2 font-mono text-slate-500">{sig.code ?? "—"}</td>
                    <td className="px-5 py-2 text-slate-400">{sig.stage}</td>
                    <td className="px-5 py-2 font-mono text-slate-400">{sig.corridor ?? "—"}</td>
                    <td className="px-5 py-2">
                      <span className={`text-[10px] font-semibold ${sig.severity === "CRITICAL" || sig.severity === "HIGH" ? "text-red-400" : sig.severity === "MEDIUM" ? "text-amber-400" : "text-slate-400"}`}>
                        {sig.severity}
                      </span>
                    </td>
                    <td className="px-5 py-2 text-amber-400 font-semibold">{sig.recurrence_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* Recurring Exception Signatures table closes above */}
    </div>
  );
}

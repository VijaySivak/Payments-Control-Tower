"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useApi } from "@/hooks/useApi";
import { controlTowerApi, aiApi } from "@/lib/api/payments";
import { SeverityBadge, AnomalyTypeBadge, StageBadge, AnomalyStatusBadge } from "@/components/shared/Badge";
import { Panel } from "@/components/shared/Panel";
import { SectionHeader } from "@/components/shared/SectionHeader";
import { MetricCard } from "@/components/shared/MetricCard";
import { PageLoader } from "@/components/shared/LoadingSkeleton";
import { EmptyState, ErrorState } from "@/components/shared/EmptyState";
import { formatDate, formatRelativeTime, anomalyTypeLabel } from "@/lib/formatters";
import { SEVERITY_DOT, CHART_COLORS } from "@/lib/constants";
import type { AnomalySeverity, AnomalyType, AnomalyStatus } from "@/lib/types";
import { AlertTriangle, Shield, Zap, SlidersHorizontal, X, ChevronRight, TrendingUp, Brain } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { clsx } from "clsx";
import { ActionStatusBadge } from "@/components/shared/ActionStatusBadge";
import type { ActionStatus } from "@/lib/types";

const SEVERITIES: AnomalySeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const ANOMALY_TYPES: AnomalyType[] = [
  "SANCTIONS_FALSE_POSITIVE", "GATEWAY_TIMEOUT", "VALIDATION_ERROR",
  "FX_DELAY", "MISSING_INTERMEDIARY", "SETTLEMENT_DELAY", "RECONCILIATION_MISMATCH",
];
const STATUSES: AnomalyStatus[] = ["OPEN", "INVESTIGATING", "RESOLVED"];
const ACTION_STATUSES: ActionStatus[] = ["OPEN", "TRIAGED", "IN_PROGRESS", "MITIGATED", "RESOLVED"];

export default function AnomaliesPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<{
    severity?: string;
    anomaly_type?: string;
    status?: string;
    stage?: string;
    country?: string;
    corridor?: string;
    node?: string;
    action_status?: string;
  }>({});
  const [showFilters, setShowFilters] = useState(false);

  const { data: anomalies, loading, error, refetch } = useApi(
    () => controlTowerApi.anomalies(filters),
    [JSON.stringify(filters)]
  );
  const { data: systemInsights } = useApi(aiApi.systemAnomalyInsights, []);

  const severityCounts = anomalies
    ? SEVERITIES.reduce((acc, s) => ({ ...acc, [s]: anomalies.filter((a) => a.severity === s).length }), {} as Record<string, number>)
    : {};

  const typeData = anomalies
    ? ANOMALY_TYPES.map((t) => ({
        name: anomalyTypeLabel(t),
        count: anomalies.filter((a) => a.type === t).length,
      })).filter((d) => d.count > 0)
    : [];

  const openCount = anomalies?.filter((a) => a.status === "OPEN").length ?? 0;
  const investigatingCount = anomalies?.filter((a) => a.status === "INVESTIGATING").length ?? 0;
  const criticalCount = anomalies?.filter((a) => a.severity === "CRITICAL").length ?? 0;
  const escalatedCount = anomalies?.filter((a) => a.operational_impact_score != null && a.operational_impact_score >= 7).length ?? 0;
  const recurringCount = anomalies?.filter((a) => a.recurrence_count > 0).length ?? 0;

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="max-w-screen-2xl mx-auto px-6 py-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Anomalies</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {anomalies ? `${anomalies.length} anomalies detected` : "Loading..."}
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/15 rounded-lg text-sm text-slate-300 transition"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      {/* AI System Insights Banner */}
      {systemInsights && systemInsights.length > 0 && (
        <div className="rounded-xl border border-violet-700/30 bg-violet-900/8 px-5 py-3">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-3.5 h-3.5 text-violet-400" />
            <span className="text-[10px] font-bold text-violet-400 uppercase tracking-wide">AI Triage Intelligence</span>
            <button onClick={() => router.push("/ai-insights")} className="ml-auto text-[10px] text-blue-400 hover:text-blue-300">Full console →</button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {systemInsights.slice(0, 3).map((insight) => (
              <div key={insight.insight_id} className="flex items-start gap-2 bg-white/3 rounded-lg px-3 py-2">
                <span className={clsx("text-[9px] font-bold mt-0.5 flex-shrink-0",
                  insight.severity === "CRITICAL" ? "text-red-400" : insight.severity === "HIGH" ? "text-amber-400" : "text-yellow-400"
                )}>●</span>
                <div className="min-w-0">
                  <p className="text-[10px] font-semibold text-slate-200 truncate">{insight.title}</p>
                  <p className="text-[10px] text-blue-400/80 italic truncate">→ {insight.recommended_action}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard label="Total Anomalies" value={anomalies?.length ?? "—"} icon={AlertTriangle} variant="critical" />
        <MetricCard label="Critical" value={criticalCount} icon={Zap} variant="critical" />
        <MetricCard label="Open" value={openCount} icon={Shield} variant="warning" />
        <MetricCard label="Investigating" value={investigatingCount} icon={Shield} variant="warning" />
        <MetricCard label="High Impact" value={escalatedCount} icon={TrendingUp} variant={escalatedCount > 0 ? "critical" : "default"} />
        <MetricCard label="Recurring" value={recurringCount} icon={AlertTriangle} variant={recurringCount > 2 ? "warning" : "default"} />
      </div>

      {/* Charts + Filters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Severity breakdown */}
        <Panel>
          <SectionHeader title="By Severity" icon={AlertTriangle} className="mb-4" />
          <div className="space-y-2.5">
            {SEVERITIES.map((s) => (
              <div
                key={s}
                className="flex items-center gap-3 cursor-pointer group"
                onClick={() => setFilters((f) => ({ ...f, severity: f.severity === s ? undefined : s }))}
              >
                <span className={clsx("w-2 h-2 rounded-full flex-shrink-0", SEVERITY_DOT[s])} />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className={clsx(
                      "text-xs font-medium",
                      filters.severity === s ? "text-white" : "text-slate-300 group-hover:text-white transition"
                    )}>{s}</span>
                    <span className="text-xs text-slate-400">{severityCounts[s] ?? 0}</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-1">
                    <div
                      className={clsx("h-1 rounded-full transition-all",
                        s === "CRITICAL" ? "bg-red-500" :
                        s === "HIGH" ? "bg-orange-500" :
                        s === "MEDIUM" ? "bg-yellow-500" : "bg-blue-500"
                      )}
                      style={{ width: `${anomalies?.length ? ((severityCounts[s] ?? 0) / anomalies.length) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        {/* Type distribution */}
        <Panel className="md:col-span-2">
          <SectionHeader title="Anomaly Type Distribution" icon={Zap} className="mb-4" />
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={typeData} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={120} />
              <Tooltip
                contentStyle={{ background: "#0c1629", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 11 }}
              />
              <Bar dataKey="count" radius={[0, 3, 3, 0]}>
                {typeData.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      {/* Filter bar */}
      {showFilters && (
        <Panel>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Severity</label>
              <select value={filters.severity ?? ""} onChange={(e) => setFilters((f) => ({ ...f, severity: e.target.value || undefined }))}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="">All</option>
                {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Type</label>
              <select value={filters.anomaly_type ?? ""} onChange={(e) => setFilters((f) => ({ ...f, anomaly_type: e.target.value || undefined }))}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="">All types</option>
                {ANOMALY_TYPES.map((t) => <option key={t} value={t}>{anomalyTypeLabel(t)}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Status</label>
              <select value={filters.status ?? ""} onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value || undefined }))}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="">All statuses</option>
                {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Action Status</label>
              <select value={filters.action_status ?? ""} onChange={(e) => setFilters((f) => ({ ...f, action_status: e.target.value || undefined }))}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="">All actions</option>
                {ACTION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Country</label>
              <input type="text" placeholder="e.g. US" value={filters.country ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, country: e.target.value || undefined }))}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Corridor</label>
              <input type="text" placeholder="e.g. US-GB" value={filters.corridor ?? ""}
                onChange={(e) => setFilters((f) => ({ ...f, corridor: e.target.value.toUpperCase() || undefined }))}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50" />
            </div>
            <div className="flex items-end">
              <button onClick={() => setFilters({})} className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300">
                <X className="w-3 h-3" /> Clear
              </button>
            </div>
          </div>
        </Panel>
      )}

      {/* Anomaly list */}
      {error ? (
        <ErrorState message={error} onRetry={refetch} />
      ) : loading && !anomalies ? (
        <PageLoader />
      ) : anomalies && anomalies.length === 0 ? (
        <EmptyState icon={Shield} title="No anomalies" description="No anomalies match the current filters" />
      ) : (
        <Panel noPad>
          <div className="px-5 py-4 border-b border-white/10">
            <SectionHeader title="Anomaly Registry" subtitle={`${anomalies?.length ?? 0} records`} icon={AlertTriangle} />
          </div>
          <div className="divide-y divide-white/5">
            {anomalies?.map((anomaly) => (
              <div
                key={anomaly.id}
                className="px-5 py-4 hover:bg-white/4 cursor-pointer transition group"
                onClick={() => router.push(`/payments/${anomaly.payment_id}`)}
              >
                <div className="flex items-start gap-4">
                  <div className={clsx("mt-1.5 w-2 h-2 rounded-full flex-shrink-0", SEVERITY_DOT[anomaly.severity])} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-white group-hover:text-blue-200 transition">{anomaly.title}</span>
                      <SeverityBadge severity={anomaly.severity} />
                      <AnomalyTypeBadge type={anomaly.type} />
                      <AnomalyStatusBadge status={anomaly.status} />
                      <ActionStatusBadge status={anomaly.action_status} />
                      <StageBadge stage={anomaly.stage} />
                      {anomaly.anomaly_code && (
                        <span className="text-[9px] font-mono text-slate-500 bg-white/5 px-1 rounded">{anomaly.anomaly_code}</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{anomaly.description}</p>
                    {anomaly.root_symptom && (
                      <p className="text-xs text-slate-500 mt-0.5"><span className="text-slate-400">Symptom:</span> {anomaly.root_symptom}</p>
                    )}
                    {anomaly.probable_cause && (
                      <p className="text-xs text-slate-500 mt-0.5"><span className="text-slate-400">Cause:</span> {anomaly.probable_cause}</p>
                    )}
                    {anomaly.evidence_summary && (
                      <p className="text-xs text-slate-500 mt-1 italic">{anomaly.evidence_summary}</p>
                    )}
                    {anomaly.recommended_action && (
                      <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-1 bg-blue-900/20 border border-blue-700/30 rounded text-xs text-blue-300">
                        <Shield className="w-3 h-3" />
                        {anomaly.recommended_action}
                      </div>
                    )}
                    <div className="flex items-center gap-3 mt-2 flex-wrap">
                      <span className="text-[10px] text-slate-500 font-mono">Payment: {anomaly.payment_id.slice(0, 12)}...</span>
                      {anomaly.country && <span className="text-[10px] text-slate-500">Country: {anomaly.country}</span>}
                      {anomaly.corridor && <span className="text-[10px] text-slate-500">Corridor: {anomaly.corridor}</span>}
                      {anomaly.impacted_node && <span className="text-[10px] text-slate-500">Node: {anomaly.impacted_node}</span>}
                      {anomaly.intermediary_bank && <span className="text-[10px] text-slate-500">Bank: {anomaly.intermediary_bank}</span>}
                      {anomaly.operational_impact_score != null && (
                        <span className={`text-[10px] font-semibold ${anomaly.operational_impact_score >= 7 ? 'text-red-400' : anomaly.operational_impact_score >= 4 ? 'text-amber-400' : 'text-slate-500'}`}>
                          Impact: {anomaly.operational_impact_score.toFixed(1)}/10
                        </span>
                      )}
                      {anomaly.recurrence_count > 0 && (
                        <span className="text-[10px] text-amber-400">Recurred {anomaly.recurrence_count}x</span>
                      )}
                      {anomaly.client_impact_level && (
                        <span className="text-[10px] text-slate-500">Client: {anomaly.client_impact_level}</span>
                      )}
                      {anomaly.resolution_eta_minutes != null && (
                        <span className="text-[10px] text-slate-500">ETA: {anomaly.resolution_eta_minutes}m</span>
                      )}
                      <span className="text-[10px] text-slate-500">{formatRelativeTime(anomaly.detected_at)}</span>
                    </div>
                  </div>
                  <div className="flex-shrink-0 flex flex-col items-end gap-1">
                    {anomaly.confidence !== undefined && (
                      <span className="text-xs text-slate-400">
                        <span className="text-white font-semibold">{(anomaly.confidence * 100).toFixed(0)}%</span> confidence
                      </span>
                    )}
                    <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 transition" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

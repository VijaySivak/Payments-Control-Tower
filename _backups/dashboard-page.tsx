"use client";
import { useRouter } from "next/navigation";
import { useApi } from "@/hooks/useApi";
import { controlTowerApi, aiApi } from "@/lib/api/payments";
import { MetricCard } from "@/components/shared/MetricCard";
import { SectionHeader } from "@/components/shared/SectionHeader";
import { Panel } from "@/components/shared/Panel";
import { PageLoader } from "@/components/shared/LoadingSkeleton";
import { ErrorState } from "@/components/shared/EmptyState";
import { StatusBadge, StageBadge, SeverityBadge } from "@/components/shared/Badge";
import { SLABadge } from "@/components/shared/SLABadge";
import dynamic from "next/dynamic";
import { formatAmount, formatCurrency, formatRelativeTime, stageLabel } from "@/lib/formatters";
import { CHART_COLORS, SEVERITY_DOT, STAGE_BG } from "@/lib/constants";
import {
  Activity, AlertTriangle, CheckCircle2, Clock, Globe,
  TrendingUp, XCircle, Zap, BarChart3, Shield, Timer,
  RefreshCw, ChevronRight, Brain, Target,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, RadialBarChart, RadialBar,
} from "recharts";

const PaymentFlowMap = dynamic(
  () => import("@/components/map/PaymentFlowMap").then((m) => ({ default: m.PaymentFlowMap })),
  {
    ssr: false,
    loading: () => (
      <div className="h-80 flex items-center justify-center">
        <div className="text-slate-500 text-sm">Loading map...</div>
      </div>
    ),
  },
);

export default function DashboardPage() {
  const router = useRouter();
  const { data: overview, loading: ovLoading, error: ovError, refetch: ovRefetch } = useApi(controlTowerApi.overview, []);
  const { data: health, loading: hlLoading } = useApi(controlTowerApi.systemHealth, []);
  const { data: livePayments, loading: liveLoading } = useApi(() => controlTowerApi.livePayments(15), []);
  const { data: mapFlows, loading: mapLoading, error: mapError, refetch: mapRefetch } = useApi(controlTowerApi.mapFlows, []);
  const { data: stageMetrics } = useApi(controlTowerApi.stageMetrics, []);
  const { data: operatorSummary } = useApi(aiApi.operatorSummary, []);
  const { data: priorityQueue } = useApi(() => aiApi.priorityQueue(8), []);

  if (ovLoading && !overview) return <PageLoader />;
  if (ovError && !overview) return (
    <div className="max-w-screen-2xl mx-auto px-6 py-8">
      <ErrorState message={ovError} onRetry={ovRefetch} />
    </div>
  );

  const stageData = overview
    ? Object.entries(overview.stage_distribution).map(([stage, count]) => ({
        name: stageLabel(stage as any),
        value: count,
      }))
    : [];

  const anomalyData = overview
    ? overview.top_anomaly_types.slice(0, 6).map(({ type, count }) => ({
        name: type.replace(/_/g, " "),
        count,
      }))
    : [];

  const corridorData = overview
    ? Object.entries(overview.corridor_distribution)
        .slice(0, 8)
        .map(([corridor, count]) => ({ corridor, count }))
    : [];

  return (
    <div className="max-w-screen-2xl mx-auto px-6 py-6 space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Control Tower</h1>
          <p className="text-sm text-slate-400 mt-0.5">Cross-border payments operations overview</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          Live data
        </div>
      </div>

      {/* KPI Row */}
      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          <MetricCard
            label="Total Payments"
            value={overview.total_payments.toLocaleString()}
            icon={Activity}
            onClick={() => router.push("/payments")}
          />
          <MetricCard
            label="In Progress"
            value={overview.in_progress}
            icon={Clock}
            variant="default"
            onClick={() => router.push("/payments?status=IN_PROGRESS")}
          />
          <MetricCard
            label="Completed"
            value={overview.completed}
            icon={CheckCircle2}
            variant="success"
            onClick={() => router.push("/payments?status=COMPLETED")}
          />
          <MetricCard
            label="Failed"
            value={overview.failed}
            icon={XCircle}
            variant="critical"
            onClick={() => router.push("/payments?status=FAILED")}
          />
          <MetricCard
            label="On Hold"
            value={overview.on_hold}
            icon={AlertTriangle}
            variant="warning"
            onClick={() => router.push("/payments?status=ON_HOLD")}
          />
          <MetricCard
            label="Anomalies"
            value={overview.anomaly_count}
            subValue={`${overview.severe_anomaly_count} severe`}
            icon={Zap}
            variant="critical"
            onClick={() => router.push("/anomalies")}
          />
          <MetricCard
            label="SLA Breaches"
            value={overview.sla_breach_count}
            subValue={`${overview.anomaly_rate}% anomaly rate`}
            icon={Timer}
            variant={overview.sla_breach_count > 5 ? "critical" : "warning"}
            onClick={() => router.push("/payments?sla_breach=true")}
          />
          <MetricCard
            label="Throughput/hr"
            value={`${overview.throughput_per_hour.toFixed(1)}`}
            subValue={`${overview.success_rate}% success`}
            icon={TrendingUp}
            variant="success"
          />
        </div>
      )}

      {/* AI Operator Intelligence Row */}
      {(operatorSummary || priorityQueue) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Operator Summary */}
          {operatorSummary && (
            <div className={`lg:col-span-2 rounded-xl border px-5 py-4 ${
              operatorSummary.system_status === "DEGRADED" ? "border-red-700/35 bg-red-900/8" :
              operatorSummary.system_status === "ELEVATED" ? "border-amber-700/30 bg-amber-900/6" :
              "border-emerald-700/25 bg-emerald-900/6"
            }`}>
              <div className="flex items-start gap-3">
                <Brain className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-[10px] font-bold text-violet-400 uppercase">AI Operator Brief</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${
                      operatorSummary.system_status === "DEGRADED" ? "text-red-400 border-red-700/30 bg-red-900/20" :
                      operatorSummary.system_status === "ELEVATED" ? "text-amber-400 border-amber-700/25 bg-amber-900/15" :
                      "text-emerald-400 border-emerald-700/20 bg-emerald-900/10"
                    }`}>{operatorSummary.system_status}</span>
                    <button onClick={() => router.push("/ai-insights")} className="ml-auto text-[10px] text-blue-400 hover:text-blue-300">Full AI Console →</button>
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed">{operatorSummary.headline}</p>
                  {operatorSummary.key_alerts.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {operatorSummary.key_alerts.slice(0, 2).map((alert, i) => (
                        <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-red-900/20 text-red-300 border border-red-700/25">{alert}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Top Priority Items */}
          {priorityQueue && priorityQueue.length > 0 && (
            <div className="rounded-xl border border-amber-700/25 bg-amber-900/6">
              <div className="px-4 py-2.5 border-b border-white/8 flex items-center gap-2">
                <Target className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-xs font-semibold text-amber-300">Priority Queue</span>
                <span className="ml-auto text-[10px] text-slate-500">{priorityQueue.length} items</span>
              </div>
              <div className="divide-y divide-white/5">
                {priorityQueue.slice(0, 4).map((item) => (
                  <div key={item.payment_id}
                    onClick={() => router.push(`/payments/${item.payment_id}`)}
                    className="px-4 py-2 flex items-center gap-2 hover:bg-white/4 cursor-pointer group transition"
                  >
                    <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                      item.urgency === "CRITICAL" ? "bg-red-500" : item.urgency === "HIGH" ? "bg-amber-500" : "bg-yellow-400"
                    }`} />
                    <span className="text-[10px] font-mono text-slate-300 flex-1 truncate">{item.payment_reference}</span>
                    {item.sla_breach && <span className="text-[9px] text-red-400 border border-red-700/25 px-1 rounded">SLA</span>}
                    <span className="text-[10px] font-bold text-slate-500">{item.priority_score.toFixed(0)}</span>
                    <ChevronRight className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Map + System Health */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          {mapError ? (
            <Panel className="h-64 flex flex-col items-center justify-center gap-3">
              <Globe className="w-8 h-8 text-slate-600" />
              <p className="text-slate-500 text-sm">Map unavailable — backend unreachable</p>
              <button onClick={mapRefetch} className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300">
                <RefreshCw className="w-3 h-3" /> Retry
              </button>
            </Panel>
          ) : mapFlows ? (
            <Panel noPad className="p-5">
              <PaymentFlowMap flows={mapFlows} />
            </Panel>
          ) : (
            <Panel className="h-64 flex items-center justify-center">
              <div className="text-slate-500 text-sm">Loading map...</div>
            </Panel>
          )}
        </div>
        <div className="space-y-3">
          {health && (
            <Panel>
              <SectionHeader title="System Health" icon={Shield} className="mb-3" />
              <div className="space-y-3">
                {/* Overall score */}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">System Status</span>
                  <span className={`text-xs font-bold ${health.system_status === "OPERATIONAL" ? "text-emerald-400" : health.system_status === "DEGRADED" ? "text-amber-400" : "text-red-400"}`}>
                    {health.system_status}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-2xl font-bold text-white tabular-nums">{health.overall_health_score.toFixed(0)}</div>
                  <div className="flex-1">
                    <div className="w-full bg-white/10 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all ${health.overall_health_score > 80 ? "bg-emerald-500" : health.overall_health_score > 60 ? "bg-amber-500" : "bg-red-500"}`}
                        style={{ width: `${health.overall_health_score}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">Overall health score</p>
                  </div>
                </div>

                {/* Sub-system scores */}
                <div className="grid grid-cols-2 gap-1.5 pt-1">
                  {[
                    { label: "Compliance", score: health.compliance_health.health_score },
                    { label: "Settlement", score: health.settlement_health.health_score },
                    { label: "Routing", score: health.routing_health.health_score },
                    { label: "FX", score: health.fx_health.health_score },
                  ].map(({ label, score }) => (
                    <div key={label} className="bg-white/5 rounded-lg p-2">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] text-slate-400">{label}</span>
                        <span className={`text-[10px] font-bold ${score > 80 ? "text-emerald-400" : score > 60 ? "text-amber-400" : "text-red-400"}`}>{score.toFixed(0)}</span>
                      </div>
                      <div className="w-full bg-white/10 rounded-full h-1">
                        <div className={`h-1 rounded-full ${score > 80 ? "bg-emerald-500" : score > 60 ? "bg-amber-500" : "bg-red-500"}`} style={{ width: `${score}%` }} />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Key metrics */}
                <div className="pt-1 border-t border-white/10 space-y-1.5">
                  {[
                    { label: "Success Rate", value: `${health.success_rate}%`, color: "text-emerald-400" },
                    { label: "Anomaly Rate", value: `${health.anomaly_rate}%`, color: "text-amber-400" },
                    { label: "SLA Breach Rate", value: `${health.sla_breach_rate}%`, color: health.sla_breach_rate > 5 ? "text-red-400" : "text-slate-300" },
                    { label: "Queue Depth", value: health.queue_depth, color: "text-white" },
                    { label: "Throughput/hr", value: health.throughput_per_hour.toFixed(1), color: "text-white" },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-400">{label}</span>
                      <span className={`text-[10px] font-semibold ${color}`}>{value}</span>
                    </div>
                  ))}
                </div>

                {/* Sanctions / recon highlights */}
                <div className="pt-1 border-t border-white/10">
                  <div className="grid grid-cols-2 gap-1.5">
                    {[
                      { label: "Sanctions", value: health.compliance_health.sanctions_hits, warn: true },
                      { label: "In Review", value: health.compliance_health.pending_review, warn: health.compliance_health.pending_review > 0 },
                      { label: "Recon Breaks", value: health.settlement_health.recon_mismatches, warn: true },
                      { label: "GW Timeouts", value: health.routing_health.gateway_timeouts, warn: health.routing_health.gateway_timeouts > 2 },
                    ].map(({ label, value, warn }) => (
                      <div key={label} className="bg-white/5 rounded-lg p-2 text-center">
                        <div className={`text-sm font-bold ${warn && value > 0 ? "text-amber-400" : "text-white"}`}>{value}</div>
                        <div className="text-[10px] text-slate-500">{label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Panel>
          )}
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Stage distribution */}
        <Panel>
          <SectionHeader title="Stage Distribution" icon={BarChart3} className="mb-4" />
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={stageData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                dataKey="value"
                paddingAngle={2}
              >
                {stageData.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, fontSize: 11 }}
                labelStyle={{ color: "#94a3b8" }}
                itemStyle={{ color: "#e2e8f0" }}
                formatter={(value: number, name: string) => [value.toLocaleString(), name]}
              />
            </PieChart>
          </ResponsiveContainer>
        </Panel>

        {/* Anomaly categories */}
        <Panel>
          <SectionHeader
            title="Anomaly Types"
            icon={AlertTriangle}
            className="mb-4"
            action={
              <button onClick={() => router.push("/anomalies")} className="text-xs text-blue-400 hover:text-blue-300">
                View all →
              </button>
            }
          />
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={anomalyData} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 9, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={95} />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, fontSize: 11 }}
                labelStyle={{ color: "#94a3b8" }}
                itemStyle={{ color: "#e2e8f0" }}
                cursor={{ fill: "rgba(255,255,255,0.05)" }}
              />
              <Bar dataKey="count" radius={[0, 3, 3, 0]}>
                {anomalyData.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        {/* Corridor distribution */}
        <Panel>
          <SectionHeader title="Top Corridors" icon={TrendingUp} className="mb-4" />
          <div className="space-y-2">
            {corridorData.slice(0, 8).map(({ corridor, count }, i) => (
              <div
                key={corridor}
                className="flex items-center gap-2 cursor-pointer group"
                onClick={() => router.push(`/payments?search=${corridor}`)}
              >
                <div className="w-5 text-[10px] text-slate-500 text-right">{i + 1}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs font-mono text-slate-300 group-hover:text-white transition">{corridor}</span>
                    <span className="text-xs text-slate-400">{count}</span>
                  </div>
                  <div className="w-full bg-white/8 rounded-full h-1">
                    <div
                      className="h-1 rounded-full bg-blue-500/70 transition-all"
                      style={{ width: `${(count / (corridorData[0]?.count ?? 1)) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* Stage metrics row */}
      {stageMetrics && stageMetrics.length > 0 && (
        <Panel noPad>
          <div className="px-5 py-3 border-b border-white/10 flex items-center justify-between">
            <SectionHeader title="Stage Pipeline Health" icon={BarChart3} subtitle="Processing time vs SLA by stage" />
            <button onClick={() => router.push("/ai-insights")} className="text-xs text-blue-400 hover:text-blue-300">Details →</button>
          </div>
          <div className="px-5 py-3 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {stageMetrics.map((sm) => {
              const delta = sm.avg_duration_seconds - sm.expected_duration_seconds;
              const ratio = sm.avg_duration_seconds / Math.max(sm.expected_duration_seconds, 1);
              const isHot = ratio > 1.5 || sm.bottleneck_count > 1;
              return (
                <div key={sm.stage} className={`rounded-lg p-2.5 border ${isHot ? "border-amber-500/30 bg-amber-500/5" : "border-white/5 bg-white/3"}`}>
                  <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wide mb-1">{sm.stage}</p>
                  <p className={`text-sm font-bold ${isHot ? "text-amber-300" : "text-white"}`}>
                    {sm.avg_duration_seconds < 60 ? `${sm.avg_duration_seconds.toFixed(0)}s` : `${(sm.avg_duration_seconds/60).toFixed(0)}m`}
                  </p>
                  <p className="text-[10px] text-slate-500">
                    exp {sm.expected_duration_seconds < 60 ? `${sm.expected_duration_seconds}s` : `${(sm.expected_duration_seconds/60).toFixed(0)}m`}
                  </p>
                  <div className="mt-1.5 flex items-center gap-1">
                    {sm.failure_rate > 0 && <span className="text-[9px] text-red-400">{sm.failure_rate.toFixed(0)}% fail</span>}
                    {sm.bottleneck_count > 0 && <span className="text-[9px] text-amber-400">{sm.bottleneck_count} bneck</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>
      )}

      {/* Live payments feed */}
      <Panel noPad>
        <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
          <SectionHeader title="Live Payment Feed" icon={Activity} subtitle="Active & recent payments" />
          <button onClick={() => router.push("/payments")} className="text-xs text-blue-400 hover:text-blue-300">
            View all →
          </button>
        </div>
        <div className="divide-y divide-white/5">
          {liveLoading ? (
            <div className="px-5 py-8 text-center text-sm text-slate-500">Loading...</div>
          ) : livePayments && livePayments.length > 0 ? (
            livePayments.map((p) => (
              <div
                key={p.id}
                className="px-5 py-3 flex items-center gap-3 hover:bg-white/5 cursor-pointer transition"
                onClick={() => router.push(`/payments/${p.id}`)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-mono text-slate-300">{p.payment_reference}</span>
                    {p.anomaly_flag && p.anomaly_severity && (
                      <span className={`w-2 h-2 rounded-full ${SEVERITY_DOT[p.anomaly_severity]}`} />
                    )}
                    {p.sla_breach && <SLABadge breach={true} recovered={p.recovered} />}
                  </div>
                  <div className="text-xs text-slate-500 truncate mt-0.5">
                    {p.source_client_name} → {p.beneficiary_name}
                  </div>
                </div>
                <div className="text-xs text-slate-400 font-mono hidden sm:block">
                  {p.source_country} → {p.destination_country}
                </div>
                <div className="text-xs font-semibold text-white tabular-nums">
                  {formatCurrency(p.amount, p.source_currency)}
                </div>
                <StageBadge stage={p.current_stage} />
                <StatusBadge status={p.current_status} />
                <div className="text-xs text-slate-500 hidden lg:block">
                  {formatRelativeTime(p.updated_at)}
                </div>
              </div>
            ))
          ) : (
            <div className="px-5 py-8 text-center text-sm text-slate-500">No active payments</div>
          )}
        </div>
      </Panel>

      {/* Delayed countries */}
      {overview && overview.top_delayed_countries.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Panel>
            <SectionHeader title="Top Delayed Countries" icon={Clock} className="mb-4" />
            <div className="space-y-2">
              {overview.top_delayed_countries.map(({ country, count }) => (
                <div
                  key={country}
                  className="flex items-center justify-between py-1.5 cursor-pointer hover:bg-white/5 rounded px-2 -mx-2 transition"
                  onClick={() => router.push(`/payments?destination_country=${country}`)}
                >
                  <span className="text-sm text-slate-300">{country}</span>
                  <span className="text-xs font-semibold text-amber-400">{count} delayed</span>
                </div>
              ))}
            </div>
          </Panel>
          <Panel>
            <SectionHeader title="Avg Processing Time" icon={TrendingUp} className="mb-4" />
            <div className="flex items-center gap-4">
              <div className="text-4xl font-bold text-white tabular-nums">
                {overview.average_processing_time_seconds < 3600
                  ? `${(overview.average_processing_time_seconds / 60).toFixed(0)}m`
                  : `${(overview.average_processing_time_seconds / 3600).toFixed(1)}h`}
              </div>
              <div>
                <p className="text-xs text-slate-400">Average end-to-end processing time</p>
                <p className="text-xs text-slate-500 mt-1">Based on completed payments</p>
              </div>
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}

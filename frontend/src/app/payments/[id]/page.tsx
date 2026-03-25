"use client";
import { useParams, useRouter } from "next/navigation";
import { useApi } from "@/hooks/useApi";
import { paymentsApi, aiApi } from "@/lib/api/payments";
import { StageBadge, StatusBadge, SeverityBadge, PriorityBadge, AnomalyTypeBadge, AnomalyStatusBadge } from "@/components/shared/Badge";
import { Panel, PanelHeader, PanelBody } from "@/components/shared/Panel";
import { SectionHeader } from "@/components/shared/SectionHeader";
import { PageLoader } from "@/components/shared/LoadingSkeleton";
import { ErrorState } from "@/components/shared/EmptyState";
import { formatCurrency, formatDate, formatRelativeTime, formatDuration } from "@/lib/formatters";
import { SEVERITY_BG, SEVERITY_DOT, STAGE_BG, STAGE_ORDER } from "@/lib/constants";
import {
  ArrowLeft, AlertTriangle, Activity, FileText,
  RotateCcw, Shield, Clock, CreditCard, MapPin,
  TrendingUp, BrainCircuit, ChevronRight, Timer, Cpu, GitBranch, Zap, Brain,
} from "lucide-react";
import { AISummaryBanner } from "@/components/ai/AISummaryBanner";
import { RCASummaryCard } from "@/components/ai/RCASummaryCard";
import { RecommendationList } from "@/components/ai/RecommendationList";
import { RepairActionTable } from "@/components/ai/RepairActionTable";
import { AgentTracePanel } from "@/components/ai/AgentTracePanel";
import { clsx } from "clsx";
import { SLABadge } from "@/components/shared/SLABadge";
import { ActionStatusBadge } from "@/components/shared/ActionStatusBadge";

export default function PaymentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const { data: payment, loading, error, refetch } = useApi(() => paymentsApi.get(id), [id]);
  const { data: journey } = useApi(() => paymentsApi.journey(id), [id]);
  const { data: timeline } = useApi(() => paymentsApi.timeline(id), [id]);
  const { data: logs } = useApi(() => paymentsApi.logs(id), [id]);
  const { data: paymentAnomalies } = useApi(() => paymentsApi.anomalies(id), [id]);
  const { data: observability } = useApi(() => paymentsApi.observability(id), [id]);
  const { data: aiPackage, loading: aiLoading } = useApi(() => aiApi.paymentAIPackage(id), [id]);

  if (loading) return <PageLoader />;
  if (error || !payment) return (
    <div className="max-w-screen-xl mx-auto px-6 py-8">
      <ErrorState message={error ?? "Payment not found"} onRetry={refetch} />
    </div>
  );

  const stageIdx = STAGE_ORDER.indexOf(payment.current_stage as any);
  const processingTime = payment.actual_completion_at
    ? (new Date(payment.actual_completion_at).getTime() - new Date(payment.created_at).getTime()) / 1000
    : null;

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-6 space-y-5">
      {/* Back + header */}
      <div className="flex items-start gap-4">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition mt-1"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-bold text-white font-mono">{payment.payment_reference}</h1>
            <StageBadge stage={payment.current_stage} />
            <StatusBadge status={payment.current_status} />
            <PriorityBadge priority={payment.priority} />
            {payment.anomaly_flag && payment.anomaly_type && (
              <AnomalyTypeBadge type={payment.anomaly_type} />
            )}
            {payment.anomaly_severity && (
              <SeverityBadge severity={payment.anomaly_severity} />
            )}
            {payment.sla_breach && (
              <SLABadge breach={true} breachSeconds={payment.sla_breach_seconds} recovered={payment.recovered} />
            )}
            {payment.bottleneck_stage && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-500/10 text-orange-400 border border-orange-500/20">
                <Zap className="w-2.5 h-2.5" /> Bottleneck: {payment.bottleneck_stage}
              </span>
            )}
            {payment.escalation_flag && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-red-500/10 text-red-400">Escalated</span>
            )}
            {payment.recovered && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-500/10 text-blue-400">Recovered</span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            {payment.source_client_name} → {payment.beneficiary_name}
          </p>
        </div>
        <button
          onClick={() => paymentsApi.replay(id).then((r) => router.push(`/payments/${r.payment.id}`))}
          className="flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/15 border border-white/20 rounded-lg text-sm text-slate-300 transition"
        >
          <RotateCcw className="w-4 h-4" /> Replay
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Send Amount", value: formatCurrency(payment.send_amount, payment.source_currency) },
          { label: "Receive Amount", value: formatCurrency(payment.receive_amount, payment.destination_currency) },
          { label: "FX Rate", value: `1 ${payment.source_currency} = ${payment.fx_rate.toFixed(4)} ${payment.destination_currency}` },
          { label: "Processing Time", value: processingTime ? formatDuration(processingTime) : "In progress" },
        ].map(({ label, value }) => (
          <Panel key={label} className="!py-3 !px-4">
            <p className="text-xs text-slate-400">{label}</p>
            <p className="mt-0.5 text-sm font-semibold text-white">{value}</p>
          </Panel>
        ))}
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column: Payment details + Flags */}
        <div className="space-y-5">
          {/* Payment details */}
          <Panel noPad>
            <PanelHeader>
              <SectionHeader title="Payment Details" icon={CreditCard} />
            </PanelHeader>
            <PanelBody>
              <dl className="space-y-2.5">
                {[
                  ["ID", <span key="id" className="font-mono text-xs text-blue-300">{payment.id}</span>],
                  ["Type", payment.payment_type],
                  ["Rail", payment.system_rail],
                  ["Corridor", payment.corridor],
                  ["Route Type", payment.route_type],
                  ["Source Country", payment.source_country],
                  ["Destination", payment.destination_country],
                  ["Priority", payment.priority],
                  ["Created", formatDate(payment.created_at)],
                  ["Expected", payment.expected_completion_at ? formatDate(payment.expected_completion_at) : "—"],
                  ["Completed", payment.actual_completion_at ? formatDate(payment.actual_completion_at) : "—"],
                ].map(([k, v]) => (
                  <div key={String(k)} className="flex items-start justify-between gap-2">
                    <dt className="text-xs text-slate-400 flex-shrink-0">{k}</dt>
                    <dd className="text-xs text-slate-200 text-right">{v as any}</dd>
                  </div>
                ))}
              </dl>
            </PanelBody>
          </Panel>

          {/* Flags */}
          <Panel noPad>
            <PanelHeader>
              <SectionHeader title="Exception Flags" icon={Shield} />
            </PanelHeader>
            <PanelBody className="space-y-2">
              {[
                { label: "Sanctions Hit", active: payment.sanctions_hit, severity: "HIGH" },
                { label: "Validation Error", active: payment.validation_error, severity: "MEDIUM" },
                { label: "Gateway Timeout", active: payment.gateway_timeout, severity: "MEDIUM" },
                { label: "Reconciliation Break", active: payment.reconciliation_break, severity: "CRITICAL" },
                { label: "Anomaly Detected", active: payment.anomaly_flag, severity: payment.anomaly_severity ?? "LOW" },
              ].map(({ label, active, severity }) => (
                <div key={label} className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">{label}</span>
                  <span className={clsx(
                    "text-xs font-medium px-2 py-0.5 rounded border",
                    active ? SEVERITY_BG[severity as import("@/lib/types").AnomalySeverity] : "text-slate-500 border-slate-700"
                  )}>
                    {active ? "ACTIVE" : "Clear"}
                  </span>
                </div>
              ))}
            </PanelBody>
          </Panel>
        </div>

        {/* Center + Right: Route journey + Timeline */}
        <div className="lg:col-span-2 space-y-5">
          {/* Route path */}
          <Panel noPad>
            <PanelHeader>
              <SectionHeader title="Payment Journey" icon={MapPin}
                subtitle={`${payment.route_type} • ${payment.route_path.join(" → ")}`} />
            </PanelHeader>
            <PanelBody>
              {/* Stage pipeline */}
              <div className="flex items-center gap-0 overflow-x-auto pb-2 mb-4">
                {STAGE_ORDER.map((stage, i) => {
                  const isPast = i < stageIdx;
                  const isCurrent = i === stageIdx;
                  const isActive = i <= stageIdx;
                  return (
                    <div key={stage} className="flex items-center flex-shrink-0">
                      <div className={clsx(
                        "flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs font-medium border transition",
                        isCurrent ? STAGE_BG[payment.current_stage] : isActive
                          ? "bg-emerald-900/30 text-emerald-400 border-emerald-700"
                          : "bg-white/5 text-slate-500 border-white/10"
                      )}>
                        {isActive && !isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
                        {isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />}
                        <span>{stage}</span>
                      </div>
                      {i < STAGE_ORDER.length - 1 && (
                        <ChevronRight className={clsx("w-3 h-3 flex-shrink-0", isActive ? "text-emerald-700" : "text-slate-700")} />
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Route nodes */}
              {journey && (
                <div className="flex items-center gap-3 overflow-x-auto">
                  {journey.nodes.map((node, i) => (
                    <div key={i} className="flex items-center gap-3 flex-shrink-0">
                      <div className={clsx(
                        "relative flex flex-col items-center gap-1.5 px-4 py-3 rounded-xl border text-center min-w-[90px]",
                        node.is_delayed ? "border-amber-500/50 bg-amber-900/20" :
                        node.status === "completed" ? "border-emerald-600/40 bg-emerald-900/15" :
                        node.is_origin ? "border-blue-500/50 bg-blue-900/20" :
                        node.is_destination ? "border-violet-500/50 bg-violet-900/20" :
                        "border-white/15 bg-white/5"
                      )}>
                        {node.is_delayed && (
                          <span className="absolute -top-2 left-1/2 -translate-x-1/2 text-[10px] bg-amber-500 text-black px-1 rounded font-bold">DELAY</span>
                        )}
                        <span className="text-lg font-bold text-white">{node.country}</span>
                        <span className="text-[10px] text-slate-400">{node.node_name}</span>
                        <span className={clsx("text-[10px] font-medium",
                          node.is_delayed ? "text-amber-400" :
                          node.status === "completed" ? "text-emerald-400" :
                          node.is_origin ? "text-blue-400" :
                          "text-slate-500"
                        )}>
                          {node.is_origin ? "Origin" : node.is_destination ? "Destination" : "Transit"}
                        </span>
                      </div>
                      {i < journey.nodes.length - 1 && (
                        <div className="flex items-center gap-0.5 flex-shrink-0">
                          <div className="w-6 h-px bg-white/20" />
                          <ChevronRight className="w-3 h-3 text-slate-600" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </PanelBody>
          </Panel>

          {/* Timeline / Events */}
          <Panel noPad>
            <PanelHeader>
              <SectionHeader title="Event Timeline" icon={Activity}
                subtitle={timeline ? `${timeline.length} events` : undefined} />
            </PanelHeader>
            <div className="max-h-72 overflow-y-auto divide-y divide-white/5">
              {timeline?.map((event) => (
                <div key={event.id} className="px-5 py-3 flex gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    <span className={clsx(
                      "w-2 h-2 rounded-full block mt-1",
                      event.severity ? SEVERITY_DOT[event.severity] :
                      event.status === "COMPLETED" ? "bg-emerald-500" :
                      event.status === "FAILED" ? "bg-red-500" :
                      event.status === "ON_HOLD" ? "bg-yellow-500" :
                      "bg-blue-500"
                    )} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-medium text-slate-200">{event.message}</span>
                      <StageBadge stage={event.stage} />
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-slate-500">{event.actor}</span>
                      <span className="text-[10px] text-slate-600">•</span>
                      <span className="text-[10px] text-slate-500">{formatDate(event.timestamp)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          {/* Logs */}
          <Panel noPad>
            <PanelHeader>
              <SectionHeader title="System Logs" icon={FileText}
                subtitle={logs ? `${logs.length} entries` : undefined} />
            </PanelHeader>
            <div className="max-h-60 overflow-y-auto font-mono text-xs">
              {logs?.map((log) => (
                <div key={log.id} className="px-5 py-1.5 flex gap-3 border-b border-white/5 hover:bg-white/3">
                  <span className="text-slate-500 flex-shrink-0">{formatRelativeTime(log.timestamp)}</span>
                  <span className={clsx(
                    "flex-shrink-0 font-semibold",
                    log.log_level === "ERROR" || log.log_level === "CRITICAL" ? "text-red-400" :
                    log.log_level === "WARNING" ? "text-amber-400" :
                    log.log_level === "DEBUG" ? "text-slate-500" : "text-emerald-400"
                  )}>{log.log_level}</span>
                  <span className="text-blue-300/70 flex-shrink-0">[{log.component}]</span>
                  <span className="text-slate-300 truncate">{log.message}</span>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>

      {/* Observability Panel */}
      {observability && (
        <Panel noPad>
          <PanelHeader>
            <SectionHeader title="Observability" icon={Cpu} subtitle="Stage timings, node latency, bottleneck analysis" />
          </PanelHeader>
          <div className="px-5 py-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Stage timing chart */}
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Stage Timings</p>
              <div className="space-y-2">
                {observability.stage_detail.map((sd) => {
                  const ratio = sd.duration_seconds / Math.max(sd.expected_seconds, 1);
                  const barWidth = Math.min(ratio * 50, 100);
                  const isHot = sd.is_bottleneck || ratio > 2;
                  return (
                    <div key={sd.stage}>
                      <div className="flex items-center justify-between mb-0.5">
                        <div className="flex items-center gap-1.5">
                          <span className={`text-[10px] font-mono uppercase ${isHot ? 'text-amber-300' : 'text-slate-400'}`}>{sd.stage}</span>
                          {sd.is_bottleneck && <span className="text-[9px] bg-amber-500/20 text-amber-400 px-1 rounded">BOTTLENECK</span>}
                          {sd.retry_count > 0 && <span className="text-[9px] text-red-400">{sd.retry_count}x retry</span>}
                        </div>
                        <div className="text-right">
                          <span className={`text-[10px] font-semibold ${isHot ? 'text-amber-300' : 'text-white'}`}>
                            {sd.duration_seconds < 60 ? `${sd.duration_seconds.toFixed(0)}s` : `${(sd.duration_seconds/60).toFixed(1)}m`}
                          </span>
                          <span className="text-[9px] text-slate-500 ml-1">
                            / {sd.expected_seconds < 60 ? `${sd.expected_seconds.toFixed(0)}s` : `${(sd.expected_seconds/60).toFixed(0)}m`} exp
                          </span>
                        </div>
                      </div>
                      <div className="w-full bg-white/8 rounded-full h-1.5 relative">
                        <div className="h-1.5 rounded-full bg-white/20 absolute" style={{ width: `50%` }} />
                        <div
                          className={`h-1.5 rounded-full absolute ${isHot ? 'bg-amber-500' : 'bg-blue-500'}`}
                          style={{ width: `${barWidth}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
              {observability.total_processing_seconds != null && (
                <div className="mt-3 pt-3 border-t border-white/10 flex items-center justify-between">
                  <span className="text-xs text-slate-400">Total Processing</span>
                  <span className="text-xs font-bold text-white">
                    {observability.total_processing_seconds < 3600
                      ? `${(observability.total_processing_seconds / 60).toFixed(1)}m`
                      : `${(observability.total_processing_seconds / 3600).toFixed(2)}h`}
                  </span>
                </div>
              )}
            </div>

            {/* Node latency */}
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Node Latency</p>
              <div className="space-y-2">
                {observability.node_latency.map((nl) => (
                  <div key={nl.node_name} className={`flex items-center justify-between p-2 rounded-lg border ${nl.is_delay_node ? 'border-amber-500/30 bg-amber-500/5' : 'border-white/5 bg-white/3'}`}>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs text-slate-200">{nl.node_name}</span>
                        {nl.is_delay_node && <span className="text-[9px] text-amber-400 bg-amber-500/10 px-1 rounded">DELAY NODE</span>}
                      </div>
                      <span className="text-[10px] text-slate-500">{nl.country} · {nl.node_type}</span>
                    </div>
                    <div className="text-right">
                      <span className={`text-xs font-semibold ${nl.health_status === 'HEALTHY' ? 'text-emerald-400' : nl.health_status === 'DEGRADED' ? 'text-amber-400' : 'text-red-400'}`}>
                        {nl.avg_latency_ms.toFixed(0)}ms
                      </span>
                      <div className="text-[9px] text-slate-500">{nl.health_status}</div>
                    </div>
                  </div>
                ))}
              </div>
              {/* SLA / escalation flags */}
              <div className="mt-3 pt-3 border-t border-white/10 flex flex-wrap gap-2">
                <SLABadge breach={observability.sla_breach} breachSeconds={observability.sla_breach_seconds} recovered={observability.recovered} />
                {observability.escalation_flag && (
                  <span className="text-[10px] px-1.5 py-0.5 bg-red-500/10 text-red-400 rounded">Escalated</span>
                )}
                {observability.operator_intervention && (
                  <span className="text-[10px] px-1.5 py-0.5 bg-blue-500/10 text-blue-400 rounded">Operator Intervened</span>
                )}
              </div>
            </div>
          </div>
        </Panel>
      )}

      {/* Anomaly summary */}
      {paymentAnomalies && paymentAnomalies.length > 0 && (
        <Panel noPad>
          <PanelHeader>
            <SectionHeader title="Anomaly Details" icon={AlertTriangle}
              subtitle={`${paymentAnomalies.length} anomalies detected`} />
          </PanelHeader>
          <div className="divide-y divide-white/5">
            {paymentAnomalies.map((anomaly) => (
              <div key={anomaly.id} className="px-5 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-white">{anomaly.title}</span>
                      <SeverityBadge severity={anomaly.severity} />
                      <AnomalyStatusBadge status={anomaly.status} />
                      <ActionStatusBadge status={anomaly.action_status} />
                      {anomaly.anomaly_code && (
                        <span className="text-[10px] font-mono text-slate-500 bg-white/5 px-1.5 rounded">{anomaly.anomaly_code}</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-1.5">{anomaly.description}</p>
                    {anomaly.root_symptom && (
                      <p className="text-xs text-slate-500 mt-1">
                        <span className="text-slate-400 font-medium">Root symptom: </span>{anomaly.root_symptom}
                      </p>
                    )}
                    {anomaly.probable_cause && (
                      <p className="text-xs text-slate-500 mt-1">
                        <span className="text-slate-400 font-medium">Probable cause: </span>{anomaly.probable_cause}
                      </p>
                    )}
                    {anomaly.evidence_summary && (
                      <p className="text-xs text-slate-500 mt-1 italic">Evidence: {anomaly.evidence_summary}</p>
                    )}
                    {anomaly.recommended_action && (
                      <div className="mt-2 px-3 py-2 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                        <p className="text-xs text-blue-300">
                          <span className="font-semibold">Recommended: </span>{anomaly.recommended_action}
                        </p>
                      </div>
                    )}
                    <div className="mt-2 flex flex-wrap gap-3">
                      {anomaly.operational_impact_score != null && (
                        <span className="text-[10px] text-slate-400">Impact: <span className={`font-semibold ${anomaly.operational_impact_score >= 7 ? 'text-red-400' : anomaly.operational_impact_score >= 4 ? 'text-amber-400' : 'text-green-400'}`}>{anomaly.operational_impact_score.toFixed(1)}/10</span></span>
                      )}
                      {anomaly.client_impact_level && (
                        <span className="text-[10px] text-slate-400">Client impact: <span className="text-white">{anomaly.client_impact_level}</span></span>
                      )}
                      {anomaly.resolution_eta_minutes != null && (
                        <span className="text-[10px] text-slate-400">ETA: <span className="text-white">{anomaly.resolution_eta_minutes}m</span></span>
                      )}
                      {anomaly.recurrence_count > 0 && (
                        <span className="text-[10px] text-amber-400">Recurred {anomaly.recurrence_count}x</span>
                      )}
                    </div>
                  </div>
                  {anomaly.confidence !== undefined && (
                    <div className="text-right flex-shrink-0">
                      <div className="text-xs text-slate-400">Confidence</div>
                      <div className="text-lg font-bold text-white">{(anomaly.confidence * 100).toFixed(0)}%</div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* AI Intelligence Section */}
      {aiLoading && (
        <Panel>
          <div className="flex items-center gap-2 py-2">
            <Brain className="w-4 h-4 text-violet-400 animate-pulse" />
            <span className="text-xs text-slate-400">Running AI analysis...</span>
          </div>
        </Panel>
      )}

      {aiPackage && (
        <>
          {/* AI Summary Banner */}
          <Panel noPad>
            <PanelHeader>
              <SectionHeader title="AI Operator Summary" icon={Brain} subtitle="What happened, why, and what to do" />
            </PanelHeader>
            <div className="px-5 pb-5">
              <AISummaryBanner summary={aiPackage.ai_summary} />
            </div>
          </Panel>

          {/* RCA + Recommendations side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <Panel noPad>
              <PanelHeader>
                <SectionHeader title="Root Cause Analysis" icon={BrainCircuit}
                  subtitle={`${aiPackage.rca.issue_category} · ${aiPackage.rca.resolution_priority} priority`} />
              </PanelHeader>
              <div className="px-5 pb-5">
                <RCASummaryCard rca={aiPackage.rca} compact />
              </div>
            </Panel>

            <Panel noPad>
              <PanelHeader>
                <SectionHeader title="Recommendations" icon={Zap}
                  subtitle={`${aiPackage.recommendations.length} action(s) suggested`} />
              </PanelHeader>
              <div className="px-5 pb-5">
                <RecommendationList recommendations={aiPackage.recommendations} compact />
              </div>
            </Panel>
          </div>

          {/* Repair Actions */}
          {aiPackage.repair_actions.length > 0 && (
            <Panel noPad>
              <PanelHeader>
                <SectionHeader title="Repair Playbooks" icon={RotateCcw}
                  subtitle={`${aiPackage.repair_actions.length} repair action(s) available`} />
              </PanelHeader>
              <div className="px-5 pb-5">
                <RepairActionTable actions={aiPackage.repair_actions} />
              </div>
            </Panel>
          )}

          {/* Agent Trace */}
          <Panel noPad>
            <PanelHeader>
              <SectionHeader title="Agent Analysis Trace" icon={Cpu}
                subtitle={`${aiPackage.agent_trace.agents_run.length} agents · ${aiPackage.agent_trace.total_duration_ms}ms · ${aiPackage.agent_trace.mode}`} />
            </PanelHeader>
            <div className="px-5 pb-5">
              <AgentTracePanel trace={aiPackage.agent_trace} />
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}

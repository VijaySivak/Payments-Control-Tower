// ── Enums ───────────────────────────────────────────────────────

export type PaymentStage =
  | "INITIATED"
  | "VALIDATION"
  | "COMPLIANCE"
  | "FX"
  | "ROUTING"
  | "SETTLEMENT"
  | "RECONCILIATION"
  | "COMPLETED"
  | "FAILED"
  | "ON_HOLD";

export type PaymentStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "FAILED"
  | "ON_HOLD"
  | "DELAYED";

export type PaymentPriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type PaymentType = "SWIFT" | "WIRE" | "ACH" | "SEPA" | "RTGS" | "INSTANT";

export type AnomalyType =
  | "SANCTIONS_FALSE_POSITIVE"
  | "GATEWAY_TIMEOUT"
  | "VALIDATION_ERROR"
  | "FX_DELAY"
  | "MISSING_INTERMEDIARY"
  | "SETTLEMENT_DELAY"
  | "RECONCILIATION_MISMATCH";

export type AnomalySeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type AnomalyScope = "PAYMENT" | "SYSTEM" | "CORRIDOR" | "COUNTRY";

export type AnomalyStatus = "OPEN" | "INVESTIGATING" | "RESOLVED";

export type ActionStatus = "OPEN" | "TRIAGED" | "IN_PROGRESS" | "MITIGATED" | "RESOLVED";

export type NodeHealthStatus = "HEALTHY" | "DEGRADED" | "CRITICAL" | "OFFLINE";

export type EventType =
  | "STAGE_TRANSITION"
  | "ANOMALY_DETECTED"
  | "COMPLIANCE_CHECK"
  | "FX_QUOTE"
  | "ROUTE_SELECTED"
  | "SETTLEMENT_INITIATED"
  | "RECONCILIATION_CHECK"
  | "HOLD_APPLIED"
  | "RETRY_ATTEMPTED"
  | "MANUAL_REVIEW"
  | "ESCALATION"
  | "OPERATOR_INTERVENTION"
  | "SLA_BREACH"
  | "ROUTE_FAILOVER";

export type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export type RouteType = "DIRECT" | "INTERMEDIARY" | "MULTI_HOP";

export type NodeType =
  | "CORRESPONDENT_BANK"
  | "GATEWAY"
  | "COMPLIANCE_HUB"
  | "SETTLEMENT_NETWORK"
  | "FX_PROVIDER"
  | "CLEARING_HOUSE";

// ── Domain Types ────────────────────────────────────────────────

export interface Payment {
  id: string;
  payment_reference: string;
  source_client_name: string;
  beneficiary_name: string;
  source_country: string;
  destination_country: string;
  source_currency: string;
  destination_currency: string;
  amount: number;
  fx_rate: number;
  send_amount: number;
  receive_amount: number;
  corridor: string;
  priority: PaymentPriority;
  payment_type: PaymentType;
  current_stage: PaymentStage;
  current_status: PaymentStatus;
  anomaly_flag: boolean;
  anomaly_type?: AnomalyType;
  anomaly_severity?: AnomalySeverity;
  anomaly_reason?: string;
  created_at: string;
  updated_at: string;
  expected_completion_at?: string;
  actual_completion_at?: string;
  system_rail: string;
  route_type: RouteType;
  route_path: string[];
  delay_node?: string;
  delay_country?: string;
  sanctions_hit: boolean;
  validation_error: boolean;
  gateway_timeout: boolean;
  reconciliation_break: boolean;
  metadata: Record<string, unknown>;
  // Phase 2
  stage_timings: Record<string, number>;
  stage_entry_times: Record<string, string>;
  expected_stage_durations: Record<string, number>;
  retry_counts: Record<string, number>;
  queue_wait_seconds: Record<string, number>;
  sla_breach: boolean;
  sla_breach_seconds?: number;
  bottleneck_stage?: string;
  bottleneck_node?: string;
  total_processing_seconds?: number;
  escalation_flag: boolean;
  operator_intervention: boolean;
  recovered: boolean;
}

export interface PaymentSummary {
  id: string;
  payment_reference: string;
  source_client_name: string;
  beneficiary_name: string;
  source_country: string;
  destination_country: string;
  corridor: string;
  amount: number;
  source_currency: string;
  destination_currency: string;
  current_stage: PaymentStage;
  current_status: PaymentStatus;
  priority: PaymentPriority;
  payment_type?: PaymentType;
  system_rail?: string;
  anomaly_flag: boolean;
  anomaly_type?: AnomalyType;
  anomaly_severity?: AnomalySeverity;
  created_at: string;
  updated_at: string;
  // Phase 2
  sla_breach: boolean;
  delay_country?: string;
  delay_node?: string;
  bottleneck_stage?: string;
  total_processing_seconds?: number;
  recovered: boolean;
}

export interface PaymentEvent {
  id: string;
  payment_id: string;
  timestamp: string;
  stage: PaymentStage;
  event_type: EventType;
  status: PaymentStatus;
  message: string;
  details: Record<string, unknown>;
  actor: string;
  severity?: AnomalySeverity;
}

export interface PaymentLog {
  id: string;
  payment_id: string;
  timestamp: string;
  log_level: LogLevel;
  component: string;
  message: string;
  context: Record<string, unknown>;
}

export interface JourneyNode {
  country: string;
  node_name?: string;
  node_type?: string;
  is_origin: boolean;
  is_destination: boolean;
  is_intermediate: boolean;
  is_delayed: boolean;
  stage?: PaymentStage;
  status: string;
  lat?: number;
  lng?: number;
}

export interface PaymentJourney {
  payment_id: string;
  route_path: string[];
  route_type: RouteType;
  origin_country: string;
  destination_country: string;
  current_stage: PaymentStage;
  current_status: PaymentStatus;
  delay_node?: string;
  delay_country?: string;
  nodes: JourneyNode[];
  events: PaymentEvent[];
}

export interface Anomaly {
  id: string;
  payment_id: string;
  type: AnomalyType;
  title: string;
  description: string;
  severity: AnomalySeverity;
  detected_at: string;
  stage: PaymentStage;
  scope: AnomalyScope;
  country?: string;
  intermediary_bank?: string;
  status: AnomalyStatus;
  recommended_action?: string;
  confidence?: number;
  evidence_summary?: string;
  // Phase 2
  anomaly_code?: string;
  root_symptom?: string;
  probable_cause?: string;
  first_detected_at?: string;
  last_updated_at?: string;
  impacted_node?: string;
  corridor?: string;
  operational_impact_score?: number;
  action_status: ActionStatus;
  resolution_eta_minutes?: number;
  recurrence_count: number;
  client_impact_level?: string;
}

// ── Metrics / API Response Types ────────────────────────────────

export interface OverviewMetrics {
  total_payments: number;
  in_progress: number;
  completed: number;
  failed: number;
  on_hold: number;
  delayed: number;
  anomaly_count: number;
  severe_anomaly_count: number;
  sla_breach_count: number;
  recovered_count: number;
  average_processing_time_seconds: number;
  throughput_per_hour: number;
  anomaly_rate: number;
  success_rate: number;
  corridor_distribution: Record<string, number>;
  top_delayed_countries: Array<{ country: string; count: number }>;
  top_anomaly_types: Array<{ type: string; count: number }>;
  stage_distribution: Record<string, number>;
  stage_bottleneck_ranking: Array<{ stage: string; count: number }>;
  top_corridors_by_volume: Array<{ corridor: string; count: number }>;
  top_corridors_by_risk: Array<{ corridor: string; anomaly_count: number }>;
}

export interface SystemHealth {
  system_status: string;
  overall_health_score: number;
  queue_depth: number;
  queue_by_stage: Record<string, number>;
  processing_latency_ms: number;
  throughput_per_hour: number;
  anomaly_rate: number;
  success_rate: number;
  sla_breach_rate: number;
  route_health_index: number;
  route_health: Array<{
    corridor: string;
    total: number;
    failed: number;
    delayed: number;
    anomalies: number;
    sla_breaches: number;
  }>;
  compliance_health: {
    total_screened: number;
    sanctions_hits: number;
    pending_review: number;
    cleared: number;
    health_score: number;
  };
  settlement_health: {
    total_settled: number;
    pending_settlement: number;
    settlement_failures: number;
    recon_mismatches: number;
    health_score: number;
  };
  routing_health: {
    gateway_timeouts: number;
    missing_intermediary: number;
    route_failovers: number;
    health_score: number;
  };
  fx_health: {
    fx_delays: number;
    avg_fx_stage_seconds: number;
    health_score: number;
  };
}

// ── Phase 2 Types ────────────────────────────────────────────────

export interface StageTimingDetail {
  stage: string;
  duration_seconds: number;
  expected_seconds: number;
  delta_seconds: number;
  is_bottleneck: boolean;
  retry_count: number;
  queue_wait_seconds: number;
  entry_time?: string;
}

export interface ObservabilityPackage {
  payment_id: string;
  payment_reference: string;
  total_processing_seconds?: number;
  sla_breach: boolean;
  sla_breach_seconds?: number;
  bottleneck_stage?: string;
  bottleneck_node?: string;
  escalation_flag: boolean;
  operator_intervention: boolean;
  recovered: boolean;
  stage_detail: StageTimingDetail[];
  node_latency: Array<{
    node_name: string;
    country: string;
    node_type: string;
    avg_latency_ms: number;
    health_status: string;
    is_delay_node: boolean;
  }>;
  anomaly_summary?: Record<string, unknown>;
}

export interface StageMetrics {
  stage: string;
  total_count: number;
  avg_duration_seconds: number;
  expected_duration_seconds: number;
  failure_rate: number;
  retry_rate: number;
  sla_breach_count: number;
  bottleneck_count: number;
  on_hold_count: number;
  top_failure_reasons: string[];
}

export interface NodeHealth {
  node_id: string;
  bank_name: string;
  country: string;
  node_type: string;
  health_status: NodeHealthStatus;
  health_score: number;
  avg_latency_ms: number;
  p99_latency_ms: number;
  anomaly_count: number;
  delay_count: number;
  route_usage_count: number;
  impacted_payment_ids: string[];
  last_incident_at?: string;
  supported_rails: string[];
  risk_score: number;
}

export interface DelayHotspot {
  ranked_countries: Array<{ country: string; delay_count: number; anomaly_count: number; severity: string }>;
  ranked_nodes: Array<{ node: string; delay_count: number }>;
  ranked_corridors: Array<{ corridor: string; delay_count: number }>;
  stage_hotspots: Array<{ stage: string; bottleneck_count: number }>;
  severity_breakdown: Record<string, number>;
}

export interface ExceptionPattern {
  type_frequencies: Array<{ type: string; count: number; pct: number; avg_impact: number }>;
  stage_anomaly_map: Record<string, string[]>;
  corridor_anomaly_distribution: Array<{ corridor: string; anomaly_count: number; top_type: string; breakdown: Record<string, number> }>;
  recurring_signatures: Array<{ type: string; code?: string; recurrence_count: number; stage: string; corridor?: string; severity: string }>;
  trend_summary: {
    total_anomalies: number;
    open_count: number;
    resolved_count: number;
    high_impact_count: number;
    escalated_payments: number;
    top_type?: string;
    resolution_rate: number;
  };
}

export interface EnhancedCorridor {
  corridor: string;
  source_country: string;
  destination_country: string;
  payment_count: number;
  total_amount: number;
  anomaly_count: number;
  anomaly_rate: number;
  avg_processing_time_seconds: number;
  failure_count: number;
  failure_rate: number;
  sla_breach_count: number;
  dominant_status: PaymentStatus;
  top_anomaly_type?: string;
  risk_score: number;
}

export interface AdvancedSimulationRequest {
  source_country?: string;
  destination_country?: string;
  amount?: number;
  priority?: PaymentPriority;
  payment_type?: PaymentType;
  force_scenario?: string;
  inject_anomaly?: AnomalyType;
  inject_delay_node?: string;
}

export interface AdvancedSimulationResponse {
  payment: Payment;
  journey: PaymentJourney;
  events: PaymentEvent[];
  anomaly?: Anomaly;
  observability: ObservabilityPackage;
  summary: string;
  execution_explanation: string[];
}

export interface ReplayOverrideRequest {
  replay_mode?: string;
  override_anomaly?: AnomalyType;
  inject_delay_node?: string;
}

export interface ReplayComparisonResponse {
  original_payment_id: string;
  replayed_payment_id: string;
  original: Payment;
  replayed: Payment;
  original_anomaly?: Anomaly;
  replayed_anomaly?: Anomaly;
  original_events: PaymentEvent[];
  replayed_events: PaymentEvent[];
  original_observability: ObservabilityPackage;
  replayed_observability: ObservabilityPackage;
  status_changed: boolean;
  anomaly_changed: boolean;
  timing_delta_seconds?: number;
  outcome_summary: string;
  path_changed: boolean;
}

export interface MapFlow {
  id: string;
  origin_country: string;
  destination_country: string;
  route_countries: string[];
  origin_lat: number;
  origin_lng: number;
  destination_lat: number;
  destination_lng: number;
  route_coordinates: Array<{ lat: number; lng: number; country: string }>;
  status: PaymentStatus;
  delayed_node?: string;
  delayed_country?: string;
  anomaly_severity?: AnomalySeverity;
  payment_count: number;
  payment_ids: string[];
  corridor: string;
}

export interface CorridorData {
  corridor: string;
  source_country: string;
  destination_country: string;
  payment_count: number;
  total_amount: number;
  anomaly_count: number;
  avg_processing_time_seconds: number;
  dominant_status: PaymentStatus;
}

export interface CountryData {
  country: string;
  country_code: string;
  as_source_count: number;
  as_destination_count: number;
  as_intermediary_count: number;
  anomaly_count: number;
  delay_count: number;
}

export interface PaymentListResponse {
  payments: PaymentSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SimulationRequest {
  source_country?: string;
  destination_country?: string;
  amount?: number;
  payment_type?: PaymentType;
  inject_anomaly?: AnomalyType;
}

export interface SimulationResponse {
  payment: Payment;
  journey: PaymentJourney;
  events: PaymentEvent[];
  anomaly?: Anomaly;
  summary: string;
}

export interface HealthCheckResponse {
  status: string;
  payments_count: number;
  anomalies_count: number;
  nodes_count: number;
}

// ── Phase 3 AI Types ──────────────────────────────────────────────────────────

export interface ReasoningStep {
  step_number: number;
  label: string;
  observation: string;
  evidence: string;
  conclusion: string;
}

export interface AlternativeHypothesis {
  hypothesis: string;
  reason_rejected: string;
  confidence: number;
}

export interface RCAResult {
  payment_id: string;
  anomaly_ids: string[];
  primary_issue: string;
  issue_category: string;
  impacted_stage: string;
  impacted_node?: string;
  impacted_country?: string;
  confidence_score: number;
  reasoning_steps: ReasoningStep[];
  contributing_factors: string[];
  supporting_evidence: string[];
  likely_root_cause: string;
  alternative_hypotheses: AlternativeHypothesis[];
  customer_impact_summary: string;
  operations_impact_summary: string;
  recommended_next_checks: string[];
  resolution_priority: string;
}

export interface Recommendation {
  recommendation_id: string;
  payment_id: string;
  type: string;
  priority: string;
  title: string;
  description: string;
  rationale: string;
  confidence_score: number;
  execution_urgency: string;
  recommended_owner: string;
  estimated_impact: string;
  estimated_effort: string;
  preconditions: string[];
  risk_notes: string;
  related_evidence: string[];
  action_category: string;
}

export interface RepairAction {
  action_id: string;
  action_type: string;
  title: string;
  description: string;
  target_stage?: string;
  target_node?: string;
  applicability_rules: string[];
  estimated_success_probability: number;
  risk_level: string;
  requires_human_approval: boolean;
  blocking_conditions: string[];
  execution_notes: string;
}

export interface AgentOutput {
  agent_name: string;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  status: string;
  output_summary: string;
  key_findings: string[];
  data_consumed: string[];
}

export interface PolicyDecision {
  rule_name: string;
  triggered: boolean;
  action_taken: string;
  reason: string;
}

export interface AgentTrace {
  execution_id: string;
  payment_id: string;
  started_at: string;
  completed_at: string;
  total_duration_ms: number;
  agents_run: AgentOutput[];
  final_summary: string;
  reasoning_trace: string[];
  policy_decisions: PolicyDecision[];
  guardrail_notes: string[];
  mode: string;
}

export interface AISummary {
  payment_id: string;
  operator_summary: string;
  what_went_wrong: string;
  why_it_happened: string;
  what_to_do: string;
  risk_level: string;
  urgency: string;
  key_facts: string[];
  confidence: number;
}

export interface AIPackage {
  payment_id: string;
  rca: RCAResult;
  recommendations: Recommendation[];
  repair_actions: RepairAction[];
  ai_summary: AISummary;
  agent_trace: AgentTrace;
}

export interface PriorityQueueItem {
  payment_id: string;
  payment_reference: string;
  priority_score: number;
  urgency: string;
  reason: string;
  recommended_action: string;
  anomaly_type?: string;
  anomaly_severity?: string;
  sla_breach: boolean;
  corridor: string;
  amount: number;
}

export interface CorridorRiskInsight {
  corridor: string;
  risk_score: number;
  risk_level: string;
  primary_issue: string;
  anomaly_count: number;
  sla_breach_count: number;
  avg_delay_seconds: number;
  recommended_action: string;
  trend: string;
}

export interface NodeRiskWatchlistItem {
  node_id: string;
  bank_name: string;
  country: string;
  node_type: string;
  health_status: string;
  risk_score: number;
  anomaly_count: number;
  delay_count: number;
  avg_latency_ms: number;
  risk_reason: string;
  recommended_action: string;
}

export interface SystemAnomalyInsight {
  insight_id: string;
  category: string;
  title: string;
  description: string;
  affected_payments: number;
  affected_corridors: string[];
  severity: string;
  confidence: number;
  recommended_action: string;
}

export interface OperatorSummary {
  generated_at: string;
  headline: string;
  system_status: string;
  key_alerts: string[];
  top_issues: Array<{ issue: string; count: number; urgency: string }>;
  recommended_actions: string[];
  positive_signals: string[];
  watch_items: string[];
  ai_confidence: number;
}

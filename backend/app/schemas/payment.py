from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from ..domain.enums import (
    ActionStatus,
    AnomalySeverity,
    AnomalyScope,
    AnomalyStatus,
    AnomalyType,
    EventType,
    LogLevel,
    NodeHealthStatus,
    NodeType,
    PaymentPriority,
    PaymentStage,
    PaymentStatus,
    PaymentType,
    RouteType,
)


class PaymentSchema(BaseModel):
    id: str
    payment_reference: str
    source_client_name: str
    beneficiary_name: str
    source_country: str
    destination_country: str
    source_currency: str
    destination_currency: str
    amount: float
    fx_rate: float
    send_amount: float
    receive_amount: float
    corridor: str
    priority: PaymentPriority
    payment_type: PaymentType
    current_stage: PaymentStage
    current_status: PaymentStatus
    anomaly_flag: bool
    anomaly_type: AnomalyType | None = None
    anomaly_severity: AnomalySeverity | None = None
    anomaly_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    expected_completion_at: datetime | None = None
    actual_completion_at: datetime | None = None
    system_rail: str
    route_type: RouteType
    route_path: list[str]
    delay_node: str | None = None
    delay_country: str | None = None
    sanctions_hit: bool
    validation_error: bool
    gateway_timeout: bool
    reconciliation_break: bool
    metadata: dict[str, Any]
    # Phase 2
    stage_timings: dict[str, float] = {}
    stage_entry_times: dict[str, str] = {}
    expected_stage_durations: dict[str, float] = {}
    retry_counts: dict[str, int] = {}
    queue_wait_seconds: dict[str, float] = {}
    sla_breach: bool = False
    sla_breach_seconds: float | None = None
    bottleneck_stage: str | None = None
    bottleneck_node: str | None = None
    total_processing_seconds: float | None = None
    escalation_flag: bool = False
    operator_intervention: bool = False
    recovered: bool = False

    class Config:
        from_attributes = True


class PaymentSummarySchema(BaseModel):
    id: str
    payment_reference: str
    source_client_name: str
    beneficiary_name: str
    source_country: str
    destination_country: str
    corridor: str
    amount: float
    source_currency: str
    destination_currency: str
    current_stage: PaymentStage
    current_status: PaymentStatus
    priority: PaymentPriority
    payment_type: PaymentType | None = None
    system_rail: str | None = None
    anomaly_flag: bool
    anomaly_type: AnomalyType | None = None
    anomaly_severity: AnomalySeverity | None = None
    created_at: datetime
    updated_at: datetime
    # Phase 2
    sla_breach: bool = False
    delay_country: str | None = None
    delay_node: str | None = None
    bottleneck_stage: str | None = None
    total_processing_seconds: float | None = None
    recovered: bool = False


class PaymentEventSchema(BaseModel):
    id: str
    payment_id: str
    timestamp: datetime
    stage: PaymentStage
    event_type: EventType
    status: PaymentStatus
    message: str
    details: dict[str, Any]
    actor: str
    severity: AnomalySeverity | None = None

    class Config:
        from_attributes = True


class PaymentLogSchema(BaseModel):
    id: str
    payment_id: str
    timestamp: datetime
    log_level: LogLevel
    component: str
    message: str
    context: dict[str, Any]

    class Config:
        from_attributes = True


class AnomalySchema(BaseModel):
    id: str
    payment_id: str
    type: AnomalyType
    title: str
    description: str
    severity: AnomalySeverity
    detected_at: datetime
    stage: PaymentStage
    scope: AnomalyScope
    country: str | None = None
    intermediary_bank: str | None = None
    status: AnomalyStatus
    recommended_action: str | None = None
    confidence: float | None = None
    evidence_summary: str | None = None
    # Phase 2
    anomaly_code: str | None = None
    root_symptom: str | None = None
    probable_cause: str | None = None
    first_detected_at: datetime | None = None
    last_updated_at: datetime | None = None
    impacted_node: str | None = None
    corridor: str | None = None
    operational_impact_score: float | None = None
    action_status: ActionStatus = ActionStatus.OPEN
    resolution_eta_minutes: int | None = None
    recurrence_count: int = 0
    client_impact_level: str | None = None

    class Config:
        from_attributes = True


class IntermediaryNodeSchema(BaseModel):
    id: str
    bank_name: str
    country: str
    node_type: NodeType
    latency_score: float
    risk_score: float
    # Phase 2
    health_status: NodeHealthStatus = NodeHealthStatus.HEALTHY
    avg_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    anomaly_count: int = 0
    delay_count: int = 0
    route_usage_count: int = 0
    last_incident_at: datetime | None = None
    supported_rails: list[str] = []

    class Config:
        from_attributes = True


class PaymentJourneySchema(BaseModel):
    payment_id: str
    route_path: list[str]
    route_type: RouteType
    origin_country: str
    destination_country: str
    current_stage: PaymentStage
    current_status: PaymentStatus
    delay_node: str | None = None
    delay_country: str | None = None
    nodes: list[JourneyNodeSchema]
    events: list[PaymentEventSchema]


class JourneyNodeSchema(BaseModel):
    country: str
    node_name: str | None = None
    node_type: str | None = None
    is_origin: bool = False
    is_destination: bool = False
    is_intermediate: bool = False
    is_delayed: bool = False
    stage: PaymentStage | None = None
    status: str = "completed"
    lat: float | None = None
    lng: float | None = None


class PaymentListResponse(BaseModel):
    payments: list[PaymentSummarySchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class OverviewMetrics(BaseModel):
    total_payments: int
    in_progress: int
    completed: int
    failed: int
    on_hold: int
    anomaly_count: int
    severe_anomaly_count: int
    average_processing_time_seconds: float
    corridor_distribution: dict[str, int]
    top_delayed_countries: list[dict[str, Any]]
    top_anomaly_types: list[dict[str, Any]]
    stage_distribution: dict[str, int]


class SystemHealthSchema(BaseModel):
    system_status: str
    queue_depth: int
    processing_latency_ms: float
    anomaly_rate: float
    success_rate: float
    route_health: list[dict[str, Any]]
    compliance_health: dict[str, Any]
    settlement_health: dict[str, Any]


class MapFlowSchema(BaseModel):
    id: str
    origin_country: str
    destination_country: str
    route_countries: list[str]
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    route_coordinates: list[dict[str, Any]]
    status: PaymentStatus
    delayed_node: str | None = None
    delayed_country: str | None = None
    anomaly_severity: AnomalySeverity | None = None
    payment_count: int
    payment_ids: list[str]
    corridor: str


class CorridorSchema(BaseModel):
    corridor: str
    source_country: str
    destination_country: str
    payment_count: int
    total_amount: float
    anomaly_count: int
    avg_processing_time_seconds: float
    dominant_status: PaymentStatus


class CountrySchema(BaseModel):
    country: str
    country_code: str
    as_source_count: int
    as_destination_count: int
    as_intermediary_count: int
    anomaly_count: int
    delay_count: int


class SimulationRequest(BaseModel):
    source_country: str | None = None
    destination_country: str | None = None
    amount: float | None = None
    payment_type: PaymentType | None = None
    inject_anomaly: AnomalyType | None = None


class SimulationResponse(BaseModel):
    payment: PaymentSchema
    journey: PaymentJourneySchema
    events: list[PaymentEventSchema]
    anomaly: AnomalySchema | None = None
    summary: str


# ── Phase 2 Schemas ──────────────────────────────────────────────────────────

class StageTimingDetail(BaseModel):
    stage: str
    duration_seconds: float
    expected_seconds: float
    delta_seconds: float
    is_bottleneck: bool
    retry_count: int
    queue_wait_seconds: float
    entry_time: str | None = None


class ObservabilityPackage(BaseModel):
    payment_id: str
    payment_reference: str
    total_processing_seconds: float | None
    sla_breach: bool
    sla_breach_seconds: float | None
    bottleneck_stage: str | None
    bottleneck_node: str | None
    escalation_flag: bool
    operator_intervention: bool
    recovered: bool
    stage_detail: list[StageTimingDetail]
    node_latency: list[dict[str, Any]]
    anomaly_summary: dict[str, Any] | None


class StageMetricsSchema(BaseModel):
    stage: str
    total_count: int
    avg_duration_seconds: float
    expected_duration_seconds: float
    failure_rate: float
    retry_rate: float
    sla_breach_count: int
    bottleneck_count: int
    on_hold_count: int
    top_failure_reasons: list[str]


class NodeHealthSchema(BaseModel):
    node_id: str
    bank_name: str
    country: str
    node_type: str
    health_status: str
    health_score: float
    avg_latency_ms: float
    p99_latency_ms: float
    anomaly_count: int
    delay_count: int
    route_usage_count: int
    impacted_payment_ids: list[str]
    last_incident_at: datetime | None = None
    supported_rails: list[str] = []
    risk_score: float


class DelayHotspotSchema(BaseModel):
    ranked_countries: list[dict[str, Any]]
    ranked_nodes: list[dict[str, Any]]
    ranked_corridors: list[dict[str, Any]]
    stage_hotspots: list[dict[str, Any]]
    severity_breakdown: dict[str, int]


class ExceptionPatternSchema(BaseModel):
    type_frequencies: list[dict[str, Any]]
    stage_anomaly_map: dict[str, list[str]]
    corridor_anomaly_distribution: list[dict[str, Any]]
    recurring_signatures: list[dict[str, Any]]
    trend_summary: dict[str, Any]


class AdvancedSimulationRequest(BaseModel):
    source_country: str | None = None
    destination_country: str | None = None
    amount: float | None = None
    priority: PaymentPriority | None = None
    payment_type: PaymentType | None = None
    preferred_corridor: str | None = None
    force_scenario: str | None = None
    inject_delay_node: str | None = None
    inject_anomaly: AnomalyType | None = None


class ReplayOverrideRequest(BaseModel):
    replay_mode: str = "original"  # original | different_route | different_severity | injected_delay | injected_compliance
    override_anomaly: AnomalyType | None = None
    override_severity: AnomalySeverity | None = None
    inject_delay_node: str | None = None


class AdvancedSimulationResponse(BaseModel):
    payment: PaymentSchema
    journey: PaymentJourneySchema
    events: list[PaymentEventSchema]
    anomaly: AnomalySchema | None = None
    observability: ObservabilityPackage
    summary: str
    execution_explanation: list[str]


class ReplayComparisonResponse(BaseModel):
    original_payment_id: str
    replayed_payment_id: str
    original: PaymentSchema
    replayed: PaymentSchema
    original_anomaly: AnomalySchema | None = None
    replayed_anomaly: AnomalySchema | None = None
    original_events: list[PaymentEventSchema]
    replayed_events: list[PaymentEventSchema]
    original_observability: ObservabilityPackage
    replayed_observability: ObservabilityPackage
    status_changed: bool
    anomaly_changed: bool
    timing_delta_seconds: float | None
    outcome_summary: str
    path_changed: bool


class EnhancedOverviewMetrics(BaseModel):
    total_payments: int
    in_progress: int
    completed: int
    failed: int
    on_hold: int
    delayed: int
    anomaly_count: int
    severe_anomaly_count: int
    sla_breach_count: int
    recovered_count: int
    average_processing_time_seconds: float
    throughput_per_hour: float
    anomaly_rate: float
    success_rate: float
    corridor_distribution: dict[str, int]
    top_delayed_countries: list[dict[str, Any]]
    top_anomaly_types: list[dict[str, Any]]
    stage_distribution: dict[str, int]
    stage_bottleneck_ranking: list[dict[str, Any]]
    top_corridors_by_volume: list[dict[str, Any]]
    top_corridors_by_risk: list[dict[str, Any]]


class EnhancedCorridorSchema(BaseModel):
    corridor: str
    source_country: str
    destination_country: str
    payment_count: int
    total_amount: float
    anomaly_count: int
    anomaly_rate: float
    avg_processing_time_seconds: float
    failure_count: int
    failure_rate: float
    sla_breach_count: int
    dominant_status: PaymentStatus
    top_anomaly_type: str | None = None
    risk_score: float


class EnhancedSystemHealthSchema(BaseModel):
    system_status: str
    overall_health_score: float
    queue_depth: int
    queue_by_stage: dict[str, int]
    processing_latency_ms: float
    throughput_per_hour: float
    anomaly_rate: float
    success_rate: float
    sla_breach_rate: float
    route_health_index: float
    compliance_health: dict[str, Any]
    settlement_health: dict[str, Any]
    routing_health: dict[str, Any]
    fx_health: dict[str, Any]
    route_health: list[dict[str, Any]]

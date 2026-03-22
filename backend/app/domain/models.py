from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from .enums import (
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


def new_id() -> str:
    return str(uuid.uuid4())


class Payment:
    def __init__(
        self,
        *,
        id: str | None = None,
        payment_reference: str,
        source_client_name: str,
        beneficiary_name: str,
        source_country: str,
        destination_country: str,
        source_currency: str,
        destination_currency: str,
        amount: float,
        fx_rate: float,
        send_amount: float,
        receive_amount: float,
        corridor: str,
        priority: PaymentPriority,
        payment_type: PaymentType,
        current_stage: PaymentStage,
        current_status: PaymentStatus,
        anomaly_flag: bool = False,
        anomaly_type: AnomalyType | None = None,
        anomaly_severity: AnomalySeverity | None = None,
        anomaly_reason: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        expected_completion_at: datetime | None = None,
        actual_completion_at: datetime | None = None,
        system_rail: str = "SWIFT",
        route_type: RouteType = RouteType.DIRECT,
        route_path: list[str] | None = None,
        delay_node: str | None = None,
        delay_country: str | None = None,
        sanctions_hit: bool = False,
        validation_error: bool = False,
        gateway_timeout: bool = False,
        reconciliation_break: bool = False,
        metadata: dict[str, Any] | None = None,
        # Phase 2 observability fields
        stage_timings: dict[str, float] | None = None,
        stage_entry_times: dict[str, str] | None = None,
        expected_stage_durations: dict[str, float] | None = None,
        retry_counts: dict[str, int] | None = None,
        queue_wait_seconds: dict[str, float] | None = None,
        sla_breach: bool = False,
        sla_breach_seconds: float | None = None,
        bottleneck_stage: str | None = None,
        bottleneck_node: str | None = None,
        total_processing_seconds: float | None = None,
        escalation_flag: bool = False,
        operator_intervention: bool = False,
        recovered: bool = False,
    ):
        self.id = id or new_id()
        self.payment_reference = payment_reference
        self.source_client_name = source_client_name
        self.beneficiary_name = beneficiary_name
        self.source_country = source_country
        self.destination_country = destination_country
        self.source_currency = source_currency
        self.destination_currency = destination_currency
        self.amount = amount
        self.fx_rate = fx_rate
        self.send_amount = send_amount
        self.receive_amount = receive_amount
        self.corridor = corridor
        self.priority = priority
        self.payment_type = payment_type
        self.current_stage = current_stage
        self.current_status = current_status
        self.anomaly_flag = anomaly_flag
        self.anomaly_type = anomaly_type
        self.anomaly_severity = anomaly_severity
        self.anomaly_reason = anomaly_reason
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.expected_completion_at = expected_completion_at
        self.actual_completion_at = actual_completion_at
        self.system_rail = system_rail
        self.route_type = route_type
        self.route_path = route_path or []
        self.delay_node = delay_node
        self.delay_country = delay_country
        self.sanctions_hit = sanctions_hit
        self.validation_error = validation_error
        self.gateway_timeout = gateway_timeout
        self.reconciliation_break = reconciliation_break
        self.metadata = metadata or {}
        # Phase 2
        self.stage_timings = stage_timings or {}
        self.stage_entry_times = stage_entry_times or {}
        self.expected_stage_durations = expected_stage_durations or {}
        self.retry_counts = retry_counts or {}
        self.queue_wait_seconds = queue_wait_seconds or {}
        self.sla_breach = sla_breach
        self.sla_breach_seconds = sla_breach_seconds
        self.bottleneck_stage = bottleneck_stage
        self.bottleneck_node = bottleneck_node
        self.total_processing_seconds = total_processing_seconds
        self.escalation_flag = escalation_flag
        self.operator_intervention = operator_intervention
        self.recovered = recovered


class PaymentEvent:
    def __init__(
        self,
        *,
        id: str | None = None,
        payment_id: str,
        timestamp: datetime | None = None,
        stage: PaymentStage,
        event_type: EventType,
        status: PaymentStatus,
        message: str,
        details: dict[str, Any] | None = None,
        actor: str = "system",
        severity: AnomalySeverity | None = None,
    ):
        self.id = id or new_id()
        self.payment_id = payment_id
        self.timestamp = timestamp or datetime.utcnow()
        self.stage = stage
        self.event_type = event_type
        self.status = status
        self.message = message
        self.details = details or {}
        self.actor = actor
        self.severity = severity


class PaymentLog:
    def __init__(
        self,
        *,
        id: str | None = None,
        payment_id: str,
        timestamp: datetime | None = None,
        log_level: LogLevel,
        component: str,
        message: str,
        context: dict[str, Any] | None = None,
    ):
        self.id = id or new_id()
        self.payment_id = payment_id
        self.timestamp = timestamp or datetime.utcnow()
        self.log_level = log_level
        self.component = component
        self.message = message
        self.context = context or {}


class Anomaly:
    def __init__(
        self,
        *,
        id: str | None = None,
        payment_id: str,
        type: AnomalyType,
        title: str,
        description: str,
        severity: AnomalySeverity,
        detected_at: datetime | None = None,
        stage: PaymentStage,
        scope: AnomalyScope = AnomalyScope.PAYMENT,
        country: str | None = None,
        intermediary_bank: str | None = None,
        status: AnomalyStatus = AnomalyStatus.OPEN,
        recommended_action: str | None = None,
        confidence: float | None = None,
        evidence_summary: str | None = None,
        # Phase 2 fields
        anomaly_code: str | None = None,
        root_symptom: str | None = None,
        probable_cause: str | None = None,
        first_detected_at: datetime | None = None,
        last_updated_at: datetime | None = None,
        impacted_node: str | None = None,
        corridor: str | None = None,
        operational_impact_score: float | None = None,
        action_status: ActionStatus = ActionStatus.OPEN,
        resolution_eta_minutes: int | None = None,
        recurrence_count: int = 0,
        client_impact_level: str | None = None,
    ):
        self.id = id or new_id()
        self.payment_id = payment_id
        self.type = type
        self.title = title
        self.description = description
        self.severity = severity
        self.detected_at = detected_at or datetime.utcnow()
        self.stage = stage
        self.scope = scope
        self.country = country
        self.intermediary_bank = intermediary_bank
        self.status = status
        self.recommended_action = recommended_action
        self.confidence = confidence
        self.evidence_summary = evidence_summary
        # Phase 2
        self.anomaly_code = anomaly_code
        self.root_symptom = root_symptom
        self.probable_cause = probable_cause
        self.first_detected_at = first_detected_at or self.detected_at
        self.last_updated_at = last_updated_at or self.detected_at
        self.impacted_node = impacted_node
        self.corridor = corridor
        self.operational_impact_score = operational_impact_score
        self.action_status = action_status
        self.resolution_eta_minutes = resolution_eta_minutes
        self.recurrence_count = recurrence_count
        self.client_impact_level = client_impact_level


class IntermediaryNode:
    def __init__(
        self,
        *,
        id: str | None = None,
        bank_name: str,
        country: str,
        node_type: NodeType,
        latency_score: float = 0.0,
        risk_score: float = 0.0,
        # Phase 2 fields
        health_status: NodeHealthStatus = NodeHealthStatus.HEALTHY,
        avg_latency_ms: float = 0.0,
        p99_latency_ms: float = 0.0,
        anomaly_count: int = 0,
        delay_count: int = 0,
        route_usage_count: int = 0,
        last_incident_at: datetime | None = None,
        supported_rails: list[str] | None = None,
    ):
        self.id = id or new_id()
        self.bank_name = bank_name
        self.country = country
        self.node_type = node_type
        self.latency_score = latency_score
        self.risk_score = risk_score
        # Phase 2
        self.health_status = health_status
        self.avg_latency_ms = avg_latency_ms
        self.p99_latency_ms = p99_latency_ms
        self.anomaly_count = anomaly_count
        self.delay_count = delay_count
        self.route_usage_count = route_usage_count
        self.last_incident_at = last_incident_at
        self.supported_rails = supported_rails or []

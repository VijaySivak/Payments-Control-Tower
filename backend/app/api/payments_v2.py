"""Phase 2 Payment API routes - extends Phase 1 with observability + advanced sim."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..domain.enums import AnomalyType, AnomalySeverity, PaymentPriority, PaymentType
from ..domain.models import Payment
from ..repositories.memory_store import store
from ..schemas.payment import (
    AdvancedSimulationRequest,
    AdvancedSimulationResponse,
    AnomalySchema,
    ObservabilityPackage,
    PaymentEventSchema,
    PaymentJourneySchema,
    PaymentListResponse,
    PaymentLogSchema,
    PaymentSchema,
    PaymentSummarySchema,
    ReplayComparisonResponse,
    ReplayOverrideRequest,
    SimulationRequest,
    SimulationResponse,
)
from ..services.journey_service import journey_service
from ..services.observability_service import observability_service
from ..services.simulation_service import simulation_service

router = APIRouter()


def _to_schema(p: Payment) -> PaymentSchema:
    return PaymentSchema(
        id=p.id, payment_reference=p.payment_reference,
        source_client_name=p.source_client_name, beneficiary_name=p.beneficiary_name,
        source_country=p.source_country, destination_country=p.destination_country,
        source_currency=p.source_currency, destination_currency=p.destination_currency,
        amount=p.amount, fx_rate=p.fx_rate, send_amount=p.send_amount,
        receive_amount=p.receive_amount, corridor=p.corridor, priority=p.priority,
        payment_type=p.payment_type, current_stage=p.current_stage,
        current_status=p.current_status, anomaly_flag=p.anomaly_flag,
        anomaly_type=p.anomaly_type, anomaly_severity=p.anomaly_severity,
        anomaly_reason=p.anomaly_reason, created_at=p.created_at,
        updated_at=p.updated_at, expected_completion_at=p.expected_completion_at,
        actual_completion_at=p.actual_completion_at, system_rail=p.system_rail,
        route_type=p.route_type, route_path=p.route_path,
        delay_node=p.delay_node, delay_country=p.delay_country,
        sanctions_hit=p.sanctions_hit, validation_error=p.validation_error,
        gateway_timeout=p.gateway_timeout, reconciliation_break=p.reconciliation_break,
        metadata=p.metadata,
        stage_timings=p.stage_timings,
        stage_entry_times=p.stage_entry_times,
        expected_stage_durations=p.expected_stage_durations,
        retry_counts=p.retry_counts,
        queue_wait_seconds=p.queue_wait_seconds,
        sla_breach=p.sla_breach,
        sla_breach_seconds=p.sla_breach_seconds,
        bottleneck_stage=p.bottleneck_stage,
        bottleneck_node=p.bottleneck_node,
        total_processing_seconds=p.total_processing_seconds,
        escalation_flag=p.escalation_flag,
        operator_intervention=p.operator_intervention,
        recovered=p.recovered,
    )


def _to_summary(p: Payment) -> PaymentSummarySchema:
    return PaymentSummarySchema(
        id=p.id, payment_reference=p.payment_reference,
        source_client_name=p.source_client_name, beneficiary_name=p.beneficiary_name,
        source_country=p.source_country, destination_country=p.destination_country,
        corridor=p.corridor, amount=p.amount,
        source_currency=p.source_currency, destination_currency=p.destination_currency,
        current_stage=p.current_stage, current_status=p.current_status,
        priority=p.priority, payment_type=p.payment_type, system_rail=p.system_rail,
        anomaly_flag=p.anomaly_flag,
        anomaly_type=p.anomaly_type, anomaly_severity=p.anomaly_severity,
        created_at=p.created_at, updated_at=p.updated_at,
        sla_breach=p.sla_breach,
        delay_country=p.delay_country,
        delay_node=p.delay_node,
        bottleneck_stage=p.bottleneck_stage,
        total_processing_seconds=p.total_processing_seconds,
        recovered=p.recovered,
    )


@router.get("/payments", response_model=PaymentListResponse)
def list_payments(
    status: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    source_country: Optional[str] = Query(None),
    destination_country: Optional[str] = Query(None),
    anomaly_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    corridor: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    payment_type: Optional[str] = Query(None),
    sla_breach: Optional[bool] = Query(None),
    anomaly_only: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    payments, total = store.filter_payments(
        status=status, stage=stage, source_country=source_country,
        destination_country=destination_country, anomaly_type=anomaly_type,
        severity=severity, search=search, corridor=corridor, priority=priority,
        payment_type=payment_type, sla_breach=sla_breach, anomaly_only=anomaly_only,
        sort_by=sort_by, sort_dir=sort_dir, page=page, page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size
    return PaymentListResponse(
        payments=[_to_summary(p) for p in payments],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


@router.get("/payments/{payment_id}", response_model=PaymentSchema)
def get_payment(payment_id: str):
    payment = store.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return _to_schema(payment)


@router.get("/payments/{payment_id}/journey", response_model=PaymentJourneySchema)
def get_payment_journey(payment_id: str):
    journey = journey_service.get_journey(payment_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Payment not found")
    return journey


@router.get("/payments/{payment_id}/timeline", response_model=list[PaymentEventSchema])
def get_payment_timeline(payment_id: str):
    payment = store.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return journey_service.get_timeline(payment_id)


@router.get("/payments/{payment_id}/logs", response_model=list[PaymentLogSchema])
def get_payment_logs(
    payment_id: str,
    level: Optional[str] = Query(None),
    component: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    payment = store.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    logs = journey_service.get_logs(payment_id)
    if level:
        logs = [l for l in logs if l.log_level.value == level.upper()]
    if component:
        logs = [l for l in logs if l.component.lower() == component.lower()]
    if search:
        q = search.lower()
        logs = [l for l in logs if q in l.message.lower()]
    return logs


@router.get("/payments/{payment_id}/events", response_model=list[PaymentEventSchema])
def get_payment_events(payment_id: str):
    payment = store.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return journey_service.get_timeline(payment_id)


@router.get("/payments/{payment_id}/anomalies", response_model=list[AnomalySchema])
def get_payment_anomalies(payment_id: str):
    payment = store.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    anomalies = store.get_anomalies_for_payment(payment_id)
    return [
        AnomalySchema(
            id=a.id, payment_id=a.payment_id, type=a.type,
            title=a.title, description=a.description, severity=a.severity,
            detected_at=a.detected_at, stage=a.stage, scope=a.scope,
            country=a.country, intermediary_bank=a.intermediary_bank,
            status=a.status, recommended_action=a.recommended_action,
            confidence=a.confidence, evidence_summary=a.evidence_summary,
            anomaly_code=a.anomaly_code, root_symptom=a.root_symptom,
            probable_cause=a.probable_cause,
            first_detected_at=a.first_detected_at,
            last_updated_at=a.last_updated_at,
            impacted_node=a.impacted_node, corridor=a.corridor,
            operational_impact_score=a.operational_impact_score,
            action_status=a.action_status,
            resolution_eta_minutes=a.resolution_eta_minutes,
            recurrence_count=a.recurrence_count,
            client_impact_level=a.client_impact_level,
        )
        for a in anomalies
    ]


@router.get("/payments/{payment_id}/observability", response_model=ObservabilityPackage)
def get_payment_observability(payment_id: str):
    result = observability_service.get_payment_observability(payment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Payment not found")
    return result


@router.post("/payments/simulate", response_model=SimulationResponse)
def simulate_payment(request: SimulationRequest):
    return simulation_service.simulate(
        source_country=request.source_country,
        destination_country=request.destination_country,
        amount=request.amount,
        payment_type=request.payment_type,
        inject_anomaly=request.inject_anomaly,
    )


@router.post("/payments/simulate-advanced", response_model=AdvancedSimulationResponse)
def simulate_payment_advanced(request: AdvancedSimulationRequest):
    result = simulation_service.simulate_advanced(
        source_country=request.source_country,
        destination_country=request.destination_country,
        amount=request.amount,
        priority=request.priority,
        payment_type=request.payment_type,
        force_scenario=request.force_scenario,
        inject_anomaly=request.inject_anomaly,
        inject_delay_node=request.inject_delay_node,
    )
    return result


@router.post("/payments/{payment_id}/replay", response_model=SimulationResponse)
def replay_payment(payment_id: str):
    result = simulation_service.replay(payment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Payment not found")
    return result


@router.post("/payments/{payment_id}/replay-advanced", response_model=ReplayComparisonResponse)
def replay_payment_advanced(payment_id: str, request: ReplayOverrideRequest):
    result = simulation_service.replay_advanced(
        payment_id=payment_id,
        replay_mode=request.replay_mode,
        override_anomaly=request.override_anomaly,
        override_severity=request.override_severity,
        inject_delay_node=request.inject_delay_node,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Payment not found")
    return result

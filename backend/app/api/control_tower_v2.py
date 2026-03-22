"""Phase 2 Control Tower API - extends Phase 1 with observability analytics."""

from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Optional

from ..repositories.memory_store import store
from ..schemas.payment import (
    AnomalySchema,
    CountrySchema,
    DelayHotspotSchema,
    EnhancedCorridorSchema,
    EnhancedOverviewMetrics,
    EnhancedSystemHealthSchema,
    ExceptionPatternSchema,
    MapFlowSchema,
    NodeHealthSchema,
    PaymentSummarySchema,
    StageMetricsSchema,
)
from ..services.journey_service import journey_service
from ..services.metrics_service import metrics_service
from ..services.observability_service import observability_service

router = APIRouter(prefix="/control-tower")


def _anomaly_to_schema(a) -> AnomalySchema:
    return AnomalySchema(
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


# ── Legacy-compatible endpoints (Phase 1 preserved) ──────────────────────────

@router.get("/overview", response_model=EnhancedOverviewMetrics)
def get_overview():
    return metrics_service.get_enhanced_overview()


@router.get("/system-health", response_model=EnhancedSystemHealthSchema)
def get_system_health():
    return metrics_service.get_enhanced_system_health()


@router.get("/live-payments", response_model=list[PaymentSummarySchema])
def get_live_payments(limit: int = Query(20, ge=1, le=100)):
    from ..domain.enums import PaymentStatus
    payments = store.list_payments()
    active = [
        p for p in payments
        if p.current_status in (PaymentStatus.IN_PROGRESS, PaymentStatus.DELAYED, PaymentStatus.ON_HOLD, PaymentStatus.PENDING)
    ]
    active.sort(key=lambda p: p.updated_at, reverse=True)
    active = active[:limit]
    return [
        PaymentSummarySchema(
            id=p.id, payment_reference=p.payment_reference,
            source_client_name=p.source_client_name, beneficiary_name=p.beneficiary_name,
            source_country=p.source_country, destination_country=p.destination_country,
            corridor=p.corridor, amount=p.amount,
            source_currency=p.source_currency, destination_currency=p.destination_currency,
            current_stage=p.current_stage, current_status=p.current_status,
            priority=p.priority, payment_type=p.payment_type, system_rail=p.system_rail,
            anomaly_flag=p.anomaly_flag, anomaly_type=p.anomaly_type,
            anomaly_severity=p.anomaly_severity,
            created_at=p.created_at, updated_at=p.updated_at,
            sla_breach=p.sla_breach,
            delay_country=p.delay_country,
            delay_node=p.delay_node,
            bottleneck_stage=p.bottleneck_stage,
            total_processing_seconds=p.total_processing_seconds,
            recovered=p.recovered,
        )
        for p in active
    ]


@router.get("/anomalies", response_model=list[AnomalySchema])
def get_anomalies(
    severity: Optional[str] = Query(None),
    anomaly_type: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    corridor: Optional[str] = Query(None),
    node: Optional[str] = Query(None),
    action_status: Optional[str] = Query(None),
):
    anomalies = store.filter_anomalies(
        severity=severity, anomaly_type=anomaly_type,
        country=country, stage=stage, status=status,
        corridor=corridor, node=node, action_status=action_status,
    )
    return [_anomaly_to_schema(a) for a in anomalies]


@router.get("/corridors", response_model=list[EnhancedCorridorSchema])
def get_corridors():
    return metrics_service.get_enhanced_corridors()


@router.get("/countries", response_model=list[CountrySchema])
def get_countries():
    return metrics_service.get_countries()


@router.get("/map-flows", response_model=list[MapFlowSchema])
def get_map_flows():
    return journey_service.get_map_flows()


# ── Phase 2 new endpoints ─────────────────────────────────────────────────────

@router.get("/stage-metrics", response_model=list[StageMetricsSchema])
def get_stage_metrics():
    return observability_service.get_stage_metrics()


@router.get("/node-health", response_model=list[NodeHealthSchema])
def get_node_health():
    return observability_service.get_node_health()


@router.get("/delay-hotspots", response_model=DelayHotspotSchema)
def get_delay_hotspots():
    return observability_service.get_delay_hotspots()


@router.get("/exception-patterns", response_model=ExceptionPatternSchema)
def get_exception_patterns():
    return observability_service.get_exception_patterns()

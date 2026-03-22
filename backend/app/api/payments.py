"""Payment API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..domain.models import Payment
from ..repositories.memory_store import store
from ..schemas.payment import (
    AnomalySchema,
    PaymentEventSchema,
    PaymentJourneySchema,
    PaymentListResponse,
    PaymentLogSchema,
    PaymentSchema,
    PaymentSummarySchema,
    SimulationRequest,
    SimulationResponse,
)
from ..services.journey_service import journey_service
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
    )


def _to_summary(p: Payment) -> PaymentSummarySchema:
    return PaymentSummarySchema(
        id=p.id, payment_reference=p.payment_reference,
        source_client_name=p.source_client_name, beneficiary_name=p.beneficiary_name,
        source_country=p.source_country, destination_country=p.destination_country,
        corridor=p.corridor, amount=p.amount,
        source_currency=p.source_currency, destination_currency=p.destination_currency,
        current_stage=p.current_stage, current_status=p.current_status,
        priority=p.priority, anomaly_flag=p.anomaly_flag,
        anomaly_type=p.anomaly_type, anomaly_severity=p.anomaly_severity,
        created_at=p.created_at, updated_at=p.updated_at,
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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    payments, total = store.filter_payments(
        status=status, stage=stage, source_country=source_country,
        destination_country=destination_country, anomaly_type=anomaly_type,
        severity=severity, search=search, page=page, page_size=page_size,
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
def get_payment_logs(payment_id: str):
    payment = store.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return journey_service.get_logs(payment_id)


@router.get("/payments/{payment_id}/events", response_model=list[PaymentEventSchema])
def get_payment_events(payment_id: str):
    payment = store.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return journey_service.get_timeline(payment_id)


@router.post("/payments/simulate", response_model=SimulationResponse)
def simulate_payment(request: SimulationRequest):
    return simulation_service.simulate(
        source_country=request.source_country,
        destination_country=request.destination_country,
        amount=request.amount,
        payment_type=request.payment_type,
        inject_anomaly=request.inject_anomaly,
    )


@router.post("/payments/{payment_id}/replay", response_model=SimulationResponse)
def replay_payment(payment_id: str):
    result = simulation_service.replay(payment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Payment not found")
    return result

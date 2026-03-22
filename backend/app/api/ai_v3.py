"""Phase 3 AI API routes — RCA, recommendations, repair actions, agent trace, control tower AI."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any

from ..ai.rca_engine import rca_engine
from ..ai.recommendation_engine import recommendation_engine
from ..ai.repair_actions import repair_recommender
from ..ai.agent_orchestrator import agent_orchestrator
from ..ai.control_tower_ai import control_tower_ai
from ..schemas.ai_schemas import (
    AIPackage,
    AISummary,
    AgentTrace,
    CorridorRiskInsight,
    NodeRiskWatchlistItem,
    OperatorSummary,
    PriorityQueueItem,
    RCAResult,
    Recommendation,
    RepairAction,
    SystemAnomalyInsight,
)

router = APIRouter()


# ── Payment-level AI endpoints ────────────────────────────────────────────────

@router.get("/payments/{payment_id}/rca", response_model=RCAResult)
def get_payment_rca(payment_id: str):
    result = rca_engine.analyze_payment(payment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Payment not found or RCA unavailable")
    return result


@router.get("/payments/{payment_id}/recommendations", response_model=list[Recommendation])
def get_payment_recommendations(payment_id: str):
    from ..repositories.memory_store import store
    if not store.get_payment(payment_id):
        raise HTTPException(status_code=404, detail="Payment not found")
    return recommendation_engine.generate(payment_id)


@router.get("/payments/{payment_id}/repair-actions", response_model=list[RepairAction])
def get_payment_repair_actions(payment_id: str):
    from ..repositories.memory_store import store
    payment = store.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Use RCA to determine issue category
    rca = rca_engine.analyze_payment(payment_id)
    category = rca.issue_category if rca else "OPERATIONAL"
    return repair_recommender.get_repair_actions(payment_id, category)


@router.get("/payments/{payment_id}/agent-trace", response_model=AgentTrace)
def get_payment_agent_trace(payment_id: str):
    package = agent_orchestrator.run(payment_id)
    if not package:
        raise HTTPException(status_code=404, detail="Payment not found or agent trace unavailable")
    return package.agent_trace


@router.get("/payments/{payment_id}/ai-summary", response_model=AISummary)
def get_payment_ai_summary(payment_id: str):
    package = agent_orchestrator.run(payment_id)
    if not package:
        raise HTTPException(status_code=404, detail="Payment not found or AI summary unavailable")
    return package.ai_summary


@router.get("/payments/{payment_id}/ai-package", response_model=AIPackage)
def get_payment_ai_package(payment_id: str):
    """Combined endpoint: RCA + recommendations + repair actions + summary + agent trace."""
    package = agent_orchestrator.run(payment_id)
    if not package:
        raise HTTPException(status_code=404, detail="Payment not found or AI analysis unavailable")
    return package


# ── Anomaly-level AI endpoints ────────────────────────────────────────────────

@router.get("/anomalies/{anomaly_id}/rca", response_model=RCAResult)
def get_anomaly_rca(anomaly_id: str):
    result = rca_engine.analyze_anomaly(anomaly_id)
    if not result:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return result


@router.get("/anomalies/{anomaly_id}/recommendations", response_model=list[Recommendation])
def get_anomaly_recommendations(anomaly_id: str):
    recs = recommendation_engine.generate_for_anomaly(anomaly_id)
    if recs is None:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return recs


# ── Control Tower AI endpoints ─────────────────────────────────────────────────

@router.get("/ai/priority-queue", response_model=list[PriorityQueueItem])
def get_priority_queue(limit: int = 15):
    return control_tower_ai.get_priority_queue(limit=limit)


@router.get("/ai/system-anomaly-insights", response_model=list[SystemAnomalyInsight])
def get_system_anomaly_insights():
    return control_tower_ai.get_system_anomaly_insights()


@router.get("/ai/corridor-risk-insights", response_model=list[CorridorRiskInsight])
def get_corridor_risk_insights():
    return control_tower_ai.get_corridor_risk_insights()


@router.get("/ai/node-risk-watchlist", response_model=list[NodeRiskWatchlistItem])
def get_node_risk_watchlist():
    return control_tower_ai.get_node_risk_watchlist()


@router.get("/ai/operator-summary", response_model=OperatorSummary)
def get_operator_summary():
    return control_tower_ai.get_operator_summary()

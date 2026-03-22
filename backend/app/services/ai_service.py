"""Placeholder AI service interfaces for Phase 2/3 integration.

These interfaces define the contracts for future AI modules:
- Root Cause Analysis (RCA) engine
- Recommendation engine
- Agent orchestrator

Phase 1 provides stub implementations. Phase 2/3 will replace with real LLM-backed logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RCAEngine(ABC):
    """Root Cause Analysis engine interface."""

    @abstractmethod
    def analyze(self, payment_id: str, anomaly_id: str) -> dict[str, Any]:
        """Analyze root cause of an anomaly for a given payment."""
        ...

    @abstractmethod
    def get_causal_chain(self, anomaly_id: str) -> list[dict[str, Any]]:
        """Get the causal chain leading to the anomaly."""
        ...


class RecommendationEngine(ABC):
    """Recommendation engine interface."""

    @abstractmethod
    def get_recommendations(self, payment_id: str) -> list[dict[str, Any]]:
        """Get action recommendations for a payment issue."""
        ...

    @abstractmethod
    def get_corridor_recommendations(self, corridor: str) -> list[dict[str, Any]]:
        """Get optimization recommendations for a corridor."""
        ...


class AgentOrchestrator(ABC):
    """Agent orchestrator interface for multi-step AI reasoning."""

    @abstractmethod
    def run_investigation(self, anomaly_id: str) -> dict[str, Any]:
        """Run an automated investigation for an anomaly."""
        ...

    @abstractmethod
    def get_trace(self, investigation_id: str) -> list[dict[str, Any]]:
        """Get the agent trace/steps for an investigation."""
        ...


# ── Stub implementations for Phase 1 ───────────────────────────


class StubRCAEngine(RCAEngine):
    def analyze(self, payment_id: str, anomaly_id: str) -> dict[str, Any]:
        return {
            "payment_id": payment_id,
            "anomaly_id": anomaly_id,
            "root_cause": "Analysis pending - AI module not yet integrated",
            "confidence": 0.0,
            "contributing_factors": [],
            "phase": "Phase 2/3 will provide real RCA",
        }

    def get_causal_chain(self, anomaly_id: str) -> list[dict[str, Any]]:
        return [{"step": 1, "description": "Causal chain analysis pending", "phase": "Phase 2/3"}]


class StubRecommendationEngine(RecommendationEngine):
    def get_recommendations(self, payment_id: str) -> list[dict[str, Any]]:
        return [{
            "id": "placeholder",
            "action": "AI recommendations will be available in Phase 2/3",
            "priority": "medium",
            "confidence": 0.0,
        }]

    def get_corridor_recommendations(self, corridor: str) -> list[dict[str, Any]]:
        return [{
            "id": "placeholder",
            "corridor": corridor,
            "action": "Corridor optimization insights coming in Phase 2/3",
            "confidence": 0.0,
        }]


class StubAgentOrchestrator(AgentOrchestrator):
    def run_investigation(self, anomaly_id: str) -> dict[str, Any]:
        return {
            "investigation_id": "stub",
            "anomaly_id": anomaly_id,
            "status": "pending",
            "message": "Automated investigation will be available in Phase 3",
        }

    def get_trace(self, investigation_id: str) -> list[dict[str, Any]]:
        return [{"step": 1, "action": "Agent tracing pending", "phase": "Phase 3"}]


# Singleton instances - swap these for real implementations in Phase 2/3
rca_engine: RCAEngine = StubRCAEngine()
recommendation_engine: RecommendationEngine = StubRecommendationEngine()
agent_orchestrator: AgentOrchestrator = StubAgentOrchestrator()

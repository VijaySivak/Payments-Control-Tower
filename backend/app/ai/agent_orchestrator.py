"""
Agent Orchestrator — lightweight multi-agent pipeline for explainable AI analysis.

Agents run in sequence:
  Intake → Context → RCA → Recommendation → Repair → Guardrail → Summary

Each agent records its observations, key findings, and timing.
The full trace is returned alongside the final outputs.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from ..schemas.ai_schemas import (
    AgentOutput,
    AgentTrace,
    AISummary,
    AIPackage,
    PolicyDecision,
    RCAResult,
    Recommendation,
    RepairAction,
)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


class IntakeAgent:
    """Collects payment, anomaly, logs, events, observability data."""

    def run(self, payment_id: str) -> tuple[AgentOutput, dict[str, Any]]:
        from ..repositories.memory_store import store
        from ..services.journey_service import journey_service
        from ..services.observability_service import observability_service

        t0 = time.perf_counter()
        started = _ts()
        ctx: dict[str, Any] = {}

        payment = store.get_payment(payment_id)
        anomalies = store.get_anomalies_for_payment(payment_id) if payment else []
        timeline = journey_service.get_timeline(payment_id) if payment else []
        logs = journey_service.get_logs(payment_id) if payment else []
        obs = observability_service.get_payment_observability(payment_id)

        if payment:
            ctx["payment"] = payment
            ctx["anomalies"] = anomalies
            ctx["timeline"] = timeline
            ctx["logs"] = logs
            ctx["observability"] = obs

        findings = [
            f"Payment found: {bool(payment)}",
            f"Anomalies: {len(anomalies)}",
            f"Events: {len(timeline)}",
            f"Logs: {len(logs)}",
            f"Observability data: {bool(obs)}",
        ]

        return AgentOutput(
            agent_name="IntakeAgent",
            started_at=started,
            completed_at=_ts(),
            duration_ms=_ms(t0),
            status="SUCCESS" if payment else "ERROR",
            output_summary=f"Collected context for payment {payment_id[:12]}...",
            key_findings=findings,
            data_consumed=["payments_store", "anomalies_store", "journey_service", "observability_service"],
        ), ctx


class ContextAgent:
    """Aggregates corridor, country, node, system-health context."""

    def run(self, ctx: dict[str, Any]) -> tuple[AgentOutput, dict[str, Any]]:
        from ..services.metrics_service import metrics_service
        from ..services.observability_service import observability_service

        t0 = time.perf_counter()
        started = _ts()

        payment = ctx.get("payment")
        if not payment:
            return AgentOutput(
                agent_name="ContextAgent", started_at=started, completed_at=_ts(),
                duration_ms=_ms(t0), status="SKIPPED",
                output_summary="Skipped — no payment context available",
                key_findings=[], data_consumed=[],
            ), ctx

        try:
            node_health = observability_service.get_node_health()
            delay_hotspots = observability_service.get_delay_hotspots()
            corridor_nodes = [n for n in node_health if n.country == payment.source_country or n.country == payment.destination_country]
            degraded = [n for n in corridor_nodes if n.health_status != "HEALTHY"]

            ctx["corridor_health"] = {
                "corridor": payment.corridor,
                "degraded_nodes": degraded,
                "delay_hotspot": any(
                    c.country == payment.destination_country
                    for c in delay_hotspots.ranked_countries[:5]
                ) if delay_hotspots else False,
            }

            findings = [
                f"Corridor: {payment.corridor}",
                f"Corridor nodes checked: {len(corridor_nodes)}",
                f"Degraded nodes on route: {len(degraded)}",
                f"Destination country in top-5 delay hotspots: {ctx['corridor_health']['delay_hotspot']}",
            ]
        except Exception as e:
            findings = [f"Context enrichment partial: {str(e)[:60]}"]

        return AgentOutput(
            agent_name="ContextAgent",
            started_at=started, completed_at=_ts(), duration_ms=_ms(t0),
            status="SUCCESS",
            output_summary=f"Context enriched for corridor {payment.corridor}",
            key_findings=findings,
            data_consumed=["node_health_service", "delay_hotspot_service"],
        ), ctx


class RCAAgent:
    """Produces structured root cause reasoning."""

    def run(self, ctx: dict[str, Any]) -> tuple[AgentOutput, dict[str, Any]]:
        from .rca_engine import rca_engine

        t0 = time.perf_counter()
        started = _ts()

        payment = ctx.get("payment")
        if not payment:
            return AgentOutput(
                agent_name="RCAAgent", started_at=started, completed_at=_ts(),
                duration_ms=_ms(t0), status="SKIPPED",
                output_summary="Skipped — no payment context",
                key_findings=[], data_consumed=[],
            ), ctx

        rca: RCAResult = rca_engine._run_rca(
            payment, ctx.get("anomalies", []), ctx.get("logs", [])
        )
        ctx["rca"] = rca

        findings = [
            f"Primary issue: {rca.primary_issue[:80]}",
            f"Category: {rca.issue_category}",
            f"Confidence: {rca.confidence_score * 100:.0f}%",
            f"Priority: {rca.resolution_priority}",
            f"Reasoning steps: {len(rca.reasoning_steps)}",
        ]

        return AgentOutput(
            agent_name="RCAAgent",
            started_at=started, completed_at=_ts(), duration_ms=_ms(t0),
            status="SUCCESS",
            output_summary=f"RCA complete: {rca.issue_category} — {rca.resolution_priority} priority",
            key_findings=findings,
            data_consumed=["payment_data", "anomaly_data", "observability_data"],
        ), ctx


class RecommendationAgent:
    """Produces action recommendations grounded in RCA."""

    def run(self, ctx: dict[str, Any]) -> tuple[AgentOutput, dict[str, Any]]:
        from .recommendation_engine import recommendation_engine

        t0 = time.perf_counter()
        started = _ts()

        payment = ctx.get("payment")
        rca: RCAResult | None = ctx.get("rca")

        if not payment or not rca:
            return AgentOutput(
                agent_name="RecommendationAgent", started_at=started, completed_at=_ts(),
                duration_ms=_ms(t0), status="SKIPPED",
                output_summary="Skipped — missing payment or RCA context",
                key_findings=[], data_consumed=[],
            ), ctx

        recs = recommendation_engine.generate(payment.id, rca)
        ctx["recommendations"] = recs

        findings = [
            f"Recommendations generated: {len(recs)}",
        ] + [f"  [{r.priority}] {r.title[:60]}" for r in recs[:3]]

        return AgentOutput(
            agent_name="RecommendationAgent",
            started_at=started, completed_at=_ts(), duration_ms=_ms(t0),
            status="SUCCESS",
            output_summary=f"{len(recs)} recommendations generated",
            key_findings=findings,
            data_consumed=["rca_output", "payment_context"],
        ), ctx


class RepairAgent:
    """Generates repair action playbooks."""

    def run(self, ctx: dict[str, Any]) -> tuple[AgentOutput, dict[str, Any]]:
        from .repair_actions import repair_recommender

        t0 = time.perf_counter()
        started = _ts()

        payment = ctx.get("payment")
        rca: RCAResult | None = ctx.get("rca")

        if not payment:
            return AgentOutput(
                agent_name="RepairAgent", started_at=started, completed_at=_ts(),
                duration_ms=_ms(t0), status="SKIPPED",
                output_summary="Skipped — no payment context",
                key_findings=[], data_consumed=[],
            ), ctx

        issue_category = rca.issue_category if rca else "OPERATIONAL"
        actions = repair_recommender.get_repair_actions(payment.id, issue_category)
        ctx["repair_actions"] = actions

        return AgentOutput(
            agent_name="RepairAgent",
            started_at=started, completed_at=_ts(), duration_ms=_ms(t0),
            status="SUCCESS",
            output_summary=f"{len(actions)} repair actions identified",
            key_findings=[f"Action: {a.action_type} (risk: {a.risk_level})" for a in actions[:3]],
            data_consumed=["rca_output", "payment_data"],
        ), ctx


class GuardrailAgent:
    """Applies policy checks to recommendations and repair actions."""

    def run(self, ctx: dict[str, Any]) -> tuple[AgentOutput, dict[str, Any]]:
        from .guardrail_engine import guardrail_engine

        t0 = time.perf_counter()
        started = _ts()

        payment = ctx.get("payment")
        recs: list[Recommendation] = ctx.get("recommendations", [])
        actions: list[RepairAction] = ctx.get("repair_actions", [])

        decisions: list[PolicyDecision] = []

        filtered_recs, rec_decisions = guardrail_engine.check_recommendations(payment, recs)
        filtered_actions, action_decisions = guardrail_engine.check_repair_actions(payment, actions)
        decisions = rec_decisions + action_decisions

        ctx["recommendations"] = filtered_recs
        ctx["repair_actions"] = filtered_actions
        ctx["policy_decisions"] = decisions
        ctx["guardrail_notes"] = guardrail_engine.build_guardrail_notes(decisions)

        triggered = [d for d in decisions if d.triggered]

        return AgentOutput(
            agent_name="GuardrailAgent",
            started_at=started, completed_at=_ts(), duration_ms=_ms(t0),
            status="SUCCESS",
            output_summary=f"Policy check complete: {len(triggered)} rules triggered",
            key_findings=[f"[{d.rule_name}] {d.action_taken}" for d in triggered],
            data_consumed=["recommendations", "repair_actions", "payment_data"],
        ), ctx


class SummaryAgent:
    """Produces an operator-facing natural-language summary."""

    def run(self, ctx: dict[str, Any]) -> tuple[AgentOutput, dict[str, Any]]:
        t0 = time.perf_counter()
        started = _ts()

        payment = ctx.get("payment")
        rca: RCAResult | None = ctx.get("rca")
        recs: list[Recommendation] = ctx.get("recommendations", [])

        if not payment or not rca:
            return AgentOutput(
                agent_name="SummaryAgent", started_at=started, completed_at=_ts(),
                duration_ms=_ms(t0), status="SKIPPED",
                output_summary="Skipped — insufficient context",
                key_findings=[], data_consumed=[],
            ), ctx

        top_rec = recs[0] if recs else None

        urgency = "IMMEDIATE" if payment.sla_breach else (
            "HIGH" if rca.resolution_priority in ("CRITICAL", "HIGH") else "MEDIUM"
        )

        what_went_wrong = rca.primary_issue
        why_it_happened = rca.likely_root_cause[:200] + ("..." if len(rca.likely_root_cause) > 200 else "")
        what_to_do = top_rec.title if top_rec else "Manual review by operations team recommended."

        operator_summary = (
            f"Payment {payment.payment_reference} ({payment.corridor}, "
            f"{payment.amount:,.0f} {payment.source_currency}) is experiencing a "
            f"{rca.issue_category.lower()} exception at the {rca.impacted_stage} stage. "
            f"{rca.primary_issue} Confidence: {rca.confidence_score * 100:.0f}%. "
            f"{'SLA breached. ' if payment.sla_breach else ''}"
            f"Recommended action: {what_to_do}"
        )

        key_facts = [
            f"Payment: {payment.payment_reference}",
            f"Corridor: {payment.corridor}",
            f"Amount: {payment.amount:,.0f} {payment.source_currency}",
            f"Stage: {rca.impacted_stage}",
            f"Category: {rca.issue_category}",
        ]
        if payment.sla_breach:
            key_facts.append("⚠ SLA breached")
        if payment.bottleneck_stage:
            key_facts.append(f"Bottleneck: {payment.bottleneck_stage}")

        summary = AISummary(
            payment_id=payment.id,
            operator_summary=operator_summary,
            what_went_wrong=what_went_wrong,
            why_it_happened=why_it_happened,
            what_to_do=what_to_do,
            risk_level=rca.resolution_priority,
            urgency=urgency,
            key_facts=key_facts,
            confidence=rca.confidence_score,
        )
        ctx["ai_summary"] = summary

        return AgentOutput(
            agent_name="SummaryAgent",
            started_at=started, completed_at=_ts(), duration_ms=_ms(t0),
            status="SUCCESS",
            output_summary="Operator summary generated",
            key_findings=[
                f"Risk: {rca.resolution_priority}",
                f"Urgency: {urgency}",
                f"Summary length: {len(operator_summary)} chars",
            ],
            data_consumed=["rca_output", "recommendations", "payment_data"],
        ), ctx


class AgentOrchestrator:
    """
    Runs the full agent pipeline and returns a complete AI package.
    Mode: DETERMINISTIC (always works without LLM).
    """

    def __init__(self):
        self.agents = [
            IntakeAgent(),
            ContextAgent(),
            RCAAgent(),
            RecommendationAgent(),
            RepairAgent(),
            GuardrailAgent(),
            SummaryAgent(),
        ]

    def run(self, payment_id: str) -> AIPackage | None:
        execution_id = str(uuid.uuid4())
        pipeline_start = _ts()
        t0 = time.perf_counter()

        ctx: dict[str, Any] = {"payment_id": payment_id}
        agent_outputs: list[AgentOutput] = []
        reasoning_trace: list[str] = []

        for agent in self.agents:
            try:
                output, ctx = agent.run(ctx) if not isinstance(agent, IntakeAgent) else agent.run(payment_id)  # type: ignore[call-arg]
            except Exception as e:
                output = AgentOutput(
                    agent_name=type(agent).__name__,
                    started_at=_ts(), completed_at=_ts(), duration_ms=0,
                    status="ERROR",
                    output_summary=f"Agent failed: {str(e)[:100]}",
                    key_findings=[], data_consumed=[],
                )
            agent_outputs.append(output)
            for finding in output.key_findings:
                reasoning_trace.append(f"[{output.agent_name}] {finding}")

        if not ctx.get("payment"):
            return None

        rca: RCAResult | None = ctx.get("rca")
        recs: list[Recommendation] = ctx.get("recommendations", [])
        actions: list[RepairAction] = ctx.get("repair_actions", [])
        summary: AISummary | None = ctx.get("ai_summary")
        decisions: list[PolicyDecision] = ctx.get("policy_decisions", [])
        guardrail_notes: list[str] = ctx.get("guardrail_notes", [])

        if not rca or not summary:
            return None

        trace = AgentTrace(
            execution_id=execution_id,
            payment_id=payment_id,
            started_at=pipeline_start,
            completed_at=_ts(),
            total_duration_ms=_ms(t0),
            agents_run=agent_outputs,
            final_summary=summary.operator_summary,
            reasoning_trace=reasoning_trace,
            policy_decisions=decisions,
            guardrail_notes=guardrail_notes,
            mode="DETERMINISTIC",
        )

        return AIPackage(
            payment_id=payment_id,
            rca=rca,
            recommendations=recs,
            repair_actions=actions,
            ai_summary=summary,
            agent_trace=trace,
        )

    def run_for_anomaly(self, anomaly_id: str) -> dict | None:
        from ..repositories.memory_store import store

        all_anomalies = store.list_anomalies()
        anomaly = next((a for a in all_anomalies if a.id == anomaly_id), None)
        if not anomaly:
            return None

        from .rca_engine import rca_engine
        from .recommendation_engine import recommendation_engine

        rca = rca_engine.analyze_anomaly(anomaly_id)
        recs = recommendation_engine.generate_for_anomaly(anomaly_id)
        return {"rca": rca, "recommendations": recs}


agent_orchestrator = AgentOrchestrator()

"""
Control Tower AI — system-level intelligence views.
Operator priority queue, corridor risk, node watchlist, system anomaly insights,
and operator summary generation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..schemas.ai_schemas import (
    CorridorRiskInsight,
    NodeRiskWatchlistItem,
    OperatorSummary,
    PriorityQueueItem,
    SystemAnomalyInsight,
)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


class ControlTowerAI:
    """System-level AI views built from deterministic analysis of live data."""

    # ── Priority Queue ─────────────────────────────────────────────────────────

    def get_priority_queue(self, limit: int = 15) -> list[PriorityQueueItem]:
        from ..repositories.memory_store import store
        from ..domain.enums import PaymentStatus, AnomalySeverity

        payments = store.list_payments()
        items: list[tuple[float, PriorityQueueItem]] = []

        for p in payments:
            if p.current_status not in (
                PaymentStatus.IN_PROGRESS, PaymentStatus.DELAYED,
                PaymentStatus.ON_HOLD, PaymentStatus.FAILED
            ):
                continue

            score = 0.0
            reason_parts = []
            recommended_action = "Monitor progress"

            # SLA breach
            if p.sla_breach:
                score += 40
                reason_parts.append("SLA breached")
                recommended_action = "Immediate ops escalation required"

            # Anomaly severity
            sev_scores = {
                AnomalySeverity.CRITICAL: 30,
                AnomalySeverity.HIGH: 20,
                AnomalySeverity.MEDIUM: 10,
                AnomalySeverity.LOW: 3,
            }
            if p.anomaly_severity:
                score += sev_scores.get(p.anomaly_severity, 0)
                reason_parts.append(f"{p.anomaly_severity.value} anomaly")
                if not p.sla_breach:
                    recommended_action = "Investigate anomaly and review recommended actions"

            # Amount weight
            if p.amount > 1_000_000:
                score += 15
                reason_parts.append("High-value payment (>1M)")
            elif p.amount > 500_000:
                score += 8
                reason_parts.append("Large payment (>500k)")

            # Escalation
            if p.escalation_flag:
                score += 12
                reason_parts.append("Escalation flag set")

            # Retries
            if p.retry_counts and any(v >= 2 for v in p.retry_counts.values()):
                score += 8
                reason_parts.append("Multiple retries detected")

            # Priority
            from ..domain.enums import PaymentPriority
            prio_scores = {
                PaymentPriority.CRITICAL: 15,
                PaymentPriority.HIGH: 8,
                PaymentPriority.MEDIUM: 3,
                PaymentPriority.LOW: 0,
            }
            score += prio_scores.get(p.priority, 0)

            if score > 5:  # Only include items that need attention
                urgency = "CRITICAL" if score >= 50 else "HIGH" if score >= 30 else "MEDIUM"
                items.append((score, PriorityQueueItem(
                    payment_id=p.id,
                    payment_reference=p.payment_reference,
                    priority_score=round(score, 1),
                    urgency=urgency,
                    reason=", ".join(reason_parts) if reason_parts else "Operational monitoring",
                    recommended_action=recommended_action,
                    anomaly_type=p.anomaly_type.value if p.anomaly_type else None,
                    anomaly_severity=p.anomaly_severity.value if p.anomaly_severity else None,
                    sla_breach=p.sla_breach,
                    corridor=p.corridor,
                    amount=p.amount,
                )))

        items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in items[:limit]]

    # ── Corridor Risk Insights ─────────────────────────────────────────────────

    def get_corridor_risk_insights(self) -> list[CorridorRiskInsight]:
        from ..repositories.memory_store import store

        payments = store.list_payments()
        corridors: dict[str, dict] = {}

        for p in payments:
            if p.corridor not in corridors:
                corridors[p.corridor] = {
                    "total": 0, "anomalies": 0, "sla_breaches": 0,
                    "total_delay": 0.0, "delay_count": 0,
                }
            c = corridors[p.corridor]
            c["total"] += 1
            if p.anomaly_flag:
                c["anomalies"] += 1
            if p.sla_breach:
                c["sla_breaches"] += 1
            if p.total_processing_seconds:
                c["total_delay"] += p.total_processing_seconds
                c["delay_count"] += 1

        insights: list[CorridorRiskInsight] = []
        for corridor, stats in corridors.items():
            if stats["total"] < 2:
                continue

            anomaly_rate = stats["anomalies"] / stats["total"]
            sla_rate = stats["sla_breaches"] / stats["total"]
            avg_delay = stats["total_delay"] / max(stats["delay_count"], 1)

            risk_score = (anomaly_rate * 50) + (sla_rate * 30) + min(avg_delay / 3600, 20)
            risk_level = "CRITICAL" if risk_score > 40 else "HIGH" if risk_score > 25 else "MEDIUM" if risk_score > 10 else "LOW"

            if stats["anomalies"] > stats["sla_breaches"]:
                primary_issue = "Elevated anomaly rate on corridor"
                recommended = "Review anomaly patterns and consider corridor health check"
            elif stats["sla_breaches"] > 0:
                primary_issue = "SLA compliance degraded on corridor"
                recommended = "Escalate to operations for corridor SLA review"
            else:
                primary_issue = "Processing delays observed"
                recommended = "Monitor corridor performance — no immediate action needed"

            insights.append(CorridorRiskInsight(
                corridor=corridor,
                risk_score=round(risk_score, 1),
                risk_level=risk_level,
                primary_issue=primary_issue,
                anomaly_count=stats["anomalies"],
                sla_breach_count=stats["sla_breaches"],
                avg_delay_seconds=round(avg_delay, 1),
                recommended_action=recommended,
                trend="STABLE",
            ))

        insights.sort(key=lambda x: x.risk_score, reverse=True)
        return insights[:10]

    # ── Node Risk Watchlist ────────────────────────────────────────────────────

    def get_node_risk_watchlist(self) -> list[NodeRiskWatchlistItem]:
        from ..repositories.memory_store import store
        from ..domain.enums import NodeHealthStatus

        nodes = store.list_nodes()
        watchlist: list[NodeRiskWatchlistItem] = []

        for node in nodes:
            if node.health_status == NodeHealthStatus.HEALTHY and node.anomaly_count == 0:
                continue

            risk_score = 0.0
            risk_reason = []

            if node.health_status == NodeHealthStatus.CRITICAL:
                risk_score += 40
                risk_reason.append("Node status: CRITICAL")
            elif node.health_status == NodeHealthStatus.DEGRADED:
                risk_score += 20
                risk_reason.append("Node status: DEGRADED")

            if node.anomaly_count > 5:
                risk_score += 20
                risk_reason.append(f"High anomaly count: {node.anomaly_count}")
            elif node.anomaly_count > 2:
                risk_score += 10
                risk_reason.append(f"Elevated anomalies: {node.anomaly_count}")

            if node.avg_latency_ms > 2000:
                risk_score += 15
                risk_reason.append(f"Very high latency: {node.avg_latency_ms:.0f}ms")
            elif node.avg_latency_ms > 1000:
                risk_score += 8
                risk_reason.append(f"Elevated latency: {node.avg_latency_ms:.0f}ms")

            if node.delay_count > 3:
                risk_score += 10
                risk_reason.append(f"Delay count: {node.delay_count}")

            if risk_score < 5:
                continue

            recommended = (
                "Immediate investigation required — critical node impacting payments"
                if risk_score >= 40 else
                "Monitor closely — potential corridor impact"
            )

            watchlist.append(NodeRiskWatchlistItem(
                node_id=node.id,
                bank_name=node.bank_name,
                country=node.country,
                node_type=node.node_type.value,
                health_status=node.health_status.value,
                risk_score=round(risk_score, 1),
                anomaly_count=node.anomaly_count,
                delay_count=node.delay_count,
                avg_latency_ms=node.avg_latency_ms,
                risk_reason="; ".join(risk_reason) if risk_reason else "Monitoring threshold exceeded",
                recommended_action=recommended,
            ))

        watchlist.sort(key=lambda x: x.risk_score, reverse=True)
        return watchlist[:10]

    # ── System Anomaly Insights ────────────────────────────────────────────────

    def get_system_anomaly_insights(self) -> list[SystemAnomalyInsight]:
        from ..repositories.memory_store import store

        anomalies = store.list_anomalies()
        if not anomalies:
            return []

        # Group by anomaly type
        type_groups: dict[str, list] = {}
        for a in anomalies:
            key = a.type.value
            type_groups.setdefault(key, []).append(a)

        insights: list[SystemAnomalyInsight] = []
        for atype, group in sorted(type_groups.items(), key=lambda x: -len(x[1])):
            corridors = list({a.corridor for a in group if a.corridor})[:5]
            max_sev = max((a.severity.value for a in group), default="LOW")
            avg_conf = sum(a.confidence or 0 for a in group) / max(len(group), 1)
            open_count = sum(1 for a in group if a.status.value == "OPEN")

            rec_map = {
                "SANCTIONS_FALSE_POSITIVE": "Assign compliance officer batch review for all open sanctions holds",
                "GATEWAY_TIMEOUT": "Check correspondent network health; retry eligible payments",
                "VALIDATION_ERROR": "Initiate client outreach batch for data correction",
                "FX_DELAY": "Monitor FX liquidity providers; check currency pair spreads",
                "MISSING_INTERMEDIARY": "Review correspondent bank relationships for affected corridors",
                "SETTLEMENT_DELAY": "Escalate settlement queue backlog to settlement operations",
                "RECONCILIATION_MISMATCH": "Trigger batch reconciliation recheck for affected payments",
            }

            insights.append(SystemAnomalyInsight(
                insight_id=str(uuid.uuid4()),
                category=atype,
                title=f"{len(group)} {atype.replace('_', ' ').title()} anomalies detected",
                description=(
                    f"{open_count} of {len(group)} are currently open. "
                    f"Affecting {len(corridors)} corridor(s): {', '.join(corridors) or 'various'}."
                ),
                affected_payments=len(group),
                affected_corridors=corridors,
                severity=max_sev,
                confidence=round(avg_conf, 2),
                recommended_action=rec_map.get(atype, "Operations team review recommended"),
            ))

        return insights[:8]

    # ── Operator Summary ───────────────────────────────────────────────────────

    def get_operator_summary(self) -> OperatorSummary:
        from ..repositories.memory_store import store
        from ..domain.enums import PaymentStatus, AnomalySeverity

        payments = store.list_payments()
        anomalies = store.list_anomalies()

        total = len(payments)
        active = sum(1 for p in payments if p.current_status in (
            PaymentStatus.IN_PROGRESS, PaymentStatus.DELAYED, PaymentStatus.ON_HOLD
        ))
        failed = sum(1 for p in payments if p.current_status == PaymentStatus.FAILED)
        completed = sum(1 for p in payments if p.current_status == PaymentStatus.COMPLETED)
        sla_breaches = sum(1 for p in payments if p.sla_breach)
        critical_anomalies = sum(1 for a in anomalies if a.severity == AnomalySeverity.CRITICAL)
        high_anomalies = sum(1 for a in anomalies if a.severity == AnomalySeverity.HIGH)
        open_anomalies = sum(1 for a in anomalies if a.status.value == "OPEN")

        success_rate = (completed / max(total, 1)) * 100

        # Determine system status
        if critical_anomalies > 3 or sla_breaches > 10:
            system_status = "DEGRADED"
            headline = f"System under stress — {critical_anomalies} critical anomalies and {sla_breaches} SLA breaches require immediate attention."
        elif sla_breaches > 5 or high_anomalies > 5:
            system_status = "ELEVATED"
            headline = f"Elevated exception rate — {open_anomalies} open anomalies with {sla_breaches} SLA breaches. Operations review recommended."
        else:
            system_status = "NORMAL"
            headline = f"System operating within normal parameters. {success_rate:.0f}% success rate across {total} payments."

        # Top issues
        type_counts: dict[str, int] = {}
        for a in anomalies:
            type_counts[a.type.value] = type_counts.get(a.type.value, 0) + 1
        top_types = sorted(type_counts.items(), key=lambda x: -x[1])[:3]

        top_issues = [
            {
                "issue": atype.replace("_", " ").title(),
                "count": count,
                "urgency": "HIGH" if count > 5 else "MEDIUM",
            }
            for atype, count in top_types
        ]

        key_alerts = []
        if critical_anomalies > 0:
            key_alerts.append(f"{critical_anomalies} CRITICAL anomalies require immediate attention")
        if sla_breaches > 0:
            key_alerts.append(f"{sla_breaches} payments have breached SLA")
        if failed > 0:
            key_alerts.append(f"{failed} payments in FAILED state")

        recommended_actions = []
        if critical_anomalies > 0:
            recommended_actions.append("Review critical anomalies and assign compliance/ops owners")
        if sla_breaches > 5:
            recommended_actions.append("Run corridor SLA health check — multiple SLA breaches detected")
        if failed > 2:
            recommended_actions.append("Investigate failed payments for retry eligibility")
        if not recommended_actions:
            recommended_actions.append("Continue monitoring — no immediate action required")

        positive_signals = []
        if success_rate > 70:
            positive_signals.append(f"{success_rate:.0f}% payment success rate")
        if completed > 50:
            positive_signals.append(f"{completed} payments completed successfully")

        watch_items = []
        # Get top corridors at risk
        corridor_risks = self.get_corridor_risk_insights()
        for cr in corridor_risks[:2]:
            if cr.risk_level in ("HIGH", "CRITICAL"):
                watch_items.append(f"Corridor {cr.corridor}: {cr.primary_issue}")

        return OperatorSummary(
            generated_at=_ts(),
            headline=headline,
            system_status=system_status,
            key_alerts=key_alerts,
            top_issues=top_issues,
            recommended_actions=recommended_actions,
            positive_signals=positive_signals,
            watch_items=watch_items,
            ai_confidence=0.82,
        )


control_tower_ai = ControlTowerAI()

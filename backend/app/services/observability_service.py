"""Observability service: per-payment telemetry packages and analytics."""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..domain.enums import AnomalySeverity, PaymentStage, PaymentStatus, STAGE_ORDER
from ..repositories.memory_store import store
from ..schemas.payment import (
    DelayHotspotSchema,
    ExceptionPatternSchema,
    NodeHealthSchema,
    ObservabilityPackage,
    StageMetricsSchema,
    StageTimingDetail,
)


class ObservabilityService:

    def get_payment_observability(self, payment_id: str) -> ObservabilityPackage | None:
        payment = store.get_payment(payment_id)
        if not payment:
            return None

        anomalies = store.get_anomalies_for_payment(payment_id)

        # Build stage detail list
        stage_detail: list[StageTimingDetail] = []
        all_stages = [s for s in STAGE_ORDER if s != PaymentStage.COMPLETED]
        for stage in all_stages:
            sv = stage.value
            actual = payment.stage_timings.get(sv)
            if actual is None:
                continue
            expected = payment.expected_stage_durations.get(sv, 60.0)
            delta = round(actual - expected, 1)
            retry = payment.retry_counts.get(sv, 0)
            queue = payment.queue_wait_seconds.get(sv, 0.0)
            entry_time = payment.stage_entry_times.get(sv)
            is_bottleneck = payment.bottleneck_stage == sv

            stage_detail.append(StageTimingDetail(
                stage=sv,
                duration_seconds=actual,
                expected_seconds=expected,
                delta_seconds=delta,
                is_bottleneck=is_bottleneck,
                retry_count=retry,
                queue_wait_seconds=queue,
                entry_time=entry_time,
            ))

        # Node latency panel
        node_latency = []
        for node in store.list_nodes():
            if node.country in payment.route_path:
                node_latency.append({
                    "node_name": node.bank_name,
                    "country": node.country,
                    "node_type": node.node_type.value,
                    "avg_latency_ms": node.avg_latency_ms,
                    "health_status": node.health_status.value,
                    "is_delay_node": payment.delay_node == node.bank_name,
                })

        # Anomaly summary
        anomaly_summary = None
        if anomalies:
            a = anomalies[0]
            anomaly_summary = {
                "id": a.id,
                "type": a.type.value,
                "severity": a.severity.value,
                "title": a.title,
                "stage": a.stage.value,
                "action_status": a.action_status.value,
                "operational_impact_score": a.operational_impact_score,
                "root_symptom": a.root_symptom,
                "probable_cause": a.probable_cause,
                "resolution_eta_minutes": a.resolution_eta_minutes,
                "recurrence_count": a.recurrence_count,
            }

        return ObservabilityPackage(
            payment_id=payment.id,
            payment_reference=payment.payment_reference,
            total_processing_seconds=payment.total_processing_seconds,
            sla_breach=payment.sla_breach,
            sla_breach_seconds=payment.sla_breach_seconds,
            bottleneck_stage=payment.bottleneck_stage,
            bottleneck_node=payment.bottleneck_node,
            escalation_flag=payment.escalation_flag,
            operator_intervention=payment.operator_intervention,
            recovered=payment.recovered,
            stage_detail=stage_detail,
            node_latency=node_latency,
            anomaly_summary=anomaly_summary,
        )

    def get_stage_metrics(self) -> list[StageMetricsSchema]:
        payments = store.list_payments()
        results = []

        for stage in STAGE_ORDER:
            if stage in (PaymentStage.COMPLETED, PaymentStage.FAILED, PaymentStage.ON_HOLD):
                continue

            sv = stage.value
            stage_payments = [p for p in payments if p.stage_timings.get(sv) is not None]
            if not stage_payments:
                continue

            durations = [p.stage_timings[sv] for p in stage_payments]
            avg_dur = round(sum(durations) / len(durations), 1) if durations else 0.0
            expected_dur = float(sum(p.expected_stage_durations.get(sv, 60) for p in stage_payments) / max(len(stage_payments), 1))

            # Failure rate: payments that stopped at this stage with failed/on_hold
            stopped_failed = [p for p in stage_payments if p.current_stage == stage and p.current_status in (PaymentStatus.FAILED, PaymentStatus.ON_HOLD)]
            failure_rate = round(len(stopped_failed) / max(len(stage_payments), 1) * 100, 1)

            # Retry rate
            retried = [p for p in stage_payments if p.retry_counts.get(sv, 0) > 0]
            retry_rate = round(len(retried) / max(len(stage_payments), 1) * 100, 1)

            sla_breach_count = sum(1 for p in stage_payments if p.sla_breach and p.bottleneck_stage == sv)
            bottleneck_count = sum(1 for p in stage_payments if p.bottleneck_stage == sv)
            on_hold_count = len(stopped_failed)

            # Top failure reasons from anomalies at this stage
            anomalies_at_stage = store.filter_anomalies(stage=sv)
            reason_counter = Counter(a.type.value for a in anomalies_at_stage)
            top_reasons = [r for r, _ in reason_counter.most_common(3)]

            results.append(StageMetricsSchema(
                stage=sv,
                total_count=len(stage_payments),
                avg_duration_seconds=avg_dur,
                expected_duration_seconds=round(expected_dur, 1),
                failure_rate=failure_rate,
                retry_rate=retry_rate,
                sla_breach_count=sla_breach_count,
                bottleneck_count=bottleneck_count,
                on_hold_count=on_hold_count,
                top_failure_reasons=top_reasons,
            ))

        return results

    def get_node_health(self) -> list[NodeHealthSchema]:
        payments = store.list_payments()
        nodes = store.list_nodes()
        results = []

        for node in nodes:
            # Find impacted payments
            impacted_ids = [
                p.id for p in payments
                if (p.delay_node == node.bank_name or node.country in p.route_path)
                and p.anomaly_flag
            ][:10]

            # Compute health score 0-100 (100 = perfectly healthy)
            latency_penalty = min(node.avg_latency_ms / 10, 40)
            anomaly_penalty = min(node.anomaly_count * 5, 30)
            risk_penalty = node.risk_score * 30
            health_score = max(0.0, round(100 - latency_penalty - anomaly_penalty - risk_penalty, 1))

            results.append(NodeHealthSchema(
                node_id=node.id,
                bank_name=node.bank_name,
                country=node.country,
                node_type=node.node_type.value,
                health_status=node.health_status.value,
                health_score=health_score,
                avg_latency_ms=node.avg_latency_ms,
                p99_latency_ms=node.p99_latency_ms,
                anomaly_count=node.anomaly_count,
                delay_count=node.delay_count,
                route_usage_count=node.route_usage_count,
                impacted_payment_ids=impacted_ids,
                last_incident_at=node.last_incident_at,
                supported_rails=node.supported_rails,
                risk_score=node.risk_score,
            ))

        results.sort(key=lambda n: n.health_score)
        return results

    def get_delay_hotspots(self) -> DelayHotspotSchema:
        payments = store.list_payments()
        anomalies = store.list_anomalies()

        # Countries ranked by delays
        country_delay: Counter = Counter()
        country_anomaly: Counter = Counter()
        for p in payments:
            if p.delay_country:
                country_delay[p.delay_country] += 1
            if p.anomaly_flag and p.delay_country:
                country_anomaly[p.delay_country] += 1

        ranked_countries = [
            {
                "country": c,
                "delay_count": n,
                "anomaly_count": country_anomaly.get(c, 0),
                "severity": "HIGH" if n > 4 else ("MEDIUM" if n > 2 else "LOW"),
            }
            for c, n in country_delay.most_common(10)
        ]

        # Nodes ranked by delays
        node_delay: Counter = Counter()
        for p in payments:
            if p.delay_node:
                node_delay[p.delay_node] += 1

        ranked_nodes = [
            {"node": n, "delay_count": cnt}
            for n, cnt in node_delay.most_common(10)
        ]

        # Corridors ranked by delays
        corridor_delay: Counter = Counter()
        for p in payments:
            if p.delay_country or (p.anomaly_flag and p.current_status in (PaymentStatus.DELAYED, PaymentStatus.ON_HOLD)):
                corridor_delay[p.corridor] += 1

        ranked_corridors = [
            {"corridor": c, "delay_count": cnt}
            for c, cnt in corridor_delay.most_common(10)
        ]

        # Stage hotspots: bottleneck count per stage
        stage_bottleneck: Counter = Counter()
        for p in payments:
            if p.bottleneck_stage:
                stage_bottleneck[p.bottleneck_stage] += 1

        stage_hotspots = [
            {"stage": s, "bottleneck_count": cnt}
            for s, cnt in stage_bottleneck.most_common()
        ]

        # Severity breakdown
        sev_counter = Counter(a.severity.value for a in anomalies)

        return DelayHotspotSchema(
            ranked_countries=ranked_countries,
            ranked_nodes=ranked_nodes,
            ranked_corridors=ranked_corridors,
            stage_hotspots=stage_hotspots,
            severity_breakdown=dict(sev_counter),
        )

    def get_exception_patterns(self) -> ExceptionPatternSchema:
        anomalies = store.list_anomalies()
        payments = store.list_payments()

        # Type frequencies
        type_counter: Counter = Counter(a.type.value for a in anomalies)
        type_frequencies = [
            {
                "type": t,
                "count": cnt,
                "pct": round(cnt / max(len(anomalies), 1) * 100, 1),
                "avg_impact": round(
                    sum(a.operational_impact_score or 0 for a in anomalies if a.type.value == t) / max(cnt, 1), 1
                ),
            }
            for t, cnt in type_counter.most_common()
        ]

        # Stage -> anomaly type map
        stage_anomaly_map: dict[str, list[str]] = {}
        for a in anomalies:
            sv = a.stage.value
            if sv not in stage_anomaly_map:
                stage_anomaly_map[sv] = []
            if a.type.value not in stage_anomaly_map[sv]:
                stage_anomaly_map[sv].append(a.type.value)

        # Corridor anomaly distribution
        corridor_anom: dict[str, Counter] = {}
        for a in anomalies:
            c = a.corridor or "UNKNOWN"
            if c not in corridor_anom:
                corridor_anom[c] = Counter()
            corridor_anom[c][a.type.value] += 1

        corridor_anomaly_distribution = [
            {
                "corridor": c,
                "anomaly_count": sum(cnt.values()),
                "top_type": cnt.most_common(1)[0][0] if cnt else None,
                "breakdown": dict(cnt),
            }
            for c, cnt in sorted(corridor_anom.items(), key=lambda x: sum(x[1].values()), reverse=True)[:10]
        ]

        # Recurring signatures: anomaly types with recurrence_count > 0
        recurring = [
            {
                "type": a.type.value,
                "code": a.anomaly_code,
                "recurrence_count": a.recurrence_count,
                "stage": a.stage.value,
                "corridor": a.corridor,
                "severity": a.severity.value,
            }
            for a in anomalies
            if a.recurrence_count > 0
        ]
        recurring.sort(key=lambda x: x["recurrence_count"], reverse=True)

        # Trend summary
        total_open = sum(1 for a in anomalies if a.status.value == "OPEN")
        total_resolved = sum(1 for a in anomalies if a.status.value == "RESOLVED")
        high_impact = sum(1 for a in anomalies if (a.operational_impact_score or 0) >= 7.0)
        escalated = sum(1 for p in payments if p.escalation_flag)

        trend_summary = {
            "total_anomalies": len(anomalies),
            "open_count": total_open,
            "resolved_count": total_resolved,
            "high_impact_count": high_impact,
            "escalated_payments": escalated,
            "top_type": type_counter.most_common(1)[0][0] if type_counter else None,
            "resolution_rate": round(total_resolved / max(len(anomalies), 1) * 100, 1),
        }

        return ExceptionPatternSchema(
            type_frequencies=type_frequencies,
            stage_anomaly_map=stage_anomaly_map,
            corridor_anomaly_distribution=corridor_anomaly_distribution,
            recurring_signatures=recurring[:20],
            trend_summary=trend_summary,
        )


observability_service = ObservabilityService()

"""Metrics aggregation service for control tower overview and system health."""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from ..domain.enums import AnomalySeverity, PaymentStage, PaymentStatus
from ..repositories.memory_store import store
from ..schemas.payment import (
    CorridorSchema,
    CountrySchema,
    EnhancedCorridorSchema,
    EnhancedOverviewMetrics,
    EnhancedSystemHealthSchema,
    OverviewMetrics,
    SystemHealthSchema,
)


class MetricsService:

    def get_overview(self) -> OverviewMetrics:
        payments = store.list_payments()
        anomalies = store.list_anomalies()

        total = len(payments)
        in_progress = sum(1 for p in payments if p.current_status == PaymentStatus.IN_PROGRESS)
        completed = sum(1 for p in payments if p.current_status == PaymentStatus.COMPLETED)
        failed = sum(1 for p in payments if p.current_status == PaymentStatus.FAILED)
        on_hold = sum(1 for p in payments if p.current_status == PaymentStatus.ON_HOLD)
        delayed = sum(1 for p in payments if p.current_status == PaymentStatus.DELAYED)

        anomaly_count = len(anomalies)
        severe_count = sum(1 for a in anomalies if a.severity in (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL))

        # Average processing time for completed payments
        processing_times = []
        for p in payments:
            if p.actual_completion_at and p.created_at:
                delta = (p.actual_completion_at - p.created_at).total_seconds()
                processing_times.append(delta)
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0.0

        # Corridor distribution
        corridor_counter = Counter(p.corridor for p in payments)
        corridor_dist = dict(corridor_counter.most_common(20))

        # Top delayed countries
        delay_counter = Counter(p.delay_country for p in payments if p.delay_country)
        top_delayed = [{"country": c, "count": n} for c, n in delay_counter.most_common(10)]

        # Top anomaly types
        anom_type_counter = Counter(a.type.value for a in anomalies)
        top_anomaly_types = [{"type": t, "count": n} for t, n in anom_type_counter.most_common(10)]

        # Stage distribution
        stage_counter = Counter(p.current_stage.value for p in payments)
        stage_dist = dict(stage_counter)

        return OverviewMetrics(
            total_payments=total,
            in_progress=in_progress + delayed,
            completed=completed,
            failed=failed,
            on_hold=on_hold,
            anomaly_count=anomaly_count,
            severe_anomaly_count=severe_count,
            average_processing_time_seconds=round(avg_time, 1),
            corridor_distribution=corridor_dist,
            top_delayed_countries=top_delayed,
            top_anomaly_types=top_anomaly_types,
            stage_distribution=stage_dist,
        )

    def get_system_health(self) -> SystemHealthSchema:
        payments = store.list_payments()
        anomalies = store.list_anomalies()
        total = len(payments) or 1

        completed = sum(1 for p in payments if p.current_status == PaymentStatus.COMPLETED)
        in_progress = sum(1 for p in payments if p.current_status in (PaymentStatus.IN_PROGRESS, PaymentStatus.DELAYED))

        success_rate = round(completed / total * 100, 1)
        anomaly_rate = round(len(anomalies) / total * 100, 1)

        # Route health - aggregate by corridor
        corridor_health: dict[str, dict] = {}
        for p in payments:
            if p.corridor not in corridor_health:
                corridor_health[p.corridor] = {"corridor": p.corridor, "total": 0, "failed": 0, "delayed": 0, "anomalies": 0}
            corridor_health[p.corridor]["total"] += 1
            if p.current_status == PaymentStatus.FAILED:
                corridor_health[p.corridor]["failed"] += 1
            if p.current_status == PaymentStatus.DELAYED:
                corridor_health[p.corridor]["delayed"] += 1
            if p.anomaly_flag:
                corridor_health[p.corridor]["anomalies"] += 1

        route_health = sorted(corridor_health.values(), key=lambda x: x["anomalies"], reverse=True)[:10]

        # Compliance health
        compliance_payments = [p for p in payments if p.current_stage == PaymentStage.COMPLIANCE or p.sanctions_hit]
        compliance_health = {
            "total_screened": total,
            "sanctions_hits": sum(1 for p in payments if p.sanctions_hit),
            "pending_review": sum(1 for p in compliance_payments if p.current_status == PaymentStatus.ON_HOLD),
            "cleared": total - sum(1 for p in compliance_payments if p.current_status == PaymentStatus.ON_HOLD),
        }

        # Settlement health
        settled = sum(1 for p in payments if p.current_stage in (PaymentStage.RECONCILIATION, PaymentStage.COMPLETED))
        settlement_health = {
            "total_settled": settled,
            "pending_settlement": sum(1 for p in payments if p.current_stage == PaymentStage.SETTLEMENT),
            "settlement_failures": sum(1 for p in payments if p.current_stage == PaymentStage.SETTLEMENT and p.current_status == PaymentStatus.FAILED),
            "recon_mismatches": sum(1 for p in payments if p.reconciliation_break),
        }

        return SystemHealthSchema(
            system_status="OPERATIONAL" if success_rate > 80 else "DEGRADED",
            queue_depth=in_progress,
            processing_latency_ms=round(sum(45.0 + (i * 2.3) for i in range(min(in_progress, 20))) / max(in_progress, 1), 1),
            anomaly_rate=anomaly_rate,
            success_rate=success_rate,
            route_health=route_health,
            compliance_health=compliance_health,
            settlement_health=settlement_health,
        )

    def get_corridors(self) -> list[CorridorSchema]:
        payments = store.list_payments()
        corridor_map: dict[str, list] = {}
        for p in payments:
            if p.corridor not in corridor_map:
                corridor_map[p.corridor] = []
            corridor_map[p.corridor].append(p)

        corridors = []
        for corridor_name, plist in corridor_map.items():
            parts = corridor_name.split("-")
            src = parts[0] if len(parts) > 0 else ""
            dst = parts[1] if len(parts) > 1 else ""
            total_amount = sum(p.amount for p in plist)
            anomaly_count = sum(1 for p in plist if p.anomaly_flag)
            processing_times = []
            for p in plist:
                if p.actual_completion_at:
                    processing_times.append((p.actual_completion_at - p.created_at).total_seconds())
            avg_time = sum(processing_times) / len(processing_times) if processing_times else 0

            status_counter = Counter(p.current_status for p in plist)
            dominant_status = status_counter.most_common(1)[0][0] if status_counter else PaymentStatus.PENDING

            corridors.append(CorridorSchema(
                corridor=corridor_name,
                source_country=src,
                destination_country=dst,
                payment_count=len(plist),
                total_amount=round(total_amount, 2),
                anomaly_count=anomaly_count,
                avg_processing_time_seconds=round(avg_time, 1),
                dominant_status=dominant_status,
            ))

        corridors.sort(key=lambda c: c.payment_count, reverse=True)
        return corridors

    def get_countries(self) -> list[CountrySchema]:
        payments = store.list_payments()
        country_stats: dict[str, dict] = {}

        for p in payments:
            for cc in [p.source_country, p.destination_country] + p.route_path:
                if cc not in country_stats:
                    country_stats[cc] = {"as_source": 0, "as_dest": 0, "as_inter": 0, "anomalies": 0, "delays": 0}

            country_stats[p.source_country]["as_source"] += 1
            country_stats[p.destination_country]["as_dest"] += 1
            for inter in p.route_path[1:-1]:
                country_stats[inter]["as_inter"] += 1
            if p.anomaly_flag and p.delay_country and p.delay_country in country_stats:
                country_stats[p.delay_country]["anomalies"] += 1
            if p.delay_country and p.delay_country in country_stats:
                country_stats[p.delay_country]["delays"] += 1

        result = []
        for cc, stats in country_stats.items():
            result.append(CountrySchema(
                country=cc,
                country_code=cc,
                as_source_count=stats["as_source"],
                as_destination_count=stats["as_dest"],
                as_intermediary_count=stats["as_inter"],
                anomaly_count=stats["anomalies"],
                delay_count=stats["delays"],
            ))

        result.sort(key=lambda c: c.as_source_count + c.as_destination_count, reverse=True)
        return result


    def get_enhanced_overview(self) -> EnhancedOverviewMetrics:
        payments = store.list_payments()
        anomalies = store.list_anomalies()

        total = len(payments)
        in_progress = sum(1 for p in payments if p.current_status == PaymentStatus.IN_PROGRESS)
        completed = sum(1 for p in payments if p.current_status == PaymentStatus.COMPLETED)
        failed = sum(1 for p in payments if p.current_status == PaymentStatus.FAILED)
        on_hold = sum(1 for p in payments if p.current_status == PaymentStatus.ON_HOLD)
        delayed = sum(1 for p in payments if p.current_status == PaymentStatus.DELAYED)
        sla_breach_count = sum(1 for p in payments if p.sla_breach)
        recovered_count = sum(1 for p in payments if p.recovered)

        anomaly_count = len(anomalies)
        severe_count = sum(1 for a in anomalies if a.severity in (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL))

        processing_times = [
            (p.actual_completion_at - p.created_at).total_seconds()
            for p in payments if p.actual_completion_at and p.created_at
        ]
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0.0

        # Throughput estimate: completed payments / hours span
        oldest = min((p.created_at for p in payments), default=None)
        if oldest:
            from datetime import datetime
            hours_span = max((datetime.utcnow() - oldest).total_seconds() / 3600, 1)
            throughput = round(completed / hours_span, 2)
        else:
            throughput = 0.0

        anomaly_rate = round(anomaly_count / max(total, 1) * 100, 1)
        success_rate = round(completed / max(total, 1) * 100, 1)

        corridor_counter = Counter(p.corridor for p in payments)
        stage_counter = Counter(p.current_stage.value for p in payments)
        delay_counter = Counter(p.delay_country for p in payments if p.delay_country)
        anom_type_counter = Counter(a.type.value for a in anomalies)

        # Stage bottleneck ranking
        bottleneck_counter = Counter(p.bottleneck_stage for p in payments if p.bottleneck_stage)
        stage_bottleneck_ranking = [
            {"stage": s, "count": cnt}
            for s, cnt in bottleneck_counter.most_common(8)
        ]

        # Top corridors by volume
        top_corridors_volume = [
            {"corridor": c, "count": n}
            for c, n in corridor_counter.most_common(8)
        ]

        # Top corridors by risk (anomaly count)
        corridor_anomaly: Counter = Counter()
        for a in anomalies:
            if a.corridor:
                corridor_anomaly[a.corridor] += 1
        top_corridors_risk = [
            {"corridor": c, "anomaly_count": cnt}
            for c, cnt in corridor_anomaly.most_common(8)
        ]

        return EnhancedOverviewMetrics(
            total_payments=total,
            in_progress=in_progress + delayed,
            completed=completed,
            failed=failed,
            on_hold=on_hold,
            delayed=delayed,
            anomaly_count=anomaly_count,
            severe_anomaly_count=severe_count,
            sla_breach_count=sla_breach_count,
            recovered_count=recovered_count,
            average_processing_time_seconds=round(avg_time, 1),
            throughput_per_hour=throughput,
            anomaly_rate=anomaly_rate,
            success_rate=success_rate,
            corridor_distribution=dict(corridor_counter.most_common(20)),
            top_delayed_countries=[{"country": c, "count": n} for c, n in delay_counter.most_common(10)],
            top_anomaly_types=[{"type": t, "count": n} for t, n in anom_type_counter.most_common(10)],
            stage_distribution=dict(stage_counter),
            stage_bottleneck_ranking=stage_bottleneck_ranking,
            top_corridors_by_volume=top_corridors_volume,
            top_corridors_by_risk=top_corridors_risk,
        )

    def get_enhanced_corridors(self) -> list[EnhancedCorridorSchema]:
        payments = store.list_payments()
        anomalies = store.list_anomalies()
        corridor_map: dict[str, list] = {}
        for p in payments:
            corridor_map.setdefault(p.corridor, []).append(p)

        anomaly_by_corridor: dict[str, list] = {}
        for a in anomalies:
            if a.corridor:
                anomaly_by_corridor.setdefault(a.corridor, []).append(a)

        results = []
        for corridor_name, plist in corridor_map.items():
            parts = corridor_name.split("-")
            src = parts[0] if parts else ""
            dst = parts[1] if len(parts) > 1 else ""
            total_amount = sum(p.amount for p in plist)
            anomaly_list = anomaly_by_corridor.get(corridor_name, [])
            anomaly_count = len(anomaly_list)
            anomaly_rate = round(anomaly_count / max(len(plist), 1) * 100, 1)
            failure_count = sum(1 for p in plist if p.current_status == PaymentStatus.FAILED)
            failure_rate = round(failure_count / max(len(plist), 1) * 100, 1)
            sla_breach_count = sum(1 for p in plist if p.sla_breach)

            processing_times = [
                (p.actual_completion_at - p.created_at).total_seconds()
                for p in plist if p.actual_completion_at
            ]
            avg_time = sum(processing_times) / len(processing_times) if processing_times else 0

            status_counter = Counter(p.current_status for p in plist)
            dominant_status = status_counter.most_common(1)[0][0] if status_counter else PaymentStatus.PENDING

            type_counter = Counter(a.type.value for a in anomaly_list)
            top_anomaly_type = type_counter.most_common(1)[0][0] if type_counter else None

            risk_score = round(
                (anomaly_rate * 0.4 + failure_rate * 0.35 + (sla_breach_count / max(len(plist), 1) * 100) * 0.25) / 100 * 10,
                2
            )

            results.append(EnhancedCorridorSchema(
                corridor=corridor_name,
                source_country=src,
                destination_country=dst,
                payment_count=len(plist),
                total_amount=round(total_amount, 2),
                anomaly_count=anomaly_count,
                anomaly_rate=anomaly_rate,
                avg_processing_time_seconds=round(avg_time, 1),
                failure_count=failure_count,
                failure_rate=failure_rate,
                sla_breach_count=sla_breach_count,
                dominant_status=dominant_status,
                top_anomaly_type=top_anomaly_type,
                risk_score=risk_score,
            ))

        results.sort(key=lambda c: c.payment_count, reverse=True)
        return results

    def get_enhanced_system_health(self) -> EnhancedSystemHealthSchema:
        payments = store.list_payments()
        anomalies = store.list_anomalies()
        total = len(payments) or 1

        completed = sum(1 for p in payments if p.current_status == PaymentStatus.COMPLETED)
        in_progress = sum(1 for p in payments if p.current_status in (PaymentStatus.IN_PROGRESS, PaymentStatus.DELAYED))
        sla_breaches = sum(1 for p in payments if p.sla_breach)

        success_rate = round(completed / total * 100, 1)
        anomaly_rate = round(len(anomalies) / total * 100, 1)
        sla_breach_rate = round(sla_breaches / total * 100, 1)

        # Queue by stage
        queue_by_stage: dict[str, int] = {}
        for p in payments:
            if p.current_status in (PaymentStatus.IN_PROGRESS, PaymentStatus.DELAYED, PaymentStatus.ON_HOLD):
                sv = p.current_stage.value
                queue_by_stage[sv] = queue_by_stage.get(sv, 0) + 1

        # Processing latency from stage timings
        all_latencies = []
        for p in payments:
            if p.total_processing_seconds:
                all_latencies.append(p.total_processing_seconds * 1000)
        avg_latency_ms = round(sum(all_latencies) / len(all_latencies) / 1000, 1) if all_latencies else 45.0

        # Throughput
        oldest = min((p.created_at for p in payments), default=None)
        if oldest:
            from datetime import datetime
            hours_span = max((datetime.utcnow() - oldest).total_seconds() / 3600, 1)
            throughput = round(completed / hours_span, 2)
        else:
            throughput = 0.0

        # Route health
        corridor_health: dict[str, dict] = {}
        for p in payments:
            corridor_health.setdefault(p.corridor, {"corridor": p.corridor, "total": 0, "failed": 0, "delayed": 0, "anomalies": 0, "sla_breaches": 0})
            corridor_health[p.corridor]["total"] += 1
            if p.current_status == PaymentStatus.FAILED:
                corridor_health[p.corridor]["failed"] += 1
            if p.current_status == PaymentStatus.DELAYED:
                corridor_health[p.corridor]["delayed"] += 1
            if p.anomaly_flag:
                corridor_health[p.corridor]["anomalies"] += 1
            if p.sla_breach:
                corridor_health[p.corridor]["sla_breaches"] += 1
        route_health = sorted(corridor_health.values(), key=lambda x: x["anomalies"], reverse=True)[:10]

        # Route health index: % of corridors with no anomalies
        clean_corridors = sum(1 for ch in corridor_health.values() if ch["anomalies"] == 0)
        route_health_index = round(clean_corridors / max(len(corridor_health), 1) * 100, 1)

        # Compliance health
        compliance_health = {
            "total_screened": total,
            "sanctions_hits": sum(1 for p in payments if p.sanctions_hit),
            "pending_review": sum(1 for p in payments if p.sanctions_hit and p.current_status == PaymentStatus.ON_HOLD),
            "cleared": total - sum(1 for p in payments if p.sanctions_hit and p.current_status == PaymentStatus.ON_HOLD),
            "health_score": round(max(0, 100 - sum(1 for p in payments if p.sanctions_hit) / max(total, 1) * 200), 1),
        }

        # Settlement health
        settled = sum(1 for p in payments if p.current_stage in (PaymentStage.RECONCILIATION, PaymentStage.COMPLETED))
        recon_mismatches = sum(1 for p in payments if p.reconciliation_break)
        settlement_health = {
            "total_settled": settled,
            "pending_settlement": sum(1 for p in payments if p.current_stage == PaymentStage.SETTLEMENT),
            "settlement_failures": sum(1 for p in payments if p.current_stage == PaymentStage.SETTLEMENT and p.current_status == PaymentStatus.FAILED),
            "recon_mismatches": recon_mismatches,
            "health_score": round(max(0, 100 - recon_mismatches / max(total, 1) * 500), 1),
        }

        # Routing health
        gateway_timeouts = sum(1 for p in payments if p.gateway_timeout)
        routing_health = {
            "gateway_timeouts": gateway_timeouts,
            "missing_intermediary": sum(1 for p in payments if p.current_stage == PaymentStage.ROUTING and p.current_status == PaymentStatus.FAILED),
            "route_failovers": sum(1 for p in payments if p.recovered and p.bottleneck_stage == PaymentStage.ROUTING.value),
            "health_score": round(max(0, 100 - gateway_timeouts / max(total, 1) * 300), 1),
        }

        # FX health
        fx_delays = sum(1 for p in payments if p.anomaly_type and p.anomaly_type.value == "FX_DELAY")
        fx_health = {
            "fx_delays": fx_delays,
            "avg_fx_stage_seconds": round(
                sum(p.stage_timings.get("FX", 60) for p in payments if p.stage_timings.get("FX")) / max(
                    sum(1 for p in payments if p.stage_timings.get("FX")), 1
                ), 1
            ),
            "health_score": round(max(0, 100 - fx_delays / max(total, 1) * 300), 1),
        }

        # Overall health score
        overall = round(
            (compliance_health["health_score"] * 0.25 +
             settlement_health["health_score"] * 0.25 +
             routing_health["health_score"] * 0.25 +
             fx_health["health_score"] * 0.25),
            1
        )
        system_status = "OPERATIONAL" if overall > 80 else ("DEGRADED" if overall > 60 else "CRITICAL")

        return EnhancedSystemHealthSchema(
            system_status=system_status,
            overall_health_score=overall,
            queue_depth=in_progress,
            queue_by_stage=queue_by_stage,
            processing_latency_ms=avg_latency_ms,
            throughput_per_hour=throughput,
            anomaly_rate=anomaly_rate,
            success_rate=success_rate,
            sla_breach_rate=sla_breach_rate,
            route_health_index=route_health_index,
            compliance_health=compliance_health,
            settlement_health=settlement_health,
            routing_health=routing_health,
            fx_health=fx_health,
            route_health=route_health,
        )


metrics_service = MetricsService()

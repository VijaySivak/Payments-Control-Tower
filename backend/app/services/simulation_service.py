"""Payment simulation and replay service."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from ..domain.enums import (
    AnomalySeverity,
    AnomalyScope,
    AnomalyStatus,
    AnomalyType,
    EventType,
    LogLevel,
    PaymentPriority,
    PaymentStage,
    PaymentStatus,
    PaymentType,
    RouteType,
    STAGE_ORDER,
)
from ..domain.models import Anomaly, Payment, PaymentEvent, PaymentLog, new_id
from ..repositories.memory_store import store
from ..schemas.payment import (
    AdvancedSimulationResponse,
    AnomalySchema,
    ObservabilityPackage,
    PaymentEventSchema,
    PaymentJourneySchema,
    PaymentSchema,
    ReplayComparisonResponse,
    SimulationResponse,
    StageTimingDetail,
)
from ..seed.generator_v2 import (
    ANOMALY_CONFIGS,
    BANKS,
    BENEFICIARY_NAMES,
    CLIENT_NAMES,
    CORRIDORS,
    _get_fx_rate,
    _generate_stage_timings,
    _compute_sla_breach,
)
from ..utils.geo import get_currency
from .journey_service import journey_service


class SimulationService:

    def simulate(
        self,
        source_country: str | None = None,
        destination_country: str | None = None,
        amount: float | None = None,
        payment_type: PaymentType | None = None,
        inject_anomaly: AnomalyType | None = None,
    ) -> SimulationResponse:
        rng = random.Random()
        now = datetime.utcnow()

        # Pick corridor
        if source_country and destination_country:
            matching = [c for c in CORRIDORS if c["src"] == source_country and c["dst"] == destination_country]
            corridor = matching[0] if matching else {"src": source_country, "dst": destination_country, "intermediaries": []}
        else:
            corridor = rng.choice(CORRIDORS)

        src = corridor["src"]
        dst = corridor["dst"]
        src_curr = get_currency(src)
        dst_curr = get_currency(dst)
        amt = amount or round(rng.uniform(10000, 2000000), 2)
        fx_rate = _get_fx_rate(src_curr, dst_curr)
        route_path = [src] + corridor.get("intermediaries", []) + [dst]
        rt = RouteType.DIRECT if len(route_path) == 2 else (RouteType.INTERMEDIARY if len(route_path) == 3 else RouteType.MULTI_HOP)

        # Determine anomaly
        anomaly_type = inject_anomaly
        if not anomaly_type and rng.random() < 0.3:
            anomaly_type = rng.choice(list(AnomalyType))

        # Determine final state
        if anomaly_type:
            cfg = ANOMALY_CONFIGS[anomaly_type]
            target_stage = cfg["stage"]
            if anomaly_type == AnomalyType.VALIDATION_ERROR:
                final_status = PaymentStatus.FAILED
            elif anomaly_type in (AnomalyType.GATEWAY_TIMEOUT, AnomalyType.SETTLEMENT_DELAY):
                final_status = PaymentStatus.DELAYED
            elif anomaly_type == AnomalyType.FX_DELAY:
                # FX delay resolves
                target_stage = PaymentStage.COMPLETED
                final_status = PaymentStatus.COMPLETED
            else:
                final_status = PaymentStatus.ON_HOLD
        else:
            target_stage = PaymentStage.COMPLETED
            final_status = PaymentStatus.COMPLETED

        delay_node = None
        delay_country = None
        if anomaly_type in (AnomalyType.GATEWAY_TIMEOUT, AnomalyType.MISSING_INTERMEDIARY, AnomalyType.SETTLEMENT_DELAY):
            if corridor.get("intermediaries"):
                delay_country = rng.choice(corridor["intermediaries"])
                matching_banks = [b for b in BANKS if b["country"] == delay_country]
                delay_node = matching_banks[0]["name"] if matching_banks else f"{delay_country} Gateway"
            else:
                delay_country = dst
                delay_node = f"{dst} Settlement Node"

        payment = Payment(
            payment_reference=f"SIM-{now.strftime('%Y%m%d%H%M%S')}-{src}{dst}",
            source_client_name=rng.choice(CLIENT_NAMES),
            beneficiary_name=rng.choice(BENEFICIARY_NAMES),
            source_country=src,
            destination_country=dst,
            source_currency=src_curr,
            destination_currency=dst_curr,
            amount=amt,
            fx_rate=fx_rate,
            send_amount=amt,
            receive_amount=round(amt * fx_rate, 2),
            corridor=f"{src}-{dst}",
            priority=rng.choice(list(PaymentPriority)),
            payment_type=payment_type or rng.choice(list(PaymentType)),
            current_stage=target_stage,
            current_status=final_status,
            anomaly_flag=anomaly_type is not None,
            anomaly_type=anomaly_type,
            anomaly_severity=ANOMALY_CONFIGS[anomaly_type]["severity"] if anomaly_type else None,
            anomaly_reason=ANOMALY_CONFIGS[anomaly_type]["desc"] if anomaly_type else None,
            created_at=now,
            updated_at=now,
            expected_completion_at=now + timedelta(hours=rng.randint(2, 24)),
            actual_completion_at=now if final_status == PaymentStatus.COMPLETED else None,
            route_type=rt,
            route_path=route_path,
            delay_node=delay_node,
            delay_country=delay_country,
            sanctions_hit=anomaly_type == AnomalyType.SANCTIONS_FALSE_POSITIVE,
            validation_error=anomaly_type == AnomalyType.VALIDATION_ERROR,
            gateway_timeout=anomaly_type == AnomalyType.GATEWAY_TIMEOUT,
            reconciliation_break=anomaly_type == AnomalyType.RECONCILIATION_MISMATCH,
        )

        store.add_payment(payment)

        # Generate events
        events = self._generate_sim_events(payment, target_stage, anomaly_type, rng, now)
        for ev in events:
            store.add_event(ev)

        # Generate anomaly record
        anomaly_record = None
        if anomaly_type:
            cfg = ANOMALY_CONFIGS[anomaly_type]
            anomaly_obj = Anomaly(
                payment_id=payment.id,
                type=anomaly_type,
                title=cfg["title"],
                description=cfg["desc"],
                severity=cfg["severity"],
                detected_at=now + timedelta(seconds=rng.randint(10, 120)),
                stage=cfg["stage"],
                scope=cfg["scope"],
                country=delay_country or dst,
                intermediary_bank=delay_node,
                status=AnomalyStatus.OPEN,
                recommended_action=cfg.get("recommended_action"),
                confidence=round(rng.uniform(0.65, 0.98), 2),
                evidence_summary=cfg.get("evidence"),
            )
            store.add_anomaly(anomaly_obj)
            anomaly_record = AnomalySchema(
                id=anomaly_obj.id, payment_id=anomaly_obj.payment_id,
                type=anomaly_obj.type, title=anomaly_obj.title,
                description=anomaly_obj.description, severity=anomaly_obj.severity,
                detected_at=anomaly_obj.detected_at, stage=anomaly_obj.stage,
                scope=anomaly_obj.scope, country=anomaly_obj.country,
                intermediary_bank=anomaly_obj.intermediary_bank,
                status=anomaly_obj.status, recommended_action=anomaly_obj.recommended_action,
                confidence=anomaly_obj.confidence, evidence_summary=anomaly_obj.evidence_summary,
            )

        # Build response
        payment_schema = self._to_payment_schema(payment)
        journey = journey_service.get_journey(payment.id)
        event_schemas = [
            PaymentEventSchema(
                id=e.id, payment_id=e.payment_id, timestamp=e.timestamp,
                stage=e.stage, event_type=e.event_type, status=e.status,
                message=e.message, details=e.details, actor=e.actor, severity=e.severity,
            )
            for e in events
        ]

        summary_parts = [f"Simulated payment {payment.payment_reference} via {' → '.join(route_path)}"]
        if anomaly_type:
            summary_parts.append(f"Anomaly: {anomaly_type.value} at {ANOMALY_CONFIGS[anomaly_type]['stage'].value}")
        summary_parts.append(f"Final status: {final_status.value}")

        return SimulationResponse(
            payment=payment_schema,
            journey=journey,
            events=event_schemas,
            anomaly=anomaly_record,
            summary=". ".join(summary_parts),
        )

    def replay(self, payment_id: str) -> SimulationResponse | None:
        original = store.get_payment(payment_id)
        if not original:
            return None

        return self.simulate(
            source_country=original.source_country,
            destination_country=original.destination_country,
            amount=original.amount,
            payment_type=original.payment_type,
            inject_anomaly=original.anomaly_type,
        )

    def _generate_sim_events(
        self, payment: Payment, target_stage: PaymentStage,
        anomaly_type: AnomalyType | None, rng: random.Random, base_time: datetime,
    ) -> list[PaymentEvent]:
        events = []
        t = base_time
        anomaly_stage = ANOMALY_CONFIGS[anomaly_type]["stage"] if anomaly_type else None

        for stage in STAGE_ORDER:
            if stage == PaymentStage.COMPLETED:
                if target_stage == PaymentStage.COMPLETED:
                    events.append(PaymentEvent(
                        payment_id=payment.id, timestamp=t, stage=stage,
                        event_type=EventType.STAGE_TRANSITION, status=PaymentStatus.COMPLETED,
                        message="Payment completed successfully", actor="settlement-engine",
                    ))
                break

            t += timedelta(seconds=rng.randint(3, 60))

            if anomaly_stage and stage == anomaly_stage:
                events.append(PaymentEvent(
                    payment_id=payment.id, timestamp=t, stage=stage,
                    event_type=EventType.ANOMALY_DETECTED,
                    status=PaymentStatus.ON_HOLD,
                    message=f"Anomaly: {anomaly_type.value}",
                    actor="monitoring-engine",
                    severity=ANOMALY_CONFIGS[anomaly_type]["severity"],
                ))
                if target_stage in (PaymentStage.FAILED, PaymentStage.ON_HOLD):
                    break
                if target_stage == PaymentStage.COMPLETED or STAGE_ORDER.index(target_stage) > STAGE_ORDER.index(stage):
                    t += timedelta(seconds=rng.randint(30, 300))
                    events.append(PaymentEvent(
                        payment_id=payment.id, timestamp=t, stage=stage,
                        event_type=EventType.RETRY_ATTEMPTED, status=PaymentStatus.IN_PROGRESS,
                        message="Issue resolved, continuing", actor="ops-engine",
                    ))
                else:
                    break
            else:
                events.append(PaymentEvent(
                    payment_id=payment.id, timestamp=t, stage=stage,
                    event_type=EventType.STAGE_TRANSITION, status=PaymentStatus.IN_PROGRESS,
                    message=f"Processing {stage.value}", actor="system",
                ))

            if stage == target_stage and target_stage != PaymentStage.COMPLETED:
                break

        # Add logs
        for ev in events:
            store.add_log(PaymentLog(
                payment_id=payment.id, timestamp=ev.timestamp,
                log_level=LogLevel.INFO, component=ev.actor,
                message=f"[{ev.stage.value}] {ev.message}",
                context={"event_id": ev.id},
            ))

        return events

    def _to_payment_schema(self, p: Payment) -> PaymentSchema:
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
            stage_timings=getattr(p, 'stage_timings', {}),
            stage_entry_times=getattr(p, 'stage_entry_times', {}),
            expected_stage_durations=getattr(p, 'expected_stage_durations', {}),
            retry_counts=getattr(p, 'retry_counts', {}),
            queue_wait_seconds=getattr(p, 'queue_wait_seconds', {}),
            sla_breach=getattr(p, 'sla_breach', False),
            sla_breach_seconds=getattr(p, 'sla_breach_seconds', None),
            bottleneck_stage=getattr(p, 'bottleneck_stage', None),
            bottleneck_node=getattr(p, 'bottleneck_node', None),
            total_processing_seconds=getattr(p, 'total_processing_seconds', None),
            escalation_flag=getattr(p, 'escalation_flag', False),
            operator_intervention=getattr(p, 'operator_intervention', False),
            recovered=getattr(p, 'recovered', False),
        )


    def simulate_advanced(
        self,
        source_country: str | None = None,
        destination_country: str | None = None,
        amount: float | None = None,
        priority: PaymentPriority | None = None,
        payment_type: PaymentType | None = None,
        force_scenario: str | None = None,
        inject_anomaly: AnomalyType | None = None,
        inject_delay_node: str | None = None,
    ) -> AdvancedSimulationResponse:
        rng = random.Random()
        now = datetime.utcnow()

        # Resolve anomaly from force_scenario
        SCENARIO_MAP = {
            "sanctions_false_positive": AnomalyType.SANCTIONS_FALSE_POSITIVE,
            "gateway_timeout": AnomalyType.GATEWAY_TIMEOUT,
            "validation_failure": AnomalyType.VALIDATION_ERROR,
            "fx_delay": AnomalyType.FX_DELAY,
            "settlement_delay": AnomalyType.SETTLEMENT_DELAY,
            "reconciliation_mismatch": AnomalyType.RECONCILIATION_MISMATCH,
            "missing_intermediary": AnomalyType.MISSING_INTERMEDIARY,
        }
        if force_scenario and not inject_anomaly:
            inject_anomaly = SCENARIO_MAP.get(force_scenario)

        # Pick corridor
        if source_country and destination_country:
            matching = [c for c in CORRIDORS if c["src"] == source_country and c["dst"] == destination_country]
            corridor = matching[0] if matching else {"src": source_country, "dst": destination_country, "intermediaries": [], "rail": "SWIFT"}
        else:
            corridor = rng.choice(CORRIDORS)

        src = corridor["src"]
        dst = corridor["dst"]
        src_curr = get_currency(src)
        dst_curr = get_currency(dst)
        amt = amount or round(rng.uniform(10000, 2000000), 2)
        fx_rate = _get_fx_rate(src_curr, dst_curr)
        route_path = [src] + corridor.get("intermediaries", []) + [dst]
        rt = (RouteType.DIRECT if len(route_path) == 2
              else (RouteType.INTERMEDIARY if len(route_path) == 3 else RouteType.MULTI_HOP))

        anomaly_type = inject_anomaly
        if not anomaly_type and rng.random() < 0.25:
            anomaly_type = rng.choice(list(AnomalyType))

        # Determine final state
        if anomaly_type:
            cfg = ANOMALY_CONFIGS[anomaly_type]
            target_stage = cfg["stage"]
            final_status = {
                AnomalyType.VALIDATION_ERROR: PaymentStatus.FAILED,
                AnomalyType.GATEWAY_TIMEOUT: PaymentStatus.DELAYED,
                AnomalyType.SETTLEMENT_DELAY: PaymentStatus.DELAYED,
                AnomalyType.FX_DELAY: PaymentStatus.COMPLETED,
            }.get(anomaly_type, PaymentStatus.ON_HOLD)
            if anomaly_type == AnomalyType.FX_DELAY:
                target_stage = PaymentStage.COMPLETED
        else:
            target_stage = PaymentStage.COMPLETED
            final_status = PaymentStatus.COMPLETED

        delay_node = inject_delay_node
        delay_country = None
        if not delay_node and anomaly_type in (AnomalyType.GATEWAY_TIMEOUT, AnomalyType.MISSING_INTERMEDIARY, AnomalyType.SETTLEMENT_DELAY):
            if corridor.get("intermediaries"):
                delay_country = rng.choice(corridor["intermediaries"])
                mb = [b for b in BANKS if b["country"] == delay_country]
                delay_node = mb[0]["name"] if mb else f"{delay_country} Gateway"
            else:
                delay_country = dst
                delay_node = f"{dst} Settlement Node"

        resolved_priority = priority or rng.choice(list(PaymentPriority))
        is_high_value = amt > 1_000_000
        recovered = anomaly_type == AnomalyType.FX_DELAY

        timing_data = _generate_stage_timings(target_stage, anomaly_type, rng, is_high_value, recovered)
        total_seconds = timing_data["total"]
        sla_breach, sla_breach_seconds = _compute_sla_breach(resolved_priority, total_seconds, anomaly_type is not None, rng)

        payment = Payment(
            payment_reference=f"SIM-ADV-{now.strftime('%Y%m%d%H%M%S')}-{src}{dst}",
            source_client_name=rng.choice(CLIENT_NAMES),
            beneficiary_name=rng.choice(BENEFICIARY_NAMES),
            source_country=src, destination_country=dst,
            source_currency=src_curr, destination_currency=dst_curr,
            amount=amt, fx_rate=fx_rate,
            send_amount=amt, receive_amount=round(amt * fx_rate, 2),
            corridor=f"{src}-{dst}",
            priority=resolved_priority,
            payment_type=payment_type or rng.choice(list(PaymentType)),
            current_stage=target_stage, current_status=final_status,
            anomaly_flag=anomaly_type is not None,
            anomaly_type=anomaly_type,
            anomaly_severity=ANOMALY_CONFIGS[anomaly_type]["severity"] if anomaly_type else None,
            anomaly_reason=ANOMALY_CONFIGS[anomaly_type]["desc"] if anomaly_type else None,
            created_at=now, updated_at=now,
            expected_completion_at=now + timedelta(hours=rng.randint(2, 24)),
            actual_completion_at=now if final_status == PaymentStatus.COMPLETED else None,
            route_type=rt, route_path=route_path,
            delay_node=delay_node, delay_country=delay_country,
            system_rail=corridor.get("rail", "SWIFT"),
            sanctions_hit=anomaly_type == AnomalyType.SANCTIONS_FALSE_POSITIVE,
            validation_error=anomaly_type == AnomalyType.VALIDATION_ERROR,
            gateway_timeout=anomaly_type == AnomalyType.GATEWAY_TIMEOUT,
            reconciliation_break=anomaly_type == AnomalyType.RECONCILIATION_MISMATCH,
            stage_timings=timing_data["timings"],
            expected_stage_durations=timing_data["expected"],
            retry_counts=timing_data["retries"],
            queue_wait_seconds=timing_data["queues"],
            bottleneck_stage=timing_data["bottleneck_stage"],
            bottleneck_node=delay_node if timing_data["bottleneck_stage"] else None,
            total_processing_seconds=total_seconds,
            sla_breach=sla_breach,
            sla_breach_seconds=sla_breach_seconds,
            recovered=recovered,
        )
        store.add_payment(payment)

        events = self._generate_sim_events(payment, target_stage, anomaly_type, rng, now)
        for ev in events:
            store.add_event(ev)

        anomaly_record = None
        if anomaly_type:
            cfg = ANOMALY_CONFIGS[anomaly_type]
            anomaly_obj = Anomaly(
                payment_id=payment.id, type=anomaly_type,
                title=cfg["title"], description=cfg["desc"],
                severity=cfg["severity"],
                detected_at=now + timedelta(seconds=rng.randint(10, 120)),
                stage=cfg["stage"], scope=cfg["scope"],
                country=delay_country or dst, intermediary_bank=delay_node,
                status=AnomalyStatus.RESOLVED if final_status == PaymentStatus.COMPLETED else AnomalyStatus.OPEN,
                recommended_action=cfg.get("recommended_action"),
                confidence=round(rng.uniform(0.72, 0.98), 2),
                evidence_summary=cfg.get("evidence"),
                anomaly_code=cfg.get("code"),
                root_symptom=cfg.get("root_symptom"),
                probable_cause=cfg.get("probable_cause"),
                corridor=f"{src}-{dst}",
                operational_impact_score=round(cfg.get("impact_score", 5.0), 1),
                resolution_eta_minutes=cfg.get("eta_minutes"),
                client_impact_level=cfg.get("client_impact"),
            )
            store.add_anomaly(anomaly_obj)
            anomaly_record = self._anomaly_to_schema(anomaly_obj)

        payment_schema = self._to_payment_schema(payment)
        journey = journey_service.get_journey(payment.id)
        event_schemas = [
            PaymentEventSchema(
                id=e.id, payment_id=e.payment_id, timestamp=e.timestamp,
                stage=e.stage, event_type=e.event_type, status=e.status,
                message=e.message, details=e.details, actor=e.actor, severity=e.severity,
            )
            for e in events
        ]

        # Build observability package
        from .observability_service import observability_service
        obs_pkg = observability_service.get_payment_observability(payment.id)

        # Execution explanation
        explanation = [f"Corridor: {src} → {dst} via {' → '.join(route_path)}"]
        explanation.append(f"Amount: {src_curr} {amt:,.2f} → {dst_curr} {round(amt * fx_rate, 2):,.2f} (rate: {fx_rate:.4f})")
        if anomaly_type:
            explanation.append(f"Anomaly injected: {anomaly_type.value} at {ANOMALY_CONFIGS[anomaly_type]['stage'].value}")
            explanation.append(f"Root symptom: {cfg.get('root_symptom', 'N/A')}")
        explanation.append(f"Total processing time: {round(total_seconds, 0):.0f}s")
        if sla_breach:
            explanation.append(f"⚠ SLA breached by {sla_breach_seconds:.0f}s ({resolved_priority.value} priority threshold)")
        if timing_data["bottleneck_stage"]:
            explanation.append(f"Bottleneck stage: {timing_data['bottleneck_stage']}")
        explanation.append(f"Final status: {final_status.value}")

        summary = f"Advanced simulation: {payment.payment_reference} | {src}→{dst} | {final_status.value}"
        if anomaly_type:
            summary += f" | {anomaly_type.value}"

        return AdvancedSimulationResponse(
            payment=payment_schema,
            journey=journey,
            events=event_schemas,
            anomaly=anomaly_record,
            observability=obs_pkg,
            summary=summary,
            execution_explanation=explanation,
        )

    def replay_advanced(
        self,
        payment_id: str,
        replay_mode: str = "original",
        override_anomaly: AnomalyType | None = None,
        override_severity: AnomalySeverity | None = None,
        inject_delay_node: str | None = None,
    ) -> ReplayComparisonResponse | None:
        original = store.get_payment(payment_id)
        if not original:
            return None

        # Determine replay anomaly
        if replay_mode == "original":
            replay_anomaly = original.anomaly_type
        elif replay_mode == "different_route":
            replay_anomaly = None
        elif replay_mode == "injected_compliance":
            replay_anomaly = AnomalyType.SANCTIONS_FALSE_POSITIVE
        elif replay_mode == "injected_delay":
            replay_anomaly = AnomalyType.GATEWAY_TIMEOUT
        else:
            replay_anomaly = override_anomaly or original.anomaly_type

        # Run the replay simulation
        replayed_response = self.simulate_advanced(
            source_country=original.source_country,
            destination_country=original.destination_country,
            amount=original.amount,
            priority=original.priority,
            payment_type=original.payment_type,
            inject_anomaly=replay_anomaly,
            inject_delay_node=inject_delay_node,
        )

        replayed_payment = store.get_payment(replayed_response.payment.id)
        replayed_anomalies = store.get_anomalies_for_payment(replayed_response.payment.id)
        original_anomalies = store.get_anomalies_for_payment(payment_id)

        original_schema = self._to_payment_schema(original)

        from .observability_service import observability_service
        original_obs = observability_service.get_payment_observability(payment_id)
        replayed_obs = replayed_response.observability

        orig_time = original.total_processing_seconds or 0
        rep_time = replayed_payment.total_processing_seconds if replayed_payment else 0
        timing_delta = round(rep_time - orig_time, 1) if orig_time else None

        status_changed = original.current_status != replayed_response.payment.current_status
        orig_anom_type = original.anomaly_type.value if original.anomaly_type else None
        rep_anom_type = replayed_response.anomaly.type.value if replayed_response.anomaly else None
        anomaly_changed = orig_anom_type != rep_anom_type

        path_changed = original.route_path != replayed_response.payment.route_path

        outcome_parts = []
        outcome_parts.append(f"Original: {original.current_status.value} | Replay: {replayed_response.payment.current_status.value}")
        if status_changed:
            outcome_parts.append("Status changed between runs.")
        if anomaly_changed:
            outcome_parts.append(f"Anomaly changed: {orig_anom_type or 'none'} → {rep_anom_type or 'none'}")
        if timing_delta is not None:
            direction = "faster" if timing_delta < 0 else "slower"
            outcome_parts.append(f"Replay was {abs(timing_delta):.0f}s {direction}")

        return ReplayComparisonResponse(
            original_payment_id=payment_id,
            replayed_payment_id=replayed_response.payment.id,
            original=original_schema,
            replayed=replayed_response.payment,
            original_anomaly=self._anomaly_to_schema(original_anomalies[0]) if original_anomalies else None,
            replayed_anomaly=replayed_response.anomaly,
            original_events=self._get_event_schemas(payment_id),
            replayed_events=replayed_response.events,
            original_observability=original_obs,
            replayed_observability=replayed_obs,
            status_changed=status_changed,
            anomaly_changed=anomaly_changed,
            timing_delta_seconds=timing_delta,
            outcome_summary=" | ".join(outcome_parts),
            path_changed=path_changed,
        )

    def _get_event_schemas(self, payment_id: str) -> list[PaymentEventSchema]:
        events = store.get_events(payment_id)
        return [
            PaymentEventSchema(
                id=e.id, payment_id=e.payment_id, timestamp=e.timestamp,
                stage=e.stage, event_type=e.event_type, status=e.status,
                message=e.message, details=e.details, actor=e.actor, severity=e.severity,
            )
            for e in events
        ]

    def _anomaly_to_schema(self, a) -> AnomalySchema:
        return AnomalySchema(
            id=a.id, payment_id=a.payment_id, type=a.type,
            title=a.title, description=a.description, severity=a.severity,
            detected_at=a.detected_at, stage=a.stage, scope=a.scope,
            country=a.country, intermediary_bank=a.intermediary_bank,
            status=a.status, recommended_action=a.recommended_action,
            confidence=a.confidence, evidence_summary=a.evidence_summary,
            anomaly_code=getattr(a, 'anomaly_code', None),
            root_symptom=getattr(a, 'root_symptom', None),
            probable_cause=getattr(a, 'probable_cause', None),
            first_detected_at=getattr(a, 'first_detected_at', None),
            last_updated_at=getattr(a, 'last_updated_at', None),
            impacted_node=getattr(a, 'impacted_node', None),
            corridor=getattr(a, 'corridor', None),
            operational_impact_score=getattr(a, 'operational_impact_score', None),
            action_status=getattr(a, 'action_status', None),
            resolution_eta_minutes=getattr(a, 'resolution_eta_minutes', None),
            recurrence_count=getattr(a, 'recurrence_count', 0),
            client_impact_level=getattr(a, 'client_impact_level', None),
        )


simulation_service = SimulationService()

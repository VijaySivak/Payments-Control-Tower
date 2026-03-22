"""Deterministic seed data generator for realistic cross-border payment scenarios."""

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
    NodeType,
    PaymentPriority,
    PaymentStage,
    PaymentStatus,
    PaymentType,
    RouteType,
    STAGE_ORDER,
)
from ..domain.models import (
    Anomaly,
    IntermediaryNode,
    Payment,
    PaymentEvent,
    PaymentLog,
    new_id,
)
from ..repositories.memory_store import store
from ..utils.geo import get_currency, COUNTRY_COORDS

SEED = 42

# ── Corridor definitions ────────────────────────────────────────

CORRIDORS = [
    {"src": "US", "dst": "GB", "intermediaries": []},
    {"src": "US", "dst": "AE", "intermediaries": ["GB"]},
    {"src": "US", "dst": "IN", "intermediaries": ["GB", "SG"]},
    {"src": "US", "dst": "JP", "intermediaries": []},
    {"src": "DE", "dst": "SG", "intermediaries": []},
    {"src": "DE", "dst": "AU", "intermediaries": ["SG"]},
    {"src": "DE", "dst": "IN", "intermediaries": ["CH"]},
    {"src": "GB", "dst": "HK", "intermediaries": ["SG"]},
    {"src": "GB", "dst": "NG", "intermediaries": []},
    {"src": "GB", "dst": "KE", "intermediaries": ["ZA"]},
    {"src": "FR", "dst": "BR", "intermediaries": ["US"]},
    {"src": "JP", "dst": "AU", "intermediaries": ["SG"]},
    {"src": "SG", "dst": "IN", "intermediaries": []},
    {"src": "CH", "dst": "SA", "intermediaries": ["AE"]},
    {"src": "CA", "dst": "MX", "intermediaries": []},
    {"src": "US", "dst": "DE", "intermediaries": []},
    {"src": "HK", "dst": "GB", "intermediaries": []},
    {"src": "AU", "dst": "NZ", "intermediaries": []},
    {"src": "NL", "dst": "ID", "intermediaries": ["SG"]},
    {"src": "SE", "dst": "PH", "intermediaries": ["SG"]},
]

CLIENT_NAMES = [
    "Meridian Capital Partners", "Atlas Global Trading", "Zenith Commodities Ltd",
    "Pacific Rim Holdings", "Nordic Industrial Group", "Sahara Energy Corp",
    "Evergreen Shipping Co", "Pinnacle Financial Services", "Silverstone Mining",
    "Vanguard Technologies", "BlueStar Pharmaceuticals", "Orion Manufacturing",
    "Crescent Ventures", "Titan Heavy Industries", "Nexus Digital Solutions",
    "Apex Logistics International", "Summit Resource Partners", "Ember Technologies",
    "Cobalt Capital Management", "Horizon Healthcare Group",
]

BENEFICIARY_NAMES = [
    "Shanghai Export Corp", "Mumbai Trade Finance Ltd", "Lagos Commercial Bank",
    "Dubai International Holdings", "Tokyo Electronics Co", "Berlin Automotive GmbH",
    "Singapore Freight Services", "Sydney Mining Operations", "Nairobi Agricultural Export",
    "Zurich Private Wealth", "São Paulo Trading SA", "Seoul Semiconductor Inc",
    "Amsterdam Port Authority", "Stockholm Clean Energy AB", "Manila BPO Services",
    "Jakarta Palm Oil Trading", "Mexico City Manufacturing SA", "Cape Town Logistics",
    "Auckland Dairy Exports", "Hong Kong Fintech Ltd",
]

BANKS = [
    {"name": "JPMorgan Chase", "country": "US", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "HSBC Holdings", "country": "GB", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "Deutsche Bank", "country": "DE", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "DBS Bank", "country": "SG", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "Standard Chartered", "country": "HK", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "BNP Paribas", "country": "FR", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "UBS Group", "country": "CH", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "Mizuho Financial", "country": "JP", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "Emirates NBD", "country": "AE", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "ANZ Banking Group", "country": "AU", "type": NodeType.CORRESPONDENT_BANK},
    {"name": "SWIFT Gateway EU", "country": "BE", "type": NodeType.GATEWAY},
    {"name": "SWIFT Gateway APAC", "country": "SG", "type": NodeType.GATEWAY},
    {"name": "Refinitiv Compliance Hub", "country": "GB", "type": NodeType.COMPLIANCE_HUB},
    {"name": "CLS Settlement", "country": "US", "type": NodeType.SETTLEMENT_NETWORK},
    {"name": "CHIPS Network", "country": "US", "type": NodeType.SETTLEMENT_NETWORK},
]

ANOMALY_CONFIGS = {
    AnomalyType.SANCTIONS_FALSE_POSITIVE: {
        "stage": PaymentStage.COMPLIANCE,
        "title": "Sanctions screening false positive",
        "desc": "Payment flagged by sanctions screening engine due to partial name match with OFAC/EU sanctions list. Manual review required.",
        "severity": AnomalySeverity.HIGH,
        "scope": AnomalyScope.PAYMENT,
        "recommended_action": "Review sanctions hit details and clear if false positive. Escalate to compliance officer if uncertain.",
        "evidence": "Name similarity score 0.87 against SDN list entry. Beneficiary country risk: elevated.",
    },
    AnomalyType.GATEWAY_TIMEOUT: {
        "stage": PaymentStage.ROUTING,
        "title": "Payment gateway timeout",
        "desc": "Routing gateway did not respond within SLA threshold. Payment queued for retry.",
        "severity": AnomalySeverity.MEDIUM,
        "scope": AnomalyScope.SYSTEM,
        "recommended_action": "Check gateway health status. Retry automatically or switch to backup route.",
        "evidence": "Gateway response time exceeded 30s threshold. 3 retry attempts exhausted.",
    },
    AnomalyType.VALIDATION_ERROR: {
        "stage": PaymentStage.VALIDATION,
        "title": "Payment validation failure",
        "desc": "Payment failed validation checks. Missing or invalid beneficiary account details.",
        "severity": AnomalySeverity.MEDIUM,
        "scope": AnomalyScope.PAYMENT,
        "recommended_action": "Request corrected beneficiary details from originator. Validate IBAN/SWIFT format.",
        "evidence": "IBAN checksum validation failed. Account number format does not match destination country standards.",
    },
    AnomalyType.FX_DELAY: {
        "stage": PaymentStage.FX,
        "title": "FX conversion delay",
        "desc": "Foreign exchange rate lock expired. Awaiting new quote from FX provider.",
        "severity": AnomalySeverity.LOW,
        "scope": AnomalyScope.CORRIDOR,
        "recommended_action": "Request fresh FX quote. Consider pre-locked rate for high-priority payments.",
        "evidence": "FX rate lock expired after 15-minute window. Market volatility index elevated.",
    },
    AnomalyType.MISSING_INTERMEDIARY: {
        "stage": PaymentStage.ROUTING,
        "title": "Missing intermediary bank",
        "desc": "No available correspondent bank found for the specified route. Payment requires manual routing.",
        "severity": AnomalySeverity.HIGH,
        "scope": AnomalyScope.CORRIDOR,
        "recommended_action": "Identify alternative correspondent bank or route. Escalate to treasury operations.",
        "evidence": "Primary correspondent bank relationship inactive. No fallback route configured.",
    },
    AnomalyType.SETTLEMENT_DELAY: {
        "stage": PaymentStage.SETTLEMENT,
        "title": "Settlement processing delay",
        "desc": "Settlement confirmation not received within expected timeframe from settlement network.",
        "severity": AnomalySeverity.MEDIUM,
        "scope": AnomalyScope.SYSTEM,
        "recommended_action": "Check settlement network status. Contact settlement operations for status update.",
        "evidence": "Settlement confirmation pending for >4 hours. Network status: degraded performance.",
    },
    AnomalyType.RECONCILIATION_MISMATCH: {
        "stage": PaymentStage.RECONCILIATION,
        "title": "Reconciliation amount mismatch",
        "desc": "Settled amount does not match expected amount after FX conversion. Variance exceeds tolerance.",
        "severity": AnomalySeverity.CRITICAL,
        "scope": AnomalyScope.PAYMENT,
        "recommended_action": "Investigate FX rate applied vs quoted. Raise exception with settlement team.",
        "evidence": "Expected: $50,245.00, Settled: $50,198.50. Variance: $46.50 (0.09%). Threshold: 0.05%.",
    },
}

FX_RATES = {
    ("USD", "GBP"): 0.79, ("USD", "EUR"): 0.92, ("USD", "JPY"): 149.50,
    ("USD", "AED"): 3.67, ("USD", "INR"): 83.12, ("USD", "SGD"): 1.34,
    ("USD", "AUD"): 1.53, ("USD", "CNY"): 7.24, ("USD", "HKD"): 7.82,
    ("USD", "CHF"): 0.88, ("USD", "BRL"): 4.97, ("USD", "CAD"): 1.36,
    ("USD", "MXN"): 17.15, ("USD", "ZAR"): 18.72, ("USD", "NGN"): 770.0,
    ("USD", "KES"): 153.50, ("USD", "SAR"): 3.75, ("USD", "KRW"): 1320.0,
    ("USD", "SEK"): 10.45, ("USD", "PHP"): 55.80, ("USD", "MYR"): 4.72,
    ("USD", "THB"): 35.60, ("USD", "IDR"): 15450.0, ("USD", "PLN"): 4.02,
    ("USD", "TRY"): 27.50, ("USD", "EGP"): 30.90, ("USD", "NZD"): 1.63,
    ("USD", "DKK"): 6.88, ("USD", "NOK"): 10.55, ("USD", "ILS"): 3.62,
    ("USD", "TWD"): 31.50, ("USD", "CLP"): 880.0, ("USD", "COP"): 3950.0,
    ("USD", "PEN"): 3.72, ("USD", "ARS"): 350.0,
    ("GBP", "USD"): 1.27, ("EUR", "USD"): 1.09, ("EUR", "GBP"): 0.86,
    ("GBP", "EUR"): 1.16, ("EUR", "SGD"): 1.46, ("EUR", "INR"): 90.60,
    ("EUR", "AUD"): 1.67, ("EUR", "CHF"): 0.96, ("EUR", "BRL"): 5.42,
    ("GBP", "NGN"): 977.0, ("GBP", "KES"): 195.0, ("GBP", "HKD"): 9.93,
    ("GBP", "ZAR"): 23.78, ("JPY", "AUD"): 0.0102, ("SGD", "INR"): 62.03,
    ("CHF", "SAR"): 4.26, ("CHF", "AED"): 4.17, ("CAD", "MXN"): 12.61,
    ("EUR", "IDR"): 16840.0, ("SEK", "PHP"): 5.34, ("AUD", "NZD"): 1.07,
    ("HKD", "GBP"): 0.101, ("NLD", "IDR"): 16840.0,
}


def _get_fx_rate(src_curr: str, dst_curr: str) -> float:
    if src_curr == dst_curr:
        return 1.0
    rate = FX_RATES.get((src_curr, dst_curr))
    if rate:
        return rate
    inverse = FX_RATES.get((dst_curr, src_curr))
    if inverse:
        return 1.0 / inverse
    return 1.0


def _build_route_path(corridor: dict) -> list[str]:
    path = [corridor["src"]]
    for inter in corridor.get("intermediaries", []):
        path.append(inter)
    path.append(corridor["dst"])
    return path


def _pick_payment_type(rng: random.Random) -> PaymentType:
    return rng.choice([PaymentType.SWIFT, PaymentType.WIRE, PaymentType.SEPA, PaymentType.RTGS, PaymentType.INSTANT])


def _pick_priority(rng: random.Random) -> PaymentPriority:
    return rng.choices(
        [PaymentPriority.LOW, PaymentPriority.MEDIUM, PaymentPriority.HIGH, PaymentPriority.CRITICAL],
        weights=[15, 40, 30, 15],
    )[0]


def _generate_events_for_payment(
    payment: Payment,
    target_stage: PaymentStage,
    anomaly_stage: PaymentStage | None,
    anomaly_type: AnomalyType | None,
    rng: random.Random,
    base_time: datetime,
) -> list[PaymentEvent]:
    events: list[PaymentEvent] = []
    t = base_time

    for stage in STAGE_ORDER:
        if stage == PaymentStage.COMPLETED:
            if target_stage == PaymentStage.COMPLETED:
                events.append(PaymentEvent(
                    payment_id=payment.id, timestamp=t, stage=stage,
                    event_type=EventType.STAGE_TRANSITION, status=PaymentStatus.COMPLETED,
                    message=f"Payment completed successfully", actor="settlement-engine",
                ))
            break

        t += timedelta(seconds=rng.randint(5, 120))

        if anomaly_stage and stage == anomaly_stage:
            events.append(PaymentEvent(
                payment_id=payment.id, timestamp=t, stage=stage,
                event_type=EventType.ANOMALY_DETECTED,
                status=PaymentStatus.ON_HOLD if anomaly_type != AnomalyType.GATEWAY_TIMEOUT else PaymentStatus.DELAYED,
                message=f"Anomaly detected at {stage.value}: {anomaly_type.value if anomaly_type else 'unknown'}",
                actor="monitoring-engine",
                severity=ANOMALY_CONFIGS[anomaly_type]["severity"] if anomaly_type else None,
                details={"anomaly_type": anomaly_type.value if anomaly_type else None},
            ))
            if target_stage in (PaymentStage.FAILED, PaymentStage.ON_HOLD):
                break
            t += timedelta(seconds=rng.randint(60, 600))
            events.append(PaymentEvent(
                payment_id=payment.id, timestamp=t, stage=stage,
                event_type=EventType.RETRY_ATTEMPTED,
                status=PaymentStatus.IN_PROGRESS,
                message=f"Retry/resolution attempted for {anomaly_type.value if anomaly_type else 'issue'}",
                actor="ops-engine",
            ))
        else:
            event_map = {
                PaymentStage.INITIATED: (EventType.STAGE_TRANSITION, "Payment initiated and queued", "intake-service"),
                PaymentStage.VALIDATION: (EventType.STAGE_TRANSITION, "Payment validation passed", "validation-engine"),
                PaymentStage.COMPLIANCE: (EventType.COMPLIANCE_CHECK, "Compliance screening completed", "compliance-engine"),
                PaymentStage.FX: (EventType.FX_QUOTE, f"FX rate locked: {payment.fx_rate:.4f}", "fx-engine"),
                PaymentStage.ROUTING: (EventType.ROUTE_SELECTED, f"Route selected: {' -> '.join(payment.route_path)}", "routing-engine"),
                PaymentStage.SETTLEMENT: (EventType.SETTLEMENT_INITIATED, "Settlement instruction sent", "settlement-engine"),
                PaymentStage.RECONCILIATION: (EventType.RECONCILIATION_CHECK, "Reconciliation check completed", "recon-engine"),
            }
            et, msg, actor = event_map.get(stage, (EventType.STAGE_TRANSITION, f"Processing {stage.value}", "system"))
            events.append(PaymentEvent(
                payment_id=payment.id, timestamp=t, stage=stage,
                event_type=et, status=PaymentStatus.IN_PROGRESS,
                message=msg, actor=actor,
            ))

        if stage == target_stage and target_stage not in (PaymentStage.COMPLETED, PaymentStage.FAILED):
            break

    return events


def _generate_logs_for_payment(
    payment: Payment,
    events: list[PaymentEvent],
    rng: random.Random,
) -> list[PaymentLog]:
    logs: list[PaymentLog] = []
    components = ["intake-service", "validation-engine", "compliance-engine", "fx-engine",
                  "routing-engine", "settlement-engine", "recon-engine", "monitoring-engine"]

    for event in events:
        logs.append(PaymentLog(
            payment_id=payment.id,
            timestamp=event.timestamp - timedelta(milliseconds=rng.randint(10, 500)),
            log_level=LogLevel.INFO,
            component=event.actor,
            message=f"[{event.stage.value}] {event.message}",
            context={"event_id": event.id, "stage": event.stage.value},
        ))
        if event.event_type == EventType.ANOMALY_DETECTED:
            logs.append(PaymentLog(
                payment_id=payment.id,
                timestamp=event.timestamp + timedelta(milliseconds=rng.randint(10, 200)),
                log_level=LogLevel.WARNING,
                component="monitoring-engine",
                message=f"Anomaly alert raised for payment {payment.payment_reference}",
                context={"anomaly_type": event.details.get("anomaly_type"), "payment_id": payment.id},
            ))
        if rng.random() < 0.3:
            logs.append(PaymentLog(
                payment_id=payment.id,
                timestamp=event.timestamp + timedelta(milliseconds=rng.randint(50, 1000)),
                log_level=rng.choice([LogLevel.DEBUG, LogLevel.INFO]),
                component=rng.choice(components),
                message=f"Processing metric captured for stage {event.stage.value}",
                context={"latency_ms": rng.randint(5, 500)},
            ))

    return logs


def seed_data(num_payments: int = 75) -> None:
    """Generate and store realistic seeded payment data."""
    rng = random.Random(SEED)
    now = datetime.utcnow()

    # Seed intermediary nodes
    for bank in BANKS:
        node = IntermediaryNode(
            bank_name=bank["name"],
            country=bank["country"],
            node_type=bank["type"],
            latency_score=round(rng.uniform(10, 500), 1),
            risk_score=round(rng.uniform(0.01, 0.5), 3),
        )
        store.add_node(node)

    # Define scenario distribution
    # ~50% completed, ~15% in-progress, ~20% anomalous, ~8% failed, ~7% on-hold
    scenarios: list[dict[str, Any]] = []

    # Completed payments
    for i in range(int(num_payments * 0.50)):
        scenarios.append({"target_stage": PaymentStage.COMPLETED, "anomaly": None, "final_status": PaymentStatus.COMPLETED})

    # In-progress at various stages
    active_stages = [PaymentStage.VALIDATION, PaymentStage.COMPLIANCE, PaymentStage.FX,
                     PaymentStage.ROUTING, PaymentStage.SETTLEMENT, PaymentStage.RECONCILIATION]
    for i in range(int(num_payments * 0.15)):
        scenarios.append({"target_stage": rng.choice(active_stages), "anomaly": None, "final_status": PaymentStatus.IN_PROGRESS})

    # Anomalous - sanctions false positive
    for i in range(max(3, int(num_payments * 0.06))):
        scenarios.append({"target_stage": PaymentStage.COMPLIANCE, "anomaly": AnomalyType.SANCTIONS_FALSE_POSITIVE, "final_status": PaymentStatus.ON_HOLD})

    # Anomalous - gateway timeout
    for i in range(max(3, int(num_payments * 0.06))):
        scenarios.append({"target_stage": PaymentStage.ROUTING, "anomaly": AnomalyType.GATEWAY_TIMEOUT, "final_status": PaymentStatus.DELAYED})

    # Anomalous - validation error
    for i in range(max(2, int(num_payments * 0.04))):
        scenarios.append({"target_stage": PaymentStage.VALIDATION, "anomaly": AnomalyType.VALIDATION_ERROR, "final_status": PaymentStatus.FAILED})

    # Anomalous - FX delay (resolved, completed)
    for i in range(max(1, int(num_payments * 0.03))):
        scenarios.append({"target_stage": PaymentStage.COMPLETED, "anomaly": AnomalyType.FX_DELAY, "final_status": PaymentStatus.COMPLETED})

    # Anomalous - settlement delay
    for i in range(max(1, int(num_payments * 0.03))):
        scenarios.append({"target_stage": PaymentStage.SETTLEMENT, "anomaly": AnomalyType.SETTLEMENT_DELAY, "final_status": PaymentStatus.DELAYED})

    # Anomalous - reconciliation mismatch
    for i in range(max(1, int(num_payments * 0.02))):
        scenarios.append({"target_stage": PaymentStage.RECONCILIATION, "anomaly": AnomalyType.RECONCILIATION_MISMATCH, "final_status": PaymentStatus.ON_HOLD})

    # Anomalous - missing intermediary
    for i in range(max(1, int(num_payments * 0.02))):
        scenarios.append({"target_stage": PaymentStage.ROUTING, "anomaly": AnomalyType.MISSING_INTERMEDIARY, "final_status": PaymentStatus.FAILED})

    # Failed payments
    remaining = num_payments - len(scenarios)
    for i in range(remaining):
        scenarios.append({"target_stage": PaymentStage.FAILED, "anomaly": None, "final_status": PaymentStatus.FAILED})

    rng.shuffle(scenarios)

    for idx, scenario in enumerate(scenarios[:num_payments]):
        corridor = rng.choice(CORRIDORS)
        src = corridor["src"]
        dst = corridor["dst"]
        src_curr = get_currency(src)
        dst_curr = get_currency(dst)
        amount = round(rng.uniform(5000, 5000000), 2)
        fx_rate = _get_fx_rate(src_curr, dst_curr)
        send_amount = amount
        receive_amount = round(amount * fx_rate, 2)
        route_path = _build_route_path(corridor)
        route_type = RouteType.DIRECT if len(route_path) == 2 else (RouteType.INTERMEDIARY if len(route_path) == 3 else RouteType.MULTI_HOP)

        anomaly_type = scenario.get("anomaly")
        target_stage = scenario["target_stage"]
        final_status = scenario["final_status"]

        delay_node = None
        delay_country = None
        if anomaly_type in (AnomalyType.GATEWAY_TIMEOUT, AnomalyType.MISSING_INTERMEDIARY, AnomalyType.SETTLEMENT_DELAY):
            if len(corridor.get("intermediaries", [])) > 0:
                delay_country = rng.choice(corridor["intermediaries"])
                matching = [b for b in BANKS if b["country"] == delay_country]
                delay_node = matching[0]["name"] if matching else f"{delay_country} Gateway"
            else:
                delay_country = dst
                delay_node = f"{dst} Settlement Node"

        created_at = now - timedelta(hours=rng.randint(1, 168), minutes=rng.randint(0, 59))
        expected_hours = rng.randint(2, 48)
        expected_completion = created_at + timedelta(hours=expected_hours)
        actual_completion = None
        if final_status == PaymentStatus.COMPLETED:
            actual_completion = created_at + timedelta(hours=rng.randint(1, expected_hours + 6))

        payment = Payment(
            payment_reference=f"PAY-{2024}{(idx + 1):04d}-{src}{dst}",
            source_client_name=rng.choice(CLIENT_NAMES),
            beneficiary_name=rng.choice(BENEFICIARY_NAMES),
            source_country=src,
            destination_country=dst,
            source_currency=src_curr,
            destination_currency=dst_curr,
            amount=amount,
            fx_rate=fx_rate,
            send_amount=send_amount,
            receive_amount=receive_amount,
            corridor=f"{src}-{dst}",
            priority=_pick_priority(rng),
            payment_type=_pick_payment_type(rng),
            current_stage=target_stage,
            current_status=final_status,
            anomaly_flag=anomaly_type is not None,
            anomaly_type=anomaly_type,
            anomaly_severity=ANOMALY_CONFIGS[anomaly_type]["severity"] if anomaly_type else None,
            anomaly_reason=ANOMALY_CONFIGS[anomaly_type]["desc"] if anomaly_type else None,
            created_at=created_at,
            updated_at=created_at + timedelta(minutes=rng.randint(5, 300)),
            expected_completion_at=expected_completion,
            actual_completion_at=actual_completion,
            system_rail=rng.choice(["SWIFT", "CHIPS", "TARGET2", "CHAPS", "Fedwire"]),
            route_type=route_type,
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
        anomaly_stage = ANOMALY_CONFIGS[anomaly_type]["stage"] if anomaly_type else None
        events = _generate_events_for_payment(payment, target_stage, anomaly_stage, anomaly_type, rng, created_at)
        for ev in events:
            store.add_event(ev)

        # Generate logs
        logs = _generate_logs_for_payment(payment, events, rng)
        for log in logs:
            store.add_log(log)

        # Generate anomaly record if applicable
        if anomaly_type:
            cfg = ANOMALY_CONFIGS[anomaly_type]
            anomaly = Anomaly(
                payment_id=payment.id,
                type=anomaly_type,
                title=cfg["title"],
                description=cfg["desc"],
                severity=cfg["severity"],
                detected_at=created_at + timedelta(minutes=rng.randint(5, 60)),
                stage=cfg["stage"],
                scope=cfg["scope"],
                country=delay_country or dst,
                intermediary_bank=delay_node,
                status=AnomalyStatus.RESOLVED if final_status == PaymentStatus.COMPLETED else rng.choice([AnomalyStatus.OPEN, AnomalyStatus.INVESTIGATING]),
                recommended_action=cfg.get("recommended_action"),
                confidence=round(rng.uniform(0.65, 0.98), 2),
                evidence_summary=cfg.get("evidence"),
            )
            store.add_anomaly(anomaly)

    print(f"[SEED] Generated {store.payment_count()} payments, {store.anomaly_count()} anomalies, {len(store.list_nodes())} nodes")

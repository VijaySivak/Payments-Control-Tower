"""Phase 2 enriched seed data generator with stage timings, SLA, observability."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from ..domain.enums import (
    ActionStatus,
    AnomalySeverity,
    AnomalyScope,
    AnomalyStatus,
    AnomalyType,
    EventType,
    LogLevel,
    NodeHealthStatus,
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

# ── Stage expected durations (seconds) ────────────────────────────────────────
STAGE_EXPECTED_DURATIONS = {
    PaymentStage.INITIATED:       30,
    PaymentStage.VALIDATION:      45,
    PaymentStage.COMPLIANCE:      120,
    PaymentStage.FX:              60,
    PaymentStage.ROUTING:         90,
    PaymentStage.SETTLEMENT:      300,
    PaymentStage.RECONCILIATION:  180,
    PaymentStage.COMPLETED:       10,
}

# ── Corridor definitions ───────────────────────────────────────────────────────
CORRIDORS = [
    {"src": "US", "dst": "GB", "intermediaries": [],            "rail": "SWIFT"},
    {"src": "US", "dst": "AE", "intermediaries": ["GB"],        "rail": "SWIFT"},
    {"src": "US", "dst": "IN", "intermediaries": ["GB", "SG"],  "rail": "SWIFT"},
    {"src": "US", "dst": "JP", "intermediaries": [],            "rail": "SWIFT"},
    {"src": "US", "dst": "DE", "intermediaries": [],            "rail": "TARGET2"},
    {"src": "US", "dst": "SG", "intermediaries": [],            "rail": "SWIFT"},
    {"src": "DE", "dst": "SG", "intermediaries": [],            "rail": "TARGET2"},
    {"src": "DE", "dst": "AU", "intermediaries": ["SG"],        "rail": "TARGET2"},
    {"src": "DE", "dst": "IN", "intermediaries": ["CH"],        "rail": "TARGET2"},
    {"src": "GB", "dst": "HK", "intermediaries": ["SG"],        "rail": "CHAPS"},
    {"src": "GB", "dst": "NG", "intermediaries": [],            "rail": "SWIFT"},
    {"src": "GB", "dst": "KE", "intermediaries": ["ZA"],        "rail": "SWIFT"},
    {"src": "GB", "dst": "IN", "intermediaries": [],            "rail": "CHAPS"},
    {"src": "FR", "dst": "BR", "intermediaries": ["US"],        "rail": "TARGET2"},
    {"src": "FR", "dst": "ZA", "intermediaries": [],            "rail": "TARGET2"},
    {"src": "JP", "dst": "AU", "intermediaries": ["SG"],        "rail": "Zengin"},
    {"src": "JP", "dst": "US", "intermediaries": [],            "rail": "Zengin"},
    {"src": "SG", "dst": "IN", "intermediaries": [],            "rail": "FAST"},
    {"src": "SG", "dst": "PH", "intermediaries": [],            "rail": "FAST"},
    {"src": "CH", "dst": "SA", "intermediaries": ["AE"],        "rail": "SIC"},
    {"src": "CH", "dst": "US", "intermediaries": [],            "rail": "SIC"},
    {"src": "CA", "dst": "MX", "intermediaries": [],            "rail": "Fedwire"},
    {"src": "CA", "dst": "IN", "intermediaries": ["GB"],        "rail": "Fedwire"},
    {"src": "HK", "dst": "GB", "intermediaries": [],            "rail": "CHATS"},
    {"src": "HK", "dst": "AU", "intermediaries": [],            "rail": "CHATS"},
    {"src": "AU", "dst": "NZ", "intermediaries": [],            "rail": "NPP"},
    {"src": "AU", "dst": "SG", "intermediaries": [],            "rail": "NPP"},
    {"src": "NL", "dst": "ID", "intermediaries": ["SG"],        "rail": "TARGET2"},
    {"src": "SE", "dst": "PH", "intermediaries": ["SG"],        "rail": "RIX"},
    {"src": "AE", "dst": "IN", "intermediaries": [],            "rail": "UAEFTS"},
    {"src": "ZA", "dst": "GB", "intermediaries": [],            "rail": "SWIFT"},
    {"src": "KR", "dst": "US", "intermediaries": [],            "rail": "BOK"},
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
    {"name": "JPMorgan Chase", "country": "US", "type": NodeType.CORRESPONDENT_BANK, "rails": ["SWIFT", "Fedwire", "CHIPS"]},
    {"name": "HSBC Holdings", "country": "GB", "type": NodeType.CORRESPONDENT_BANK, "rails": ["SWIFT", "CHAPS"]},
    {"name": "Deutsche Bank", "country": "DE", "type": NodeType.CORRESPONDENT_BANK, "rails": ["TARGET2", "SWIFT"]},
    {"name": "DBS Bank", "country": "SG", "type": NodeType.CORRESPONDENT_BANK, "rails": ["FAST", "SWIFT"]},
    {"name": "Standard Chartered", "country": "HK", "type": NodeType.CORRESPONDENT_BANK, "rails": ["CHATS", "SWIFT"]},
    {"name": "BNP Paribas", "country": "FR", "type": NodeType.CORRESPONDENT_BANK, "rails": ["TARGET2", "SWIFT"]},
    {"name": "UBS Group", "country": "CH", "type": NodeType.CORRESPONDENT_BANK, "rails": ["SIC", "SWIFT"]},
    {"name": "Mizuho Financial", "country": "JP", "type": NodeType.CORRESPONDENT_BANK, "rails": ["Zengin", "SWIFT"]},
    {"name": "Emirates NBD", "country": "AE", "type": NodeType.CORRESPONDENT_BANK, "rails": ["UAEFTS", "SWIFT"]},
    {"name": "ANZ Banking Group", "country": "AU", "type": NodeType.CORRESPONDENT_BANK, "rails": ["NPP", "SWIFT"]},
    {"name": "Nedbank", "country": "ZA", "type": NodeType.CORRESPONDENT_BANK, "rails": ["SWIFT"]},
    {"name": "State Bank of India", "country": "IN", "type": NodeType.CORRESPONDENT_BANK, "rails": ["NEFT", "SWIFT"]},
    {"name": "SWIFT Gateway EU", "country": "BE", "type": NodeType.GATEWAY, "rails": ["SWIFT"]},
    {"name": "SWIFT Gateway APAC", "country": "SG", "type": NodeType.GATEWAY, "rails": ["SWIFT"]},
    {"name": "Refinitiv Compliance Hub", "country": "GB", "type": NodeType.COMPLIANCE_HUB, "rails": ["SWIFT"]},
    {"name": "CLS Settlement", "country": "US", "type": NodeType.SETTLEMENT_NETWORK, "rails": ["Fedwire"]},
    {"name": "CHIPS Network", "country": "US", "type": NodeType.SETTLEMENT_NETWORK, "rails": ["CHIPS"]},
    {"name": "Euroclear", "country": "BE", "type": NodeType.CLEARING_HOUSE, "rails": ["TARGET2"]},
    {"name": "LCH Clearnet", "country": "GB", "type": NodeType.CLEARING_HOUSE, "rails": ["CHAPS"]},
    {"name": "Refinitiv FX All", "country": "US", "type": NodeType.FX_PROVIDER, "rails": ["SWIFT"]},
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
        "code": "COMP-001",
        "root_symptom": "Name match score exceeded threshold in OFAC screening",
        "probable_cause": "Partial name collision with sanctioned entity; likely false positive based on country and transaction profile",
        "impact_score": 7.5,
        "client_impact": "HIGH",
        "eta_minutes": 45,
    },
    AnomalyType.GATEWAY_TIMEOUT: {
        "stage": PaymentStage.ROUTING,
        "title": "Payment gateway timeout",
        "desc": "Routing gateway did not respond within SLA threshold. Payment queued for retry.",
        "severity": AnomalySeverity.MEDIUM,
        "scope": AnomalyScope.SYSTEM,
        "recommended_action": "Check gateway health status. Retry automatically or switch to backup route.",
        "evidence": "Gateway response time exceeded 30s threshold. 3 retry attempts exhausted.",
        "code": "ROUT-002",
        "root_symptom": "No response from routing gateway within 30s SLA",
        "probable_cause": "Gateway connectivity degradation or upstream network congestion",
        "impact_score": 5.5,
        "client_impact": "MEDIUM",
        "eta_minutes": 20,
    },
    AnomalyType.VALIDATION_ERROR: {
        "stage": PaymentStage.VALIDATION,
        "title": "Payment validation failure",
        "desc": "Payment failed validation checks. Missing or invalid beneficiary account details.",
        "severity": AnomalySeverity.MEDIUM,
        "scope": AnomalyScope.PAYMENT,
        "recommended_action": "Request corrected beneficiary details from originator. Validate IBAN/SWIFT format.",
        "evidence": "IBAN checksum validation failed. Account number format does not match destination country standards.",
        "code": "VAL-003",
        "root_symptom": "IBAN checksum failure on destination account",
        "probable_cause": "Incorrect account number provided by originating client; format mismatch for destination country",
        "impact_score": 4.0,
        "client_impact": "HIGH",
        "eta_minutes": 60,
    },
    AnomalyType.FX_DELAY: {
        "stage": PaymentStage.FX,
        "title": "FX conversion delay",
        "desc": "Foreign exchange rate lock expired. Awaiting new quote from FX provider.",
        "severity": AnomalySeverity.LOW,
        "scope": AnomalyScope.CORRIDOR,
        "recommended_action": "Request fresh FX quote. Consider pre-locked rate for high-priority payments.",
        "evidence": "FX rate lock expired after 15-minute window. Market volatility index elevated.",
        "code": "FX-004",
        "root_symptom": "FX rate lock window expired before settlement instruction sent",
        "probable_cause": "Processing delay in upstream stages caused lock to expire; elevated volatility extended queue",
        "impact_score": 2.5,
        "client_impact": "LOW",
        "eta_minutes": 15,
    },
    AnomalyType.MISSING_INTERMEDIARY: {
        "stage": PaymentStage.ROUTING,
        "title": "Missing intermediary bank",
        "desc": "No available correspondent bank found for the specified route. Payment requires manual routing.",
        "severity": AnomalySeverity.HIGH,
        "scope": AnomalyScope.CORRIDOR,
        "recommended_action": "Identify alternative correspondent bank or route. Escalate to treasury operations.",
        "evidence": "Primary correspondent bank relationship inactive. No fallback route configured.",
        "code": "ROUT-005",
        "root_symptom": "No active correspondent bank relationship for this corridor",
        "probable_cause": "Correspondent agreement suspended or expired; no fallback route in routing table",
        "impact_score": 8.0,
        "client_impact": "CRITICAL",
        "eta_minutes": 120,
    },
    AnomalyType.SETTLEMENT_DELAY: {
        "stage": PaymentStage.SETTLEMENT,
        "title": "Settlement processing delay",
        "desc": "Settlement confirmation not received within expected timeframe from settlement network.",
        "severity": AnomalySeverity.MEDIUM,
        "scope": AnomalyScope.SYSTEM,
        "recommended_action": "Check settlement network status. Contact settlement operations for status update.",
        "evidence": "Settlement confirmation pending for >4 hours. Network status: degraded performance.",
        "code": "SETT-006",
        "root_symptom": "Settlement confirmation not received within 4-hour SLA window",
        "probable_cause": "Settlement network operating in degraded mode; high queue volume during batch window",
        "impact_score": 6.0,
        "client_impact": "MEDIUM",
        "eta_minutes": 240,
    },
    AnomalyType.RECONCILIATION_MISMATCH: {
        "stage": PaymentStage.RECONCILIATION,
        "title": "Reconciliation amount mismatch",
        "desc": "Settled amount does not match expected amount after FX conversion. Variance exceeds tolerance.",
        "severity": AnomalySeverity.CRITICAL,
        "scope": AnomalyScope.PAYMENT,
        "recommended_action": "Investigate FX rate applied vs quoted. Raise exception with settlement team.",
        "evidence": "Expected: $50,245.00, Settled: $50,198.50. Variance: $46.50 (0.09%). Threshold: 0.05%.",
        "code": "RECON-007",
        "root_symptom": "Settled amount variance exceeds 0.05% tolerance threshold",
        "probable_cause": "FX rate slippage between quote and execution; possible rounding error in multi-hop FX chain",
        "impact_score": 9.0,
        "client_impact": "CRITICAL",
        "eta_minutes": 180,
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
    ("USD", "IDR"): 15450.0, ("USD", "NZD"): 1.63, ("USD", "DKK"): 6.88,
    ("GBP", "USD"): 1.27, ("EUR", "USD"): 1.09, ("EUR", "GBP"): 0.86,
    ("GBP", "EUR"): 1.16, ("EUR", "SGD"): 1.46, ("EUR", "INR"): 90.60,
    ("EUR", "AUD"): 1.67, ("EUR", "CHF"): 0.96, ("EUR", "BRL"): 5.42,
    ("GBP", "NGN"): 977.0, ("GBP", "KES"): 195.0, ("GBP", "HKD"): 9.93,
    ("GBP", "ZAR"): 23.78, ("JPY", "AUD"): 0.0102, ("SGD", "INR"): 62.03,
    ("CHF", "SAR"): 4.26, ("CHF", "AED"): 4.17, ("CAD", "MXN"): 12.61,
    ("EUR", "IDR"): 16840.0, ("SEK", "PHP"): 5.34, ("AUD", "NZD"): 1.07,
    ("HKD", "GBP"): 0.101, ("AED", "INR"): 22.65, ("ZAR", "GBP"): 0.042,
    ("KRW", "USD"): 0.00076,
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


def _pick_payment_type(rng: random.Random, rail: str) -> PaymentType:
    rail_map = {
        "SWIFT": [PaymentType.SWIFT, PaymentType.WIRE],
        "TARGET2": [PaymentType.SEPA, PaymentType.RTGS],
        "CHAPS": [PaymentType.WIRE, PaymentType.RTGS],
        "Fedwire": [PaymentType.WIRE, PaymentType.RTGS],
        "FAST": [PaymentType.INSTANT],
        "NPP": [PaymentType.INSTANT],
        "Zengin": [PaymentType.WIRE, PaymentType.RTGS],
        "SIC": [PaymentType.WIRE],
    }
    options = rail_map.get(rail, list(PaymentType))
    return rng.choice(options)


def _pick_priority(rng: random.Random, amount: float) -> PaymentPriority:
    if amount > 2000000:
        return rng.choices(
            [PaymentPriority.HIGH, PaymentPriority.CRITICAL],
            weights=[40, 60],
        )[0]
    return rng.choices(
        [PaymentPriority.LOW, PaymentPriority.MEDIUM, PaymentPriority.HIGH, PaymentPriority.CRITICAL],
        weights=[15, 40, 30, 15],
    )[0]


def _generate_stage_timings(
    target_stage: PaymentStage,
    anomaly_type: AnomalyType | None,
    rng: random.Random,
    is_high_value: bool,
    recovered: bool,
) -> dict:
    """Generate realistic stage timings with bottleneck identification."""
    timings: dict[str, float] = {}
    expected: dict[str, float] = {}
    retries: dict[str, int] = {}
    queues: dict[str, float] = {}

    active_stages = []
    for s in STAGE_ORDER:
        if s == PaymentStage.COMPLETED:
            if target_stage == PaymentStage.COMPLETED:
                active_stages.append(s)
            break
        active_stages.append(s)
        if s == target_stage:
            break

    anomaly_stage = ANOMALY_CONFIGS[anomaly_type]["stage"] if anomaly_type else None

    for stage in active_stages:
        exp = STAGE_EXPECTED_DURATIONS.get(stage, 60)
        expected[stage.value] = float(exp)
        queue_wait = round(rng.uniform(1, 15), 1)

        if stage == anomaly_stage:
            # Anomalous stage: much longer than expected
            multiplier = rng.uniform(3.0, 8.0) if not recovered else rng.uniform(2.0, 4.0)
            duration = round(exp * multiplier + rng.uniform(30, 180), 1)
            retry = rng.randint(1, 4) if anomaly_type in (AnomalyType.GATEWAY_TIMEOUT, AnomalyType.SETTLEMENT_DELAY) else 0
            queue_wait = round(rng.uniform(10, 60), 1)
        elif is_high_value and stage == PaymentStage.COMPLIANCE:
            # High value gets enhanced compliance screening
            multiplier = rng.uniform(1.5, 2.5)
            duration = round(exp * multiplier, 1)
            retry = 0
        else:
            # Normal: slight variance around expected
            multiplier = rng.uniform(0.7, 1.4)
            duration = round(exp * multiplier, 1)
            retry = 1 if rng.random() < 0.08 else 0

        timings[stage.value] = duration
        retries[stage.value] = retry
        queues[stage.value] = queue_wait

    # Identify bottleneck: stage with highest delta vs expected
    bottleneck_stage = None
    max_delta = 0.0
    for sv, dur in timings.items():
        exp_v = expected.get(sv, 60)
        delta = dur - exp_v
        if delta > max_delta:
            max_delta = delta
            bottleneck_stage = sv

    total = round(sum(timings.values()), 1)

    return {
        "timings": timings,
        "expected": expected,
        "retries": retries,
        "queues": queues,
        "bottleneck_stage": bottleneck_stage if max_delta > 30 else None,
        "total": total,
    }


def _generate_events_for_payment(
    payment: Payment,
    target_stage: PaymentStage,
    anomaly_stage: PaymentStage | None,
    anomaly_type: AnomalyType | None,
    rng: random.Random,
    base_time: datetime,
    recovered: bool = False,
) -> list[PaymentEvent]:
    events: list[PaymentEvent] = []
    t = base_time

    for stage in STAGE_ORDER:
        if stage == PaymentStage.COMPLETED:
            if target_stage == PaymentStage.COMPLETED:
                events.append(PaymentEvent(
                    payment_id=payment.id, timestamp=t, stage=stage,
                    event_type=EventType.STAGE_TRANSITION, status=PaymentStatus.COMPLETED,
                    message="Payment completed successfully", actor="settlement-engine",
                ))
            break

        stage_dur = payment.stage_timings.get(stage.value, rng.randint(5, 120))
        t += timedelta(seconds=stage_dur)

        if anomaly_stage and stage == anomaly_stage:
            events.append(PaymentEvent(
                payment_id=payment.id, timestamp=t, stage=stage,
                event_type=EventType.ANOMALY_DETECTED,
                status=PaymentStatus.ON_HOLD if anomaly_type != AnomalyType.GATEWAY_TIMEOUT else PaymentStatus.DELAYED,
                message=f"Anomaly detected at {stage.value}: {anomaly_type.value if anomaly_type else 'unknown'}",
                actor="monitoring-engine",
                severity=ANOMALY_CONFIGS[anomaly_type]["severity"] if anomaly_type else None,
                details={"anomaly_type": anomaly_type.value if anomaly_type else None, "code": ANOMALY_CONFIGS[anomaly_type].get("code")},
            ))
            retry_count = payment.retry_counts.get(stage.value, 0)
            if retry_count > 0:
                for r in range(retry_count):
                    t += timedelta(seconds=rng.randint(15, 90))
                    events.append(PaymentEvent(
                        payment_id=payment.id, timestamp=t, stage=stage,
                        event_type=EventType.RETRY_ATTEMPTED,
                        status=PaymentStatus.IN_PROGRESS,
                        message=f"Retry attempt {r+1} for {anomaly_type.value if anomaly_type else 'issue'}",
                        actor="ops-engine",
                        details={"attempt": r + 1},
                    ))
            if payment.escalation_flag:
                t += timedelta(seconds=rng.randint(60, 300))
                events.append(PaymentEvent(
                    payment_id=payment.id, timestamp=t, stage=stage,
                    event_type=EventType.ESCALATION, status=PaymentStatus.ON_HOLD,
                    message="Payment escalated to senior operations team",
                    actor="ops-manager",
                    details={"reason": "Anomaly unresolved after retries"},
                ))
            if payment.operator_intervention:
                t += timedelta(seconds=rng.randint(120, 600))
                events.append(PaymentEvent(
                    payment_id=payment.id, timestamp=t, stage=stage,
                    event_type=EventType.OPERATOR_INTERVENTION,
                    status=PaymentStatus.IN_PROGRESS,
                    message="Manual operator intervention applied",
                    actor="ops-team",
                    details={"action": "Override applied"},
                ))
            if target_stage in (PaymentStage.FAILED, PaymentStage.ON_HOLD):
                break
        else:
            event_map = {
                PaymentStage.INITIATED:      (EventType.STAGE_TRANSITION, "Payment initiated and queued", "intake-service"),
                PaymentStage.VALIDATION:     (EventType.STAGE_TRANSITION, "Payment validation passed", "validation-engine"),
                PaymentStage.COMPLIANCE:     (EventType.COMPLIANCE_CHECK, "Compliance screening completed", "compliance-engine"),
                PaymentStage.FX:             (EventType.FX_QUOTE, f"FX rate locked: {payment.fx_rate:.4f}", "fx-engine"),
                PaymentStage.ROUTING:        (EventType.ROUTE_SELECTED, f"Route selected: {' -> '.join(payment.route_path)}", "routing-engine"),
                PaymentStage.SETTLEMENT:     (EventType.SETTLEMENT_INITIATED, "Settlement instruction sent", "settlement-engine"),
                PaymentStage.RECONCILIATION: (EventType.RECONCILIATION_CHECK, "Reconciliation check completed", "recon-engine"),
            }
            et, msg, actor = event_map.get(stage, (EventType.STAGE_TRANSITION, f"Processing {stage.value}", "system"))
            events.append(PaymentEvent(
                payment_id=payment.id, timestamp=t, stage=stage,
                event_type=et, status=PaymentStatus.IN_PROGRESS,
                message=msg, actor=actor,
                details={"duration_ms": int(stage_dur * 1000), "stage": stage.value},
            ))

        if stage == target_stage and target_stage not in (PaymentStage.COMPLETED, PaymentStage.FAILED):
            if payment.sla_breach:
                events.append(PaymentEvent(
                    payment_id=payment.id, timestamp=t + timedelta(seconds=30),
                    stage=stage, event_type=EventType.SLA_BREACH,
                    status=payment.current_status,
                    message=f"SLA threshold breached at stage {stage.value}",
                    actor="sla-monitor",
                    severity=AnomalySeverity.HIGH,
                    details={"breach_seconds": payment.sla_breach_seconds},
                ))
            break

    return events


def _generate_logs_for_payment(
    payment: Payment,
    events: list[PaymentEvent],
    rng: random.Random,
) -> list[PaymentLog]:
    logs: list[PaymentLog] = []
    components = [
        "intake-service", "validation-engine", "compliance-engine", "fx-engine",
        "routing-engine", "settlement-engine", "recon-engine", "monitoring-engine",
        "sla-monitor", "ops-engine",
    ]

    for event in events:
        logs.append(PaymentLog(
            payment_id=payment.id,
            timestamp=event.timestamp - timedelta(milliseconds=rng.randint(10, 200)),
            log_level=LogLevel.INFO,
            component=event.actor,
            message=f"[{event.stage.value}] {event.message}",
            context={"event_id": event.id, "stage": event.stage.value, "event_type": event.event_type.value},
        ))

        if event.event_type == EventType.ANOMALY_DETECTED:
            logs.append(PaymentLog(
                payment_id=payment.id,
                timestamp=event.timestamp + timedelta(milliseconds=rng.randint(10, 100)),
                log_level=LogLevel.WARNING,
                component="monitoring-engine",
                message=f"Anomaly alert raised for payment {payment.payment_reference}",
                context={"anomaly_type": event.details.get("anomaly_type"), "code": event.details.get("code"), "payment_id": payment.id},
            ))

        if event.event_type == EventType.SLA_BREACH:
            logs.append(PaymentLog(
                payment_id=payment.id,
                timestamp=event.timestamp + timedelta(milliseconds=50),
                log_level=LogLevel.ERROR,
                component="sla-monitor",
                message=f"SLA BREACH: Payment {payment.payment_reference} exceeded stage SLA",
                context={"stage": event.stage.value, "breach_seconds": payment.sla_breach_seconds},
            ))

        if event.event_type == EventType.RETRY_ATTEMPTED:
            logs.append(PaymentLog(
                payment_id=payment.id,
                timestamp=event.timestamp,
                log_level=LogLevel.WARNING,
                component="ops-engine",
                message=f"Retry attempt for payment {payment.payment_reference} at {event.stage.value}",
                context={"attempt": event.details.get("attempt", 1)},
            ))

        # Add debug telemetry for stage transitions
        if event.event_type == EventType.STAGE_TRANSITION and rng.random() < 0.4:
            dur_ms = event.details.get("duration_ms", rng.randint(100, 5000))
            logs.append(PaymentLog(
                payment_id=payment.id,
                timestamp=event.timestamp + timedelta(milliseconds=rng.randint(50, 500)),
                log_level=LogLevel.DEBUG,
                component=rng.choice(components),
                message=f"Stage {event.stage.value} metrics captured",
                context={"latency_ms": dur_ms, "queue_depth": rng.randint(1, 50)},
            ))

    return logs


def _compute_sla_breach(
    payment_priority: PaymentPriority,
    total_seconds: float,
    has_anomaly: bool,
    rng: random.Random,
) -> tuple[bool, float | None]:
    """Determine SLA breach based on priority and processing time."""
    sla_thresholds = {
        PaymentPriority.CRITICAL: 3600,    # 1 hour
        PaymentPriority.HIGH: 7200,         # 2 hours
        PaymentPriority.MEDIUM: 14400,      # 4 hours
        PaymentPriority.LOW: 28800,         # 8 hours
    }
    threshold = sla_thresholds.get(payment_priority, 14400)
    if total_seconds > threshold:
        breach_sec = round(total_seconds - threshold, 1)
        return True, breach_sec
    # Anomaly payments more likely to breach even if within time
    if has_anomaly and rng.random() < 0.3:
        breach_sec = round(rng.uniform(60, 1800), 1)
        return True, breach_sec
    return False, None


def seed_data(num_payments: int = 100) -> None:
    """Generate Phase 2 enriched seed data."""
    rng = random.Random(SEED)
    now = datetime.utcnow()

    # Seed intermediary nodes with Phase 2 health data
    for bank in BANKS:
        latency = round(rng.uniform(15, 450), 1)
        risk = round(rng.uniform(0.01, 0.45), 3)
        # Assign health status based on latency/risk
        if latency > 350 or risk > 0.35:
            health = NodeHealthStatus.DEGRADED
        elif latency > 400 or risk > 0.42:
            health = NodeHealthStatus.CRITICAL
        else:
            health = NodeHealthStatus.HEALTHY

        node = IntermediaryNode(
            bank_name=bank["name"],
            country=bank["country"],
            node_type=bank["type"],
            latency_score=latency,
            risk_score=risk,
            health_status=health,
            avg_latency_ms=round(latency * 2.1, 1),
            p99_latency_ms=round(latency * 4.5, 1),
            supported_rails=bank.get("rails", []),
        )
        store.add_node(node)

    # Scenario distribution
    scenarios: list[dict[str, Any]] = []

    # Completed payments ~45%
    for _ in range(int(num_payments * 0.45)):
        scenarios.append({"target_stage": PaymentStage.COMPLETED, "anomaly": None, "final_status": PaymentStatus.COMPLETED})

    # In-progress at various stages ~12%
    active_stages = [PaymentStage.VALIDATION, PaymentStage.COMPLIANCE, PaymentStage.FX,
                     PaymentStage.ROUTING, PaymentStage.SETTLEMENT, PaymentStage.RECONCILIATION]
    for _ in range(int(num_payments * 0.12)):
        scenarios.append({"target_stage": rng.choice(active_stages), "anomaly": None, "final_status": PaymentStatus.IN_PROGRESS})

    # Sanctions false positive ~7%
    for _ in range(max(4, int(num_payments * 0.07))):
        scenarios.append({"target_stage": PaymentStage.COMPLIANCE, "anomaly": AnomalyType.SANCTIONS_FALSE_POSITIVE, "final_status": PaymentStatus.ON_HOLD})

    # Gateway timeout ~6%
    for _ in range(max(4, int(num_payments * 0.06))):
        scenarios.append({"target_stage": PaymentStage.ROUTING, "anomaly": AnomalyType.GATEWAY_TIMEOUT, "final_status": PaymentStatus.DELAYED})

    # Validation error ~5%
    for _ in range(max(3, int(num_payments * 0.05))):
        scenarios.append({"target_stage": PaymentStage.VALIDATION, "anomaly": AnomalyType.VALIDATION_ERROR, "final_status": PaymentStatus.FAILED})

    # FX delay - recovered and completed ~4%
    for _ in range(max(2, int(num_payments * 0.04))):
        scenarios.append({"target_stage": PaymentStage.COMPLETED, "anomaly": AnomalyType.FX_DELAY, "final_status": PaymentStatus.COMPLETED, "recovered": True})

    # Settlement delay ~4%
    for _ in range(max(2, int(num_payments * 0.04))):
        scenarios.append({"target_stage": PaymentStage.SETTLEMENT, "anomaly": AnomalyType.SETTLEMENT_DELAY, "final_status": PaymentStatus.DELAYED})

    # Reconciliation mismatch ~3%
    for _ in range(max(2, int(num_payments * 0.03))):
        scenarios.append({"target_stage": PaymentStage.RECONCILIATION, "anomaly": AnomalyType.RECONCILIATION_MISMATCH, "final_status": PaymentStatus.ON_HOLD})

    # Missing intermediary ~2%
    for _ in range(max(2, int(num_payments * 0.02))):
        scenarios.append({"target_stage": PaymentStage.ROUTING, "anomaly": AnomalyType.MISSING_INTERMEDIARY, "final_status": PaymentStatus.FAILED})

    # Almost failed but recovered (operator intervention) ~3%
    for _ in range(max(2, int(num_payments * 0.03))):
        anomaly = rng.choice([AnomalyType.GATEWAY_TIMEOUT, AnomalyType.SANCTIONS_FALSE_POSITIVE, AnomalyType.SETTLEMENT_DELAY])
        scenarios.append({
            "target_stage": PaymentStage.COMPLETED,
            "anomaly": anomaly,
            "final_status": PaymentStatus.COMPLETED,
            "recovered": True,
            "operator_intervention": True,
        })

    # Failed payments (no anomaly) - remaining
    remaining = num_payments - len(scenarios)
    for _ in range(max(0, remaining)):
        scenarios.append({"target_stage": PaymentStage.FAILED, "anomaly": None, "final_status": PaymentStatus.FAILED})

    rng.shuffle(scenarios)

    for idx, scenario in enumerate(scenarios[:num_payments]):
        corridor = rng.choice(CORRIDORS)
        src = corridor["src"]
        dst = corridor["dst"]
        src_curr = get_currency(src)
        dst_curr = get_currency(dst)

        # Amount: mix of small, medium, large, whale
        amount_tier = rng.choices(["small", "medium", "large", "whale"], weights=[20, 45, 25, 10])[0]
        amount = {
            "small": round(rng.uniform(5000, 100000), 2),
            "medium": round(rng.uniform(100000, 1000000), 2),
            "large": round(rng.uniform(1000000, 5000000), 2),
            "whale": round(rng.uniform(5000000, 25000000), 2),
        }[amount_tier]

        fx_rate = _get_fx_rate(src_curr, dst_curr)
        route_path = _build_route_path(corridor)
        route_type = (RouteType.DIRECT if len(route_path) == 2
                      else (RouteType.INTERMEDIARY if len(route_path) == 3
                            else RouteType.MULTI_HOP))

        anomaly_type = scenario.get("anomaly")
        target_stage = scenario["target_stage"]
        final_status = scenario["final_status"]
        recovered = scenario.get("recovered", False)
        operator_intervention = scenario.get("operator_intervention", False)
        escalation_flag = operator_intervention or (anomaly_type and rng.random() < 0.3)

        delay_node = None
        delay_country = None
        if anomaly_type in (AnomalyType.GATEWAY_TIMEOUT, AnomalyType.MISSING_INTERMEDIARY, AnomalyType.SETTLEMENT_DELAY):
            if corridor.get("intermediaries"):
                delay_country = rng.choice(corridor["intermediaries"])
                matching = [b for b in BANKS if b["country"] == delay_country]
                delay_node = matching[0]["name"] if matching else f"{delay_country} Gateway"
            else:
                delay_country = dst
                delay_node = f"{dst} Settlement Node"
        elif anomaly_type == AnomalyType.SANCTIONS_FALSE_POSITIVE:
            delay_country = dst

        created_at = now - timedelta(hours=rng.randint(1, 168), minutes=rng.randint(0, 59))
        expected_hours = rng.randint(2, 48)
        expected_completion = created_at + timedelta(hours=expected_hours)
        actual_completion = None
        if final_status == PaymentStatus.COMPLETED:
            actual_completion = created_at + timedelta(hours=rng.randint(1, expected_hours + 6))

        priority = _pick_priority(rng, amount)
        payment_type = _pick_payment_type(rng, corridor.get("rail", "SWIFT"))
        is_high_value = amount > 1000000

        # Generate stage timings
        timing_data = _generate_stage_timings(target_stage, anomaly_type, rng, is_high_value, recovered)
        total_seconds = timing_data["total"]
        sla_breach, sla_breach_seconds = _compute_sla_breach(priority, total_seconds, anomaly_type is not None, rng)

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
            send_amount=amount,
            receive_amount=round(amount * fx_rate, 2),
            corridor=f"{src}-{dst}",
            priority=priority,
            payment_type=payment_type,
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
            system_rail=corridor.get("rail", "SWIFT"),
            route_type=route_type,
            route_path=route_path,
            delay_node=delay_node,
            delay_country=delay_country,
            sanctions_hit=anomaly_type == AnomalyType.SANCTIONS_FALSE_POSITIVE,
            validation_error=anomaly_type == AnomalyType.VALIDATION_ERROR,
            gateway_timeout=anomaly_type == AnomalyType.GATEWAY_TIMEOUT,
            reconciliation_break=anomaly_type == AnomalyType.RECONCILIATION_MISMATCH,
            # Phase 2 observability
            stage_timings=timing_data["timings"],
            expected_stage_durations=timing_data["expected"],
            retry_counts=timing_data["retries"],
            queue_wait_seconds=timing_data["queues"],
            bottleneck_stage=timing_data["bottleneck_stage"],
            bottleneck_node=delay_node if timing_data["bottleneck_stage"] else None,
            total_processing_seconds=total_seconds,
            sla_breach=sla_breach,
            sla_breach_seconds=sla_breach_seconds,
            escalation_flag=bool(escalation_flag),
            operator_intervention=operator_intervention,
            recovered=recovered,
        )

        store.add_payment(payment)

        # Generate events
        anomaly_stage = ANOMALY_CONFIGS[anomaly_type]["stage"] if anomaly_type else None
        events = _generate_events_for_payment(
            payment, target_stage, anomaly_stage, anomaly_type, rng, created_at, recovered
        )
        for ev in events:
            store.add_event(ev)

        # Generate logs
        logs = _generate_logs_for_payment(payment, events, rng)
        for log in logs:
            store.add_log(log)

        # Generate anomaly record if applicable
        if anomaly_type:
            cfg = ANOMALY_CONFIGS[anomaly_type]
            # Assign action_status based on payment outcome
            if final_status == PaymentStatus.COMPLETED:
                action_st = ActionStatus.RESOLVED
                anomaly_status = AnomalyStatus.RESOLVED
            elif operator_intervention:
                action_st = ActionStatus.IN_PROGRESS
                anomaly_status = AnomalyStatus.INVESTIGATING
            elif recovered:
                action_st = ActionStatus.MITIGATED
                anomaly_status = AnomalyStatus.RESOLVED
            else:
                action_st = rng.choice([ActionStatus.OPEN, ActionStatus.TRIAGED, ActionStatus.IN_PROGRESS])
                anomaly_status = rng.choice([AnomalyStatus.OPEN, AnomalyStatus.INVESTIGATING])

            detected_offset = timedelta(minutes=rng.randint(2, 30))
            anomaly = Anomaly(
                payment_id=payment.id,
                type=anomaly_type,
                title=cfg["title"],
                description=cfg["desc"],
                severity=cfg["severity"],
                detected_at=created_at + detected_offset,
                stage=cfg["stage"],
                scope=cfg["scope"],
                country=delay_country or dst,
                intermediary_bank=delay_node,
                status=anomaly_status,
                recommended_action=cfg.get("recommended_action"),
                confidence=round(rng.uniform(0.65, 0.98), 2),
                evidence_summary=cfg.get("evidence"),
                # Phase 2
                anomaly_code=cfg.get("code"),
                root_symptom=cfg.get("root_symptom"),
                probable_cause=cfg.get("probable_cause"),
                first_detected_at=created_at + detected_offset,
                last_updated_at=created_at + detected_offset + timedelta(minutes=rng.randint(5, 120)),
                impacted_node=delay_node,
                corridor=f"{src}-{dst}",
                operational_impact_score=round(cfg.get("impact_score", 5.0) * rng.uniform(0.8, 1.2), 1),
                action_status=action_st,
                resolution_eta_minutes=cfg.get("eta_minutes"),
                recurrence_count=rng.choices([0, 1, 2, 3], weights=[55, 25, 15, 5])[0],
                client_impact_level=cfg.get("client_impact"),
            )
            store.add_anomaly(anomaly)

    # Post-process: update node stats based on seeded payments
    _update_node_stats()

    print(f"[SEED] Generated {store.payment_count()} payments, {store.anomaly_count()} anomalies, {len(store.list_nodes())} nodes")


def _update_node_stats() -> None:
    """Compute node health stats from seeded payment data."""
    payments = store.list_payments()
    nodes = {n.bank_name: n for n in store.list_nodes()}

    for payment in payments:
        for country_code in payment.route_path:
            matching = [n for n in nodes.values() if n.country == country_code]
            for node in matching:
                node.route_usage_count += 1
                if payment.delay_country == country_code:
                    node.delay_count += 1
                if payment.anomaly_flag and payment.delay_country == country_code:
                    node.anomaly_count += 1
                if payment.anomaly_flag and not node.last_incident_at:
                    node.last_incident_at = payment.updated_at

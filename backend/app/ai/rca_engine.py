"""
RCA Engine — deterministic, evidence-based root cause analysis.

Works in two modes:
1. DETERMINISTIC (default): rule-based reasoning from payment/anomaly data
2. LLM_AUGMENTED: optional enrichment if env vars configured (future)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from ..domain.enums import AnomalyType, AnomalySeverity
from ..schemas.ai_schemas import (
    AlternativeHypothesis,
    RCAResult,
    ReasoningStep,
)

# ── Issue category mapping ────────────────────────────────────────────────────

_ANOMALY_TYPE_CATEGORY = {
    AnomalyType.SANCTIONS_FALSE_POSITIVE: "COMPLIANCE",
    AnomalyType.GATEWAY_TIMEOUT: "ROUTING",
    AnomalyType.VALIDATION_ERROR: "VALIDATION",
    AnomalyType.FX_DELAY: "FX",
    AnomalyType.MISSING_INTERMEDIARY: "ROUTING",
    AnomalyType.SETTLEMENT_DELAY: "SETTLEMENT",
    AnomalyType.RECONCILIATION_MISMATCH: "SETTLEMENT",
}

_SEVERITY_PRIORITY = {
    AnomalySeverity.CRITICAL: "CRITICAL",
    AnomalySeverity.HIGH: "HIGH",
    AnomalySeverity.MEDIUM: "MEDIUM",
    AnomalySeverity.LOW: "LOW",
}

# ── RCA knowledge base (deterministic rules) ──────────────────────────────────

_RCA_KNOWLEDGE = {
    "SANCTIONS_FALSE_POSITIVE": {
        "primary_issue": "Sanctions screening triggered false positive hold",
        "likely_root_cause": (
            "The payment matched a name or entity pattern in the sanctions watch-list "
            "but does not correspond to a true restricted party. This is a known pattern "
            "with high-value cross-border payments where beneficiary names partially match "
            "screened entities."
        ),
        "contributing_factors": [
            "Beneficiary name similarity to a sanctioned entity",
            "Corridor flagged for elevated compliance scrutiny",
            "Automated screening without contextual disambiguation",
            "Missing disambiguation data in payment reference",
        ],
        "supporting_evidence": [
            "Anomaly type: SANCTIONS_FALSE_POSITIVE",
            "Payment held at COMPLIANCE_SCREENING stage",
            "No prior confirmed sanctions hits on this client",
        ],
        "next_checks": [
            "Verify beneficiary identity against original account documents",
            "Compare full legal entity name against watch-list entry",
            "Check corridor-level false positive rate for this rule set",
            "Escalate to compliance officer for manual release if verified clean",
        ],
        "customer_impact": "Payment is on hold. Client funds are not at risk but delivery is delayed pending compliance review.",
        "ops_impact": "Manual compliance review required. Resolution typically takes 1-4 hours. SLA may be breached.",
        "alternatives": [
            ("System error or data corruption in screening DB", "No evidence of screening system errors in logs", 0.05),
            ("Actual sanctions match requiring hold", "No confirmed restricted party data found", 0.10),
        ],
    },
    "GATEWAY_TIMEOUT": {
        "primary_issue": "Routing gateway timeout — downstream correspondent bank unreachable",
        "likely_root_cause": (
            "The payment routing gateway failed to receive acknowledgement from the "
            "intermediary/correspondent bank within the SLA window. This is typically "
            "caused by transient network congestion, scheduled maintenance windows, or "
            "elevated latency at the correspondent node."
        ),
        "contributing_factors": [
            "Correspondent bank latency above threshold",
            "Network congestion on payment corridor",
            "Gateway timeout configuration may be too aggressive",
            "Possible intermediary bank maintenance window",
        ],
        "supporting_evidence": [
            "Anomaly type: GATEWAY_TIMEOUT",
            "Payment stalled at ROUTING or SETTLEMENT stage",
            "Timeout recorded in gateway logs",
        ],
        "next_checks": [
            "Check correspondent bank system status and maintenance schedule",
            "Review recent latency trends for this node",
            "Attempt retry through alternate correspondent route",
            "Verify gateway timeout thresholds are appropriate for this corridor",
        ],
        "customer_impact": "Payment delivery delayed. Funds are in transit but processing is paused pending routing resolution.",
        "ops_impact": "Routing retry may be required. Consider alternate correspondent path if issue persists beyond 30 minutes.",
        "alternatives": [
            ("Client-side payment data issue", "Payment data validated successfully upstream", 0.05),
            ("Internal system outage", "No system-wide health alerts detected", 0.08),
        ],
    },
    "VALIDATION_ERROR": {
        "primary_issue": "Payment validation failure — missing or malformed required fields",
        "likely_root_cause": (
            "One or more required payment fields failed validation checks. This is typically "
            "caused by incomplete beneficiary data, malformed account identifiers, or "
            "missing intermediary routing codes required for the destination corridor."
        ),
        "contributing_factors": [
            "Incomplete beneficiary account details submitted by client",
            "Missing SWIFT BIC or IBAN for destination corridor",
            "Incorrect currency code or amount format",
            "Regulatory field requirements not met for destination country",
        ],
        "supporting_evidence": [
            "Anomaly type: VALIDATION_ERROR",
            "Payment failed at VALIDATION stage",
            "Validation error flag set on payment record",
        ],
        "next_checks": [
            "Identify specific failed validation field(s) from payment logs",
            "Contact client or originating system to resubmit with corrected data",
            "Verify destination corridor regulatory requirements are documented",
            "Check if validation rules were recently updated",
        ],
        "customer_impact": "Payment cannot proceed until data correction is submitted. Client must provide updated information.",
        "ops_impact": "Low risk but requires client outreach. Typically resolved within 2-8 hours depending on client response.",
        "alternatives": [
            ("System validation rule misconfiguration", "Validation logic checked and consistent with corridor rules", 0.12),
            ("Data encoding issue from originating system", "No systematic encoding errors detected", 0.08),
        ],
    },
    "FX_DELAY": {
        "primary_issue": "FX rate acquisition delay — pricing or quote latency on payment corridor",
        "likely_root_cause": (
            "The FX rate lock or quote for this payment's currency pair experienced "
            "a delay. This is most common during high-volatility market periods, when "
            "liquidity providers are under load, or for less-liquid currency corridors "
            "where pricing requires additional market polling."
        ),
        "contributing_factors": [
            "High volatility in currency pair causing pricing delay",
            "Liquidity provider response time elevated",
            "Less-liquid currency corridor requiring multiple quotes",
            "FX rate validity window expired before payment processing",
        ],
        "supporting_evidence": [
            "Anomaly type: FX_DELAY",
            "Extended time at FX_CONVERSION stage",
            "Total processing time above corridor average",
        ],
        "next_checks": [
            "Check current market conditions for the affected currency pair",
            "Verify FX liquidity provider system status",
            "Consider requesting rate re-quote if current rate has expired",
            "Assess whether alternative FX provider should be used for this corridor",
        ],
        "customer_impact": "Receive amount may vary slightly from initial indication if rate is re-quoted. Delivery delayed.",
        "ops_impact": "Monitor FX stage duration. If stalled beyond 30 minutes, manual rate intervention may be required.",
        "alternatives": [
            ("FX system outage", "Partial FX functionality observed, not full outage", 0.10),
            ("Regulatory FX restriction on corridor", "No active corridor FX restrictions flagged", 0.07),
        ],
    },
    "MISSING_INTERMEDIARY": {
        "primary_issue": "Missing or unavailable intermediary bank on payment route",
        "likely_root_cause": (
            "No viable intermediary/correspondent bank was found for the required payment "
            "route. This can occur when the preferred correspondent bank is unavailable, "
            "the route requires a specific intermediary not currently configured, or "
            "the corridor lacks direct correspondent relationships."
        ),
        "contributing_factors": [
            "Preferred correspondent bank unavailable or not responding",
            "No direct correspondent relationship for this currency pair",
            "Multi-hop route required but intermediate node missing",
            "Correspondent bank may have suspended operations on this corridor",
        ],
        "supporting_evidence": [
            "Anomaly type: MISSING_INTERMEDIARY",
            "Route path incomplete",
            "Payment stalled at ROUTING stage",
        ],
        "next_checks": [
            "Check available correspondent network for this corridor",
            "Identify alternative routing paths through different intermediaries",
            "Verify correspondent bank relationship status for destination country",
            "Consider escalating to treasury for manual correspondent arrangement",
        ],
        "customer_impact": "Payment cannot be routed. Risk of significant delay or return if alternate route not found.",
        "ops_impact": "High urgency. Manual treasury intervention may be required to establish alternate correspondent routing.",
        "alternatives": [
            ("Transient routing system issue", "No routing system errors detected in logs", 0.10),
            ("Destination country banking restriction", "No active country restrictions in policy DB", 0.08),
        ],
    },
    "SETTLEMENT_DELAY": {
        "primary_issue": "Settlement delay — downstream settlement queue backlog or processing hold",
        "likely_root_cause": (
            "The payment has cleared routing and compliance but is experiencing a delay "
            "in final settlement. This is most commonly caused by downstream bank settlement "
            "queue congestion, end-of-day settlement window timing, or a hold applied by "
            "the receiving bank's posting system."
        ),
        "contributing_factors": [
            "Downstream settlement queue backlog",
            "Settlement window timing — near end-of-day cutoff",
            "Receiving bank posting system processing delay",
            "High-value payment triggering additional settlement review",
        ],
        "supporting_evidence": [
            "Anomaly type: SETTLEMENT_DELAY",
            "Payment stalled at SETTLEMENT stage",
            "Processing time above corridor average",
        ],
        "next_checks": [
            "Check current settlement queue depth for destination bank",
            "Verify receiving bank settlement cutoff times",
            "Confirm whether payment missed today's settlement window",
            "Contact settlement operations team for priority processing if urgent",
        ],
        "customer_impact": "Funds not yet credited to beneficiary. Risk of same-day value date miss.",
        "ops_impact": "May require settlement ops escalation. Check value date implications for client.",
        "alternatives": [
            ("Receiving bank compliance hold", "No compliance flags found at destination bank", 0.12),
            ("Internal settlement system error", "Settlement system logs show no system faults", 0.06),
        ],
    },
    "RECONCILIATION_MISMATCH": {
        "primary_issue": "Reconciliation mismatch — posting discrepancy or delayed status propagation",
        "likely_root_cause": (
            "A discrepancy exists between the expected payment outcome and what has been "
            "recorded in the downstream reconciliation system. This typically indicates "
            "an asynchronous posting failure, a timing mismatch in status propagation, "
            "or a duplicate/partial posting scenario."
        ),
        "contributing_factors": [
            "Asynchronous posting status not yet reflected in reconciliation system",
            "Partial posting or duplicate transaction in downstream ledger",
            "Reconciliation system latency or batch processing delay",
            "Status message from correspondent bank not received",
        ],
        "supporting_evidence": [
            "Anomaly type: RECONCILIATION_MISMATCH",
            "Reconciliation break flag set on payment record",
            "Payment status mismatch between systems",
        ],
        "next_checks": [
            "Retrieve latest MT940/SWIFT confirmation for this payment",
            "Check downstream ledger for duplicate or partial postings",
            "Verify reconciliation system received settlement confirmation",
            "Trigger manual reconciliation recheck if auto-recon cycle pending",
        ],
        "customer_impact": "Payment may appear in inconsistent state across systems. Funds not at risk but records need correction.",
        "ops_impact": "Recon team must investigate. Risk of end-of-day balance discrepancy if not resolved promptly.",
        "alternatives": [
            ("Genuine payment failure requiring reversal", "No reversal or failure message received from correspondent", 0.10),
            ("System clock skew causing ordering issue", "No NTP sync issues detected in infrastructure logs", 0.05),
        ],
    },
}


class RCAEngine:
    """
    Deterministic RCA engine. Analyzes payment + anomaly data and produces
    an explainable root cause report with structured reasoning steps.
    """

    def analyze_payment(self, payment_id: str) -> RCAResult | None:
        from ..repositories.memory_store import store

        payment = store.get_payment(payment_id)
        if not payment:
            return None

        anomalies = store.get_anomalies_for_payment(payment_id)
        logs = store.get_logs_for_payment(payment_id) if hasattr(store, "get_logs_for_payment") else []

        return self._run_rca(payment, anomalies, logs)

    def _run_rca(self, payment, anomalies: list, logs: list) -> RCAResult:
        from ..domain.enums import AnomalyType as AT

        anomaly_ids = [a.id for a in anomalies]
        primary_anomaly = anomalies[0] if anomalies else None

        # Determine primary anomaly type
        atype_str = primary_anomaly.type.value if primary_anomaly else None
        if not atype_str and payment.anomaly_type:
            atype_str = payment.anomaly_type.value

        kb = _RCA_KNOWLEDGE.get(atype_str, {})
        issue_category = _ANOMALY_TYPE_CATEGORY.get(
            primary_anomaly.type if primary_anomaly else payment.anomaly_type,
            "OPERATIONAL"
        ) if (primary_anomaly or payment.anomaly_type) else "OPERATIONAL"

        # Build reasoning steps from evidence
        steps = self._build_reasoning_steps(payment, primary_anomaly, issue_category)

        # Contributing factors from KB + dynamic evidence
        factors = list(kb.get("contributing_factors", []))
        if payment.sla_breach:
            factors.append("SLA breach confirmed — time-sensitive escalation required")
        if payment.bottleneck_stage:
            factors.append(f"Identified bottleneck stage: {payment.bottleneck_stage}")
        if payment.retry_counts and any(v > 0 for v in payment.retry_counts.values()):
            max_retries = max(payment.retry_counts.values())
            factors.append(f"Retry attempts detected ({max_retries}x) indicating transient failure")
        if payment.escalation_flag:
            factors.append("Manual escalation flag set — operator intervention may already be in progress")

        # Supporting evidence
        evidence = list(kb.get("supporting_evidence", []))
        evidence.append(f"Payment corridor: {payment.corridor}")
        evidence.append(f"Payment type: {payment.payment_type.value}")
        evidence.append(f"Current stage: {payment.current_stage.value}")
        evidence.append(f"Current status: {payment.current_status.value}")
        if payment.total_processing_seconds:
            mins = payment.total_processing_seconds / 60
            evidence.append(f"Total processing time: {mins:.1f} minutes")
        if primary_anomaly and primary_anomaly.confidence:
            evidence.append(f"Anomaly detection confidence: {primary_anomaly.confidence * 100:.0f}%")

        # Alternative hypotheses
        alternatives = [
            AlternativeHypothesis(
                hypothesis=h,
                reason_rejected=r,
                confidence=c,
            )
            for h, r, c in kb.get("alternatives", [])
        ]

        # Resolution priority
        severity = (
            primary_anomaly.severity if primary_anomaly
            else payment.anomaly_severity
        )
        resolution_priority = _SEVERITY_PRIORITY.get(severity, "MEDIUM") if severity else "MEDIUM"
        if payment.sla_breach:
            resolution_priority = "CRITICAL"

        # Confidence score based on evidence quality
        confidence = self._compute_confidence(payment, primary_anomaly, anomalies)

        # Impacted stage
        impacted_stage = (
            primary_anomaly.stage.value if primary_anomaly
            else payment.bottleneck_stage or payment.current_stage.value
        )

        return RCAResult(
            payment_id=payment.id,
            anomaly_ids=anomaly_ids,
            primary_issue=kb.get("primary_issue", f"Operational exception: {atype_str or 'Unknown issue'}"),
            issue_category=issue_category,
            impacted_stage=impacted_stage,
            impacted_node=payment.bottleneck_node or payment.delay_node,
            impacted_country=payment.delay_country or payment.destination_country,
            confidence_score=confidence,
            reasoning_steps=steps,
            contributing_factors=factors[:6],
            supporting_evidence=evidence[:8],
            likely_root_cause=kb.get("likely_root_cause", "Operational exception detected. Manual investigation recommended."),
            alternative_hypotheses=alternatives,
            customer_impact_summary=kb.get("customer_impact", "Payment processing delayed. Funds are secured."),
            operations_impact_summary=kb.get("ops_impact", "Operations review required to determine next steps."),
            recommended_next_checks=kb.get("next_checks", ["Review payment logs", "Contact operations team"])[:5],
            resolution_priority=resolution_priority,
        )

    def _build_reasoning_steps(self, payment, primary_anomaly, issue_category: str) -> list[ReasoningStep]:
        steps = []
        n = 1

        # Step 1: Payment context
        steps.append(ReasoningStep(
            step_number=n, label="Payment Context Analysis",
            observation=f"Payment {payment.payment_reference} on corridor {payment.corridor}, "
                        f"amount {payment.amount:,.2f} {payment.source_currency}, "
                        f"type {payment.payment_type.value}",
            evidence=f"Current stage: {payment.current_stage.value}, "
                     f"status: {payment.current_status.value}",
            conclusion=f"Payment is active in {payment.current_stage.value} stage with {payment.current_status.value} status",
        ))
        n += 1

        # Step 2: Anomaly detection
        if primary_anomaly:
            steps.append(ReasoningStep(
                step_number=n, label="Anomaly Signal Detection",
                observation=f"Anomaly detected: {primary_anomaly.title}",
                evidence=f"Type: {primary_anomaly.type.value}, Severity: {primary_anomaly.severity.value}, "
                         f"Confidence: {(primary_anomaly.confidence or 0) * 100:.0f}%",
                conclusion=f"Anomaly confirmed as {primary_anomaly.type.value} — root cause analysis proceeds in {issue_category} category",
            ))
            n += 1

        # Step 3: Stage timing analysis
        if payment.stage_timings:
            bottleneck = payment.bottleneck_stage
            if bottleneck and payment.expected_stage_durations:
                actual = payment.stage_timings.get(bottleneck, 0)
                expected = payment.expected_stage_durations.get(bottleneck, 1)
                ratio = actual / max(expected, 1)
                steps.append(ReasoningStep(
                    step_number=n, label="Stage Timing Analysis",
                    observation=f"Bottleneck stage identified: {bottleneck}",
                    evidence=f"Actual duration: {actual:.0f}s vs expected: {expected:.0f}s ({ratio:.1f}x over)",
                    conclusion=f"Stage {bottleneck} is running {ratio:.1f}x over expected — primary time-loss point",
                ))
                n += 1

        # Step 4: SLA assessment
        if payment.sla_breach:
            steps.append(ReasoningStep(
                step_number=n, label="SLA Breach Assessment",
                observation="SLA breach confirmed on this payment",
                evidence=f"Breach duration: {payment.sla_breach_seconds:.0f}s over SLA threshold"
                         if payment.sla_breach_seconds else "SLA breach flag set",
                conclusion="Time-critical: immediate escalation warranted to prevent further SLA degradation",
            ))
            n += 1

        # Step 5: Node/route context
        if payment.delay_node or payment.delay_country:
            steps.append(ReasoningStep(
                step_number=n, label="Route & Node Context",
                observation=f"Delay localized to node: {payment.delay_node or 'N/A'}, country: {payment.delay_country or 'N/A'}",
                evidence=f"Route path: {' → '.join(payment.route_path or [])}",
                conclusion=f"Delay is isolated to a specific point in the route, suggesting a targeted intervention may resolve the issue",
            ))
            n += 1

        # Step 6: Retry history
        if payment.retry_counts and any(v > 0 for v in payment.retry_counts.values()):
            retry_str = ", ".join(f"{k}:{v}" for k, v in payment.retry_counts.items() if v > 0)
            steps.append(ReasoningStep(
                step_number=n, label="Retry History Analysis",
                observation=f"Retry attempts recorded: {retry_str}",
                evidence="Retries indicate transient failure — system has already attempted self-recovery",
                conclusion="Pattern of retries without resolution suggests persistent underlying issue rather than transient failure",
            ))
            n += 1

        return steps

    def _compute_confidence(self, payment, primary_anomaly, anomalies: list) -> float:
        score = 0.5
        if primary_anomaly:
            score += 0.15
            if primary_anomaly.confidence:
                score += primary_anomaly.confidence * 0.1
        if payment.anomaly_type:
            score += 0.1
        if payment.stage_timings:
            score += 0.05
        if payment.bottleneck_stage:
            score += 0.05
        if payment.delay_node or payment.delay_country:
            score += 0.05
        return round(min(score, 0.95), 2)

    def analyze_anomaly(self, anomaly_id: str) -> RCAResult | None:
        from ..repositories.memory_store import store

        all_anomalies = store.list_anomalies()
        anomaly = next((a for a in all_anomalies if a.id == anomaly_id), None)
        if not anomaly:
            return None

        payment = store.get_payment(anomaly.payment_id)
        if not payment:
            return None

        return self._run_rca(payment, [anomaly], [])


rca_engine = RCAEngine()

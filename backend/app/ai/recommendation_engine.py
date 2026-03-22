"""
Recommendation Engine — deterministic, evidence-grounded action suggestions.
Turns RCA + payment context into ranked next-step recommendations.
"""
from __future__ import annotations

import uuid
from typing import Any

from ..schemas.ai_schemas import RCAResult, Recommendation

# ── Recommendation templates keyed by issue_category + anomaly_type ──────────

_REC_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "COMPLIANCE": [
        {
            "type": "INVESTIGATE_COMPLIANCE_HIT",
            "priority": "HIGH",
            "title": "Review sanctions screening result with compliance officer",
            "description": "Assign this payment to a compliance officer for manual review of the screening hit. Verify that the beneficiary is not a restricted party.",
            "rationale": "Sanctions false positives require human verification before release. Automated release is not permissible.",
            "urgency": "WITHIN_1H",
            "owner": "COMPLIANCE",
            "impact": "Unblocks payment delivery if verified clean. Prevents regulatory breach if genuine hit.",
            "effort": "LOW (30-60 min manual review)",
            "preconditions": ["Compliance officer available", "Original KYC documents accessible"],
            "risk_notes": "Do not release without formal compliance sign-off. Regulatory risk if genuine hit is cleared.",
            "category": "COMPLIANCE_REVIEW",
        },
        {
            "type": "OVERRIDE_FALSE_POSITIVE",
            "priority": "MEDIUM",
            "title": "Override false positive with operator approval if identity verified",
            "description": "If compliance review confirms the beneficiary is not a restricted party, apply a false positive override to allow payment processing to continue.",
            "rationale": "Verified false positives should be overridden to restore SLA compliance and reduce unnecessary hold time.",
            "urgency": "WITHIN_1H",
            "owner": "COMPLIANCE",
            "impact": "Immediately unblocks payment. Restores SLA if applied within time window.",
            "effort": "LOW (requires compliance sign-off)",
            "preconditions": ["Compliance officer sign-off received", "Identity verified against original documents"],
            "risk_notes": "Only apply after formal compliance clearance. Document override decision for audit trail.",
            "category": "COMPLIANCE_OVERRIDE",
        },
    ],
    "ROUTING": [
        {
            "type": "RETRY_ROUTING_GATEWAY",
            "priority": "HIGH",
            "title": "Retry routing through primary correspondent gateway",
            "description": "Initiate a routing retry through the same correspondent gateway. Transient network issues typically resolve within one retry cycle.",
            "rationale": "Gateway timeouts are often transient. A single retry has high success probability before escalating.",
            "urgency": "IMMEDIATE",
            "owner": "TECH",
            "impact": "Payment resumes processing if transient. Minimal disruption to client.",
            "effort": "LOW (automated retry possible)",
            "preconditions": ["Correspondent gateway status checked", "Retry not already attempted 3+ times"],
            "risk_notes": "Limit retries to 3 before switching route to avoid duplicate payment risk.",
            "category": "RETRY",
        },
        {
            "type": "REROUTE_PAYMENT",
            "priority": "MEDIUM",
            "title": "Reroute through alternate correspondent bank",
            "description": "Switch to an alternate correspondent bank or routing path for this corridor. Check available correspondent relationships for the destination country.",
            "rationale": "If primary correspondent is persistently unavailable, an alternate route will restore payment flow.",
            "urgency": "WITHIN_1H",
            "owner": "OPS",
            "impact": "Unblocks payment via alternate path. May incur slightly different FX or fee terms.",
            "effort": "MEDIUM (requires route reconfiguration or manual treasury instruction)",
            "preconditions": ["Alternate correspondent available for this corridor", "Treasury approval for route switch"],
            "risk_notes": "Verify alternate route fees and FX terms before rerouting. Notify client if significant cost difference.",
            "category": "REROUTE",
        },
        {
            "type": "CONTACT_INTERMEDIARY",
            "priority": "MEDIUM",
            "title": "Contact correspondent / intermediary bank directly",
            "description": "Reach out to the intermediary bank operations team to diagnose the routing failure and request manual intervention.",
            "rationale": "Direct contact with correspondent bank can accelerate resolution and surface information not available in system logs.",
            "urgency": "WITHIN_1H",
            "owner": "OPS",
            "impact": "Provides root cause clarity and may accelerate correspondent-side resolution.",
            "effort": "MEDIUM (ops team outreach)",
            "preconditions": ["Correspondent bank contact details available", "Payment reference confirmed"],
            "risk_notes": "Log all correspondent communications. Document outcome for audit.",
            "category": "ESCALATION",
        },
    ],
    "VALIDATION": [
        {
            "type": "REQUEST_DATA_CORRECTION",
            "priority": "HIGH",
            "title": "Request corrected payment data from originating client",
            "description": "Contact the originating client or system to obtain corrected or completed payment field data. Identify the specific field(s) that failed validation.",
            "rationale": "Validation errors cannot be resolved without source data correction. Client must resubmit corrected instruction.",
            "urgency": "WITHIN_1H",
            "owner": "OPS",
            "impact": "Unblocks payment once corrected data is received. No further action needed from ops side.",
            "effort": "LOW-MEDIUM (depends on client response time)",
            "preconditions": ["Failed field(s) identified in payment logs", "Client contact details available"],
            "risk_notes": "Do not attempt to infer or fill missing data fields. All corrections must come from the client.",
            "category": "DATA_FIX",
        },
        {
            "type": "HOLD_AND_MONITOR",
            "priority": "LOW",
            "title": "Place payment on hold and await data correction",
            "description": "Mark payment as on hold for data correction. Set follow-up reminder for client response within 4 hours.",
            "rationale": "Payment cannot proceed without data correction. A structured hold prevents it from blocking queue processing.",
            "urgency": "WITHIN_24H",
            "owner": "OPS",
            "impact": "Keeps payment in controlled state while awaiting client. Reduces ops queue noise.",
            "effort": "LOW",
            "preconditions": ["Client notified of data requirement"],
            "risk_notes": "Ensure SLA implications of hold are communicated to client.",
            "category": "HOLD",
        },
    ],
    "FX": [
        {
            "type": "REQUEST_FX_REQUOTE",
            "priority": "HIGH",
            "title": "Request FX rate re-quote from liquidity provider",
            "description": "Trigger a fresh FX rate quote for this payment's currency pair. Current rate may have expired or failed to lock.",
            "rationale": "FX delays are often resolved by a fresh rate request. Current quote window may have expired.",
            "urgency": "IMMEDIATE",
            "owner": "TREASURY",
            "impact": "Unblocks FX stage. Client receive amount may vary slightly from initial indication.",
            "effort": "LOW (automated rate request possible)",
            "preconditions": ["FX system operational", "Client rate tolerance acceptable"],
            "risk_notes": "New rate may differ from original. Verify client acceptance if rate tolerance exceeded.",
            "category": "FX_ACTION",
        },
        {
            "type": "SWITCH_FX_PROVIDER",
            "priority": "MEDIUM",
            "title": "Switch to alternative FX liquidity provider for this corridor",
            "description": "If primary FX provider is experiencing elevated latency, route the FX quote request to the secondary liquidity provider.",
            "rationale": "Alternative liquidity provider may have better availability for this currency pair.",
            "urgency": "WITHIN_1H",
            "owner": "TREASURY",
            "impact": "Restores FX processing. May have slightly different spread.",
            "effort": "MEDIUM (treasury configuration change)",
            "preconditions": ["Alternative FX provider configured for this currency pair", "Treasury approval"],
            "risk_notes": "Simulated recommendation. Verify with treasury before executing.",
            "category": "FX_ACTION",
        },
    ],
    "SETTLEMENT": [
        {
            "type": "ESCALATE_TO_SETTLEMENT_OPS",
            "priority": "HIGH",
            "title": "Escalate to settlement operations team for priority processing",
            "description": "Alert settlement operations team to prioritize this payment for manual processing. Provide payment reference and urgency level.",
            "rationale": "Settlement delays can result in value date misses with client financial impact. Escalation allows priority queue insertion.",
            "urgency": "WITHIN_1H",
            "owner": "OPS",
            "impact": "May recover same-day settlement. Prevents value date miss for client.",
            "effort": "LOW (escalation notification)",
            "preconditions": ["Settlement ops team reachable", "Payment reference confirmed"],
            "risk_notes": "Confirm receiving bank settlement cut-off time before escalating.",
            "category": "ESCALATION",
        },
        {
            "type": "FORCE_RECONCILIATION_RECHECK",
            "priority": "MEDIUM",
            "title": "Trigger manual reconciliation recheck for this payment",
            "description": "Initiate a reconciliation recheck cycle for this payment. Compare system ledger state against correspondent confirmation messages.",
            "rationale": "Reconciliation mismatches may auto-resolve once confirmation messages arrive. A manual trigger accelerates this.",
            "urgency": "WITHIN_1H",
            "owner": "OPS",
            "impact": "Resolves posting discrepancy and restores accurate payment state.",
            "effort": "LOW-MEDIUM",
            "preconditions": ["Settlement confirmation message received or retrievable", "Recon system accessible"],
            "risk_notes": "Do not mark payment as complete without verified correspondent confirmation.",
            "category": "RECONCILIATION",
        },
        {
            "type": "MONITOR_ONLY",
            "priority": "LOW",
            "title": "Monitor settlement progress — no immediate action required",
            "description": "Payment is in the settlement queue. No intervention required at this time. Monitor for status update in next 30 minutes.",
            "rationale": "Some settlement delays resolve automatically once batch processing completes.",
            "urgency": "WITHIN_24H",
            "owner": "OPS",
            "impact": "Low risk of wasted effort. Appropriate when settlement is simply delayed, not blocked.",
            "effort": "MINIMAL",
            "preconditions": ["No critical SLA breach imminent"],
            "risk_notes": "Re-escalate if no progress observed within monitoring window.",
            "category": "MONITOR",
        },
    ],
    "OPERATIONAL": [
        {
            "type": "HOLD_FOR_MANUAL_REVIEW",
            "priority": "MEDIUM",
            "title": "Place payment on hold for manual operations review",
            "description": "Assign payment to operations team for manual investigation. Review payment logs, events, and stage timings.",
            "rationale": "Unclassified operational issues require human investigation to determine appropriate next step.",
            "urgency": "WITHIN_1H",
            "owner": "OPS",
            "impact": "Prevents payment from advancing into an uncertain state. Allows structured investigation.",
            "effort": "MEDIUM",
            "preconditions": [],
            "risk_notes": "Document investigation findings and resolution path.",
            "category": "MANUAL_REVIEW",
        },
        {
            "type": "PRIORITIZE_HIGH_VALUE",
            "priority": "HIGH",
            "title": "Prioritize for high-value payment manual handling",
            "description": "Given the high transaction value and current operational exception, assign to senior operations staff for expedited resolution.",
            "rationale": "High-value payments have elevated financial and reputational risk. Prioritized handling reduces exposure.",
            "urgency": "WITHIN_1H",
            "owner": "OPS",
            "impact": "Reduces financial exposure and client impact for high-value exceptions.",
            "effort": "MEDIUM",
            "preconditions": ["Senior ops staff available"],
            "risk_notes": "Ensure audit trail for all actions taken on high-value payment.",
            "category": "ESCALATION",
        },
    ],
}


class RecommendationEngine:
    """
    Deterministic recommendation engine. Takes RCA result + payment context
    and produces ranked, grounded action recommendations.
    """

    def generate(self, payment_id: str, rca: RCAResult | None = None) -> list[Recommendation]:
        from ..repositories.memory_store import store

        payment = store.get_payment(payment_id)
        if not payment:
            return []

        if rca is None:
            from .rca_engine import rca_engine
            rca = rca_engine.analyze_payment(payment_id)

        if rca is None:
            return []

        templates = _REC_TEMPLATES.get(rca.issue_category, _REC_TEMPLATES["OPERATIONAL"])

        # Always add high-value escalation if amount > 500k
        if payment.amount > 500_000 and not any(t["type"] == "PRIORITIZE_HIGH_VALUE" for t in templates):
            templates = templates + _REC_TEMPLATES["OPERATIONAL"]

        recs = []
        for i, tmpl in enumerate(templates):
            evidence = [
                f"Payment: {payment.payment_reference}",
                f"Corridor: {payment.corridor}",
                f"Stage: {rca.impacted_stage}",
                f"Issue: {rca.primary_issue}",
            ]
            if rca.impacted_node:
                evidence.append(f"Impacted node: {rca.impacted_node}")
            if rca.impacted_country:
                evidence.append(f"Impacted country: {rca.impacted_country}")

            confidence = rca.confidence_score - (i * 0.06)
            if payment.sla_breach and i == 0:
                confidence = min(confidence + 0.1, 0.95)

            recs.append(Recommendation(
                recommendation_id=str(uuid.uuid4()),
                payment_id=payment_id,
                type=tmpl["type"],
                priority=tmpl["priority"] if not (payment.sla_breach and i == 0) else "CRITICAL",
                title=tmpl["title"],
                description=tmpl["description"],
                rationale=tmpl["rationale"],
                confidence_score=max(round(confidence, 2), 0.30),
                execution_urgency=tmpl["urgency"] if not payment.sla_breach else "IMMEDIATE",
                recommended_owner=tmpl["owner"],
                estimated_impact=tmpl["impact"],
                estimated_effort=tmpl["effort"],
                preconditions=tmpl["preconditions"],
                risk_notes=tmpl["risk_notes"],
                related_evidence=evidence,
                action_category=tmpl["category"],
            ))

        return recs[:4]  # Top 4 recommendations

    def generate_for_anomaly(self, anomaly_id: str) -> list[Recommendation]:
        from ..repositories.memory_store import store

        all_anomalies = store.list_anomalies()
        anomaly = next((a for a in all_anomalies if a.id == anomaly_id), None)
        if not anomaly:
            return []

        return self.generate(anomaly.payment_id)


recommendation_engine = RecommendationEngine()

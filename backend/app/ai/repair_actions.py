"""
Repair Action Framework — structured playbooks for payment exception recovery.
Actions are informational/advisory, never destructive automation.
"""
from __future__ import annotations

import uuid
from ..schemas.ai_schemas import RepairAction

# ── Action type constants ──────────────────────────────────────────────────────
RETRY_STAGE = "RETRY_STAGE"
REROUTE_PAYMENT = "REROUTE_PAYMENT"
ESCALATE_TO_OPERATIONS = "ESCALATE_TO_OPERATIONS"
REQUEST_DATA_FIX = "REQUEST_DATA_FIX"
MARK_FALSE_POSITIVE = "MARK_FALSE_POSITIVE"
HOLD_AND_MONITOR = "HOLD_AND_MONITOR"
FORCE_RECONCILIATION_RECHECK = "FORCE_RECONCILIATION_RECHECK"
SWITCH_CORRIDOR = "SWITCH_CORRIDOR"
PRIORITIZE_FOR_MANUAL_HANDLING = "PRIORITIZE_FOR_MANUAL_HANDLING"

# ── Repair playbook catalog ────────────────────────────────────────────────────

_PLAYBOOKS: dict[str, dict] = {
    RETRY_STAGE: {
        "title": "Retry Payment Stage",
        "description": "Re-submit the payment to the current or failed stage. Clears transient failure state and re-queues for processing.",
        "estimated_success_probability": 0.72,
        "risk_level": "LOW",
        "requires_human_approval": False,
        "execution_notes": "Safe to retry up to 3 times for transient failures. Implement deduplication check before retry to prevent duplicate payments.",
        "blocking_conditions": [
            "Payment already retried 3+ times without success",
            "Underlying system outage still active",
            "Compliance hold is blocking — retry will not bypass compliance",
        ],
    },
    REROUTE_PAYMENT: {
        "title": "Reroute via Alternate Correspondent",
        "description": "Change the payment routing path to use an alternate correspondent bank or network rail for the destination corridor.",
        "estimated_success_probability": 0.68,
        "risk_level": "MEDIUM",
        "requires_human_approval": True,
        "execution_notes": "Verify alternate route fees and FX terms before executing. Treasury sign-off required for routes with materially different terms. SIMULATED in demo mode.",
        "blocking_conditions": [
            "No alternate correspondent available for this corridor",
            "Alternate route has higher risk score",
            "Client instruction restricts specific routing",
        ],
    },
    ESCALATE_TO_OPERATIONS: {
        "title": "Escalate to Operations Team",
        "description": "Flag payment for immediate human review by the operations team. Sets high-priority queue marker.",
        "estimated_success_probability": 0.90,
        "risk_level": "LOW",
        "requires_human_approval": False,
        "execution_notes": "Use for situations requiring human judgment, SLA-breached payments, or when automated resolution has been exhausted.",
        "blocking_conditions": [
            "Operations team unavailable (outside business hours — use on-call)",
        ],
    },
    REQUEST_DATA_FIX: {
        "title": "Request Client Data Correction",
        "description": "Notify originating client or system that a data correction is required before payment can proceed. Provides specific field requirements.",
        "estimated_success_probability": 0.85,
        "risk_level": "LOW",
        "requires_human_approval": False,
        "execution_notes": "Identify specific failed validation fields before initiating request. Set SLA expectation with client for correction turnaround.",
        "blocking_conditions": [
            "Client contact details unavailable",
            "Data correction already requested and outstanding",
        ],
    },
    MARK_FALSE_POSITIVE: {
        "title": "Mark Sanctions Hit as False Positive",
        "description": "After compliance officer review and sign-off, mark the sanctions screening hit as a false positive to release the payment for processing.",
        "estimated_success_probability": 0.95,
        "risk_level": "HIGH",
        "requires_human_approval": True,
        "execution_notes": "REQUIRES formal compliance officer sign-off. Document decision with rationale. Create audit entry. Only apply when identity is conclusively verified.",
        "blocking_conditions": [
            "Compliance officer sign-off not obtained",
            "Identity verification not completed",
            "Genuine restricted party concern remains unresolved",
        ],
    },
    HOLD_AND_MONITOR: {
        "title": "Place on Hold and Monitor",
        "description": "Move payment to a controlled hold state and set a monitoring reminder. Appropriate when situation may self-resolve or is awaiting external input.",
        "estimated_success_probability": 0.60,
        "risk_level": "LOW",
        "requires_human_approval": False,
        "execution_notes": "Set a clear monitoring trigger (time or event) to re-evaluate. Document hold reason and expected resolution path.",
        "blocking_conditions": [
            "Payment is already in a final or failed state",
        ],
    },
    FORCE_RECONCILIATION_RECHECK: {
        "title": "Force Reconciliation Recheck",
        "description": "Trigger an immediate reconciliation recheck cycle for this payment. Compares system state against correspondent bank confirmations.",
        "estimated_success_probability": 0.78,
        "risk_level": "MEDIUM",
        "requires_human_approval": False,
        "execution_notes": "Retrieve latest SWIFT MT940 or equivalent confirmation before triggering. Only mark as complete when confirmation is verified.",
        "blocking_conditions": [
            "Correspondent confirmation not yet received",
            "Reconciliation system in maintenance mode",
        ],
    },
    SWITCH_CORRIDOR: {
        "title": "Switch to Alternative Corridor (Simulated)",
        "description": "Recommend switching the preferred corridor for this payment type/client to reduce future exposure to this failure pattern. Advisory only.",
        "estimated_success_probability": 0.55,
        "risk_level": "MEDIUM",
        "requires_human_approval": True,
        "execution_notes": "SIMULATED/ADVISORY: This is a forward-looking recommendation, not an immediate fix. Route the current payment via available alternatives first.",
        "blocking_conditions": [
            "No alternative corridor available",
            "Client corridor preference explicitly specified in standing instruction",
        ],
    },
    PRIORITIZE_FOR_MANUAL_HANDLING: {
        "title": "Prioritize for Senior Operations Handling",
        "description": "Flag payment for immediate attention by senior operations staff. Appropriate for high-value or high-severity exception payments.",
        "estimated_success_probability": 0.88,
        "risk_level": "LOW",
        "requires_human_approval": False,
        "execution_notes": "Assign to senior ops queue with full context packet. Include RCA summary, anomaly details, and timeline in case notes.",
        "blocking_conditions": [
            "No senior ops staff available — escalate to on-call manager",
        ],
    },
}

# ── Issue-category to repair action mapping ───────────────────────────────────

_CATEGORY_ACTIONS: dict[str, list[str]] = {
    "COMPLIANCE": [MARK_FALSE_POSITIVE, ESCALATE_TO_OPERATIONS, HOLD_AND_MONITOR],
    "ROUTING": [RETRY_STAGE, REROUTE_PAYMENT, ESCALATE_TO_OPERATIONS, SWITCH_CORRIDOR],
    "VALIDATION": [REQUEST_DATA_FIX, HOLD_AND_MONITOR, ESCALATE_TO_OPERATIONS],
    "FX": [RETRY_STAGE, ESCALATE_TO_OPERATIONS, HOLD_AND_MONITOR],
    "SETTLEMENT": [ESCALATE_TO_OPERATIONS, FORCE_RECONCILIATION_RECHECK, HOLD_AND_MONITOR],
    "OPERATIONAL": [ESCALATE_TO_OPERATIONS, PRIORITIZE_FOR_MANUAL_HANDLING, HOLD_AND_MONITOR],
}


class RepairRecommender:
    """Generates repair playbook actions for a payment based on its RCA category."""

    def get_repair_actions(self, payment_id: str, issue_category: str = "OPERATIONAL") -> list[RepairAction]:
        from ..repositories.memory_store import store

        payment = store.get_payment(payment_id)
        action_types = _CATEGORY_ACTIONS.get(issue_category, _CATEGORY_ACTIONS["OPERATIONAL"])

        # Add high-value handling if amount > 500k
        if payment and payment.amount > 500_000 and PRIORITIZE_FOR_MANUAL_HANDLING not in action_types:
            action_types = [PRIORITIZE_FOR_MANUAL_HANDLING] + list(action_types)

        actions = []
        for atype in action_types:
            pb = _PLAYBOOKS.get(atype)
            if not pb:
                continue

            # Determine applicable stage from payment context
            target_stage = None
            target_node = None
            if payment:
                target_stage = payment.bottleneck_stage or payment.current_stage.value
                target_node = payment.bottleneck_node or payment.delay_node

            actions.append(RepairAction(
                action_id=str(uuid.uuid4()),
                action_type=atype,
                title=pb["title"],
                description=pb["description"],
                target_stage=target_stage,
                target_node=target_node,
                applicability_rules=[
                    f"Payment category: {issue_category}",
                    f"Current stage: {payment.current_stage.value if payment else 'unknown'}",
                ],
                estimated_success_probability=pb["estimated_success_probability"],
                risk_level=pb["risk_level"],
                requires_human_approval=pb["requires_human_approval"],
                blocking_conditions=pb["blocking_conditions"],
                execution_notes=pb["execution_notes"],
            ))

        return actions


repair_recommender = RepairRecommender()

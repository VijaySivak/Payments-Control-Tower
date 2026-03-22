"""
Guardrail / Policy Engine — ensures AI recommendations stay safe and plausible.
All recommendations pass through policy rules before being returned to callers.
"""
from __future__ import annotations

from ..schemas.ai_schemas import PolicyDecision, Recommendation, RepairAction


# ── Policy rules ──────────────────────────────────────────────────────────────

def _rule_sanctions_no_auto_reroute(
    payment, recommendation: Recommendation
) -> PolicyDecision | None:
    """Sanctions-related issues must not auto-recommend rerouting without review."""
    if (
        payment
        and payment.sanctions_hit
        and recommendation.type in ("REROUTE_PAYMENT", "RETRY_STAGE", "SWITCH_CORRIDOR")
    ):
        return PolicyDecision(
            rule_name="SANCTIONS_NO_AUTO_REROUTE",
            triggered=True,
            action_taken="RECOMMENDATION_DOWNGRADED",
            reason="Sanctions hit present. Rerouting without compliance review is not permitted. Recommendation downgraded to hold pending compliance clearance.",
        )
    return None


def _rule_high_value_requires_approval(
    payment, action: RepairAction
) -> PolicyDecision | None:
    """High-value payments (>500k) must have human approval for aggressive actions."""
    aggressive_types = {"REROUTE_PAYMENT", "MARK_FALSE_POSITIVE", "SWITCH_CORRIDOR"}
    if (
        payment
        and payment.amount > 500_000
        and action.action_type in aggressive_types
        and not action.requires_human_approval
    ):
        return PolicyDecision(
            rule_name="HIGH_VALUE_REQUIRES_APPROVAL",
            triggered=True,
            action_taken="REQUIRES_HUMAN_APPROVAL_FLAG_SET",
            reason=f"Payment amount {payment.amount:,.0f} exceeds high-value threshold. "
                   f"Action '{action.action_type}' requires explicit human approval.",
        )
    return None


def _rule_recon_no_auto_complete(
    payment, recommendation: Recommendation
) -> PolicyDecision | None:
    """Reconciliation issues must not be marked complete without verification."""
    if (
        payment
        and payment.reconciliation_break
        and recommendation.type in ("MARK_FALSE_POSITIVE",)
    ):
        return PolicyDecision(
            rule_name="RECON_NO_AUTO_COMPLETE",
            triggered=True,
            action_taken="RECOMMENDATION_BLOCKED",
            reason="Reconciliation break active. Payment cannot be marked complete without verified correspondent confirmation.",
        )
    return None


def _rule_validation_prefer_data_fix(
    payment, recommendation: Recommendation
) -> PolicyDecision | None:
    """Validation issues should prefer data correction over retry."""
    if (
        payment
        and payment.validation_error
        and recommendation.type == "RETRY_STAGE"
        and recommendation.priority in ("HIGH", "CRITICAL")
    ):
        return PolicyDecision(
            rule_name="VALIDATION_PREFER_DATA_FIX",
            triggered=True,
            action_taken="RECOMMENDATION_PRIORITY_ADJUSTED",
            reason="Validation error present. Retrying without data correction has low success probability. Data fix recommended first.",
        )
    return None


def _rule_repeated_failures_escalate(
    payment, recommendation: Recommendation
) -> PolicyDecision | None:
    """Repeated failures should escalate rather than allow infinite retry."""
    if (
        payment
        and payment.retry_counts
        and any(v >= 3 for v in payment.retry_counts.values())
        and recommendation.type == "RETRY_STAGE"
    ):
        return PolicyDecision(
            rule_name="REPEATED_FAILURES_ESCALATE",
            triggered=True,
            action_taken="RECOMMENDATION_BLOCKED",
            reason="Payment has already been retried 3+ times. Further retry not recommended. Escalate to operations for manual investigation.",
        )
    return None


def _rule_severe_anomaly_high_priority(
    payment, recommendation: Recommendation
) -> PolicyDecision | None:
    """Critical/High anomalies must be tagged high-priority."""
    from ..domain.enums import AnomalySeverity
    if (
        payment
        and payment.anomaly_severity in (AnomalySeverity.CRITICAL, AnomalySeverity.HIGH)
        and recommendation.priority not in ("CRITICAL", "HIGH")
    ):
        return PolicyDecision(
            rule_name="SEVERE_ANOMALY_HIGH_PRIORITY",
            triggered=True,
            action_taken="RECOMMENDATION_PRIORITY_ELEVATED",
            reason=f"Payment has {payment.anomaly_severity.value} severity anomaly. Recommendation priority elevated.",
        )
    return None


def _rule_corridor_switch_simulated(
    payment, action: RepairAction
) -> PolicyDecision | None:
    """Corridor switch actions are always advisory/simulated."""
    if action.action_type == "SWITCH_CORRIDOR":
        return PolicyDecision(
            rule_name="CORRIDOR_SWITCH_SIMULATED",
            triggered=True,
            action_taken="MARKED_AS_ADVISORY",
            reason="Corridor switching is a simulated/advisory recommendation. No automated route change will be executed. Requires treasury approval and manual execution.",
        )
    return None


# ── Guardrail Engine ──────────────────────────────────────────────────────────

class GuardrailEngine:
    """
    Runs AI recommendations and repair actions through policy rules.
    Returns policy decisions and modified outputs.
    """

    def check_recommendations(
        self, payment, recommendations: list[Recommendation]
    ) -> tuple[list[Recommendation], list[PolicyDecision]]:
        decisions: list[PolicyDecision] = []
        filtered: list[Recommendation] = []

        for rec in recommendations:
            blocked = False
            for rule_fn in [
                _rule_sanctions_no_auto_reroute,
                _rule_recon_no_auto_complete,
                _rule_validation_prefer_data_fix,
                _rule_repeated_failures_escalate,
                _rule_severe_anomaly_high_priority,
            ]:
                decision = rule_fn(payment, rec)
                if decision:
                    decisions.append(decision)
                    if decision.action_taken == "RECOMMENDATION_BLOCKED":
                        blocked = True
                        break

            if not blocked:
                filtered.append(rec)

        return filtered, decisions

    def check_repair_actions(
        self, payment, actions: list[RepairAction]
    ) -> tuple[list[RepairAction], list[PolicyDecision]]:
        decisions: list[PolicyDecision] = []
        modified: list[RepairAction] = []

        for action in actions:
            action_copy = action.model_copy(deep=True)
            for rule_fn in [
                _rule_high_value_requires_approval,
                _rule_corridor_switch_simulated,
            ]:
                decision = rule_fn(payment, action_copy)
                if decision:
                    decisions.append(decision)
                    if decision.action_taken == "REQUIRES_HUMAN_APPROVAL_FLAG_SET":
                        action_copy.requires_human_approval = True
                    if decision.action_taken == "MARKED_AS_ADVISORY":
                        action_copy.execution_notes = "[ADVISORY/SIMULATED] " + action_copy.execution_notes
            modified.append(action_copy)

        return modified, decisions

    def build_guardrail_notes(self, decisions: list[PolicyDecision]) -> list[str]:
        notes = []
        for d in decisions:
            if d.triggered:
                notes.append(f"[{d.rule_name}] {d.reason}")
        return notes


guardrail_engine = GuardrailEngine()

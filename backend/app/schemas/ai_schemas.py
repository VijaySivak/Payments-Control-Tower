"""Phase 3 AI Layer Pydantic schemas."""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel


# ── RCA ────────────────────────────────────────────────────────────────────────

class ReasoningStep(BaseModel):
    step_number: int
    label: str
    observation: str
    evidence: str
    conclusion: str


class AlternativeHypothesis(BaseModel):
    hypothesis: str
    reason_rejected: str
    confidence: float


class RCAResult(BaseModel):
    payment_id: str
    anomaly_ids: list[str]
    primary_issue: str
    issue_category: str          # e.g. COMPLIANCE, ROUTING, SETTLEMENT, FX, VALIDATION, TIMEOUT
    impacted_stage: str
    impacted_node: Optional[str]
    impacted_country: Optional[str]
    confidence_score: float      # 0-1
    reasoning_steps: list[ReasoningStep]
    contributing_factors: list[str]
    supporting_evidence: list[str]
    likely_root_cause: str
    alternative_hypotheses: list[AlternativeHypothesis]
    customer_impact_summary: str
    operations_impact_summary: str
    recommended_next_checks: list[str]
    resolution_priority: str     # CRITICAL / HIGH / MEDIUM / LOW


# ── Recommendations ───────────────────────────────────────────────────────────

class Recommendation(BaseModel):
    recommendation_id: str
    payment_id: str
    type: str
    priority: str
    title: str
    description: str
    rationale: str
    confidence_score: float
    execution_urgency: str       # IMMEDIATE / WITHIN_1H / WITHIN_24H / MONITOR
    recommended_owner: str       # OPS / COMPLIANCE / TECH / TREASURY / AUTOMATIC
    estimated_impact: str
    estimated_effort: str
    preconditions: list[str]
    risk_notes: str
    related_evidence: list[str]
    action_category: str


# ── Repair Actions ─────────────────────────────────────────────────────────────

class RepairAction(BaseModel):
    action_id: str
    action_type: str             # RETRY_STAGE, REROUTE_PAYMENT, ESCALATE_TO_OPERATIONS, etc.
    title: str
    description: str
    target_stage: Optional[str]
    target_node: Optional[str]
    applicability_rules: list[str]
    estimated_success_probability: float
    risk_level: str              # LOW / MEDIUM / HIGH
    requires_human_approval: bool
    blocking_conditions: list[str]
    execution_notes: str


# ── Agent Trace ────────────────────────────────────────────────────────────────

class AgentOutput(BaseModel):
    agent_name: str
    started_at: str
    completed_at: str
    duration_ms: int
    status: str                  # SUCCESS / SKIPPED / ERROR
    output_summary: str
    key_findings: list[str]
    data_consumed: list[str]


class PolicyDecision(BaseModel):
    rule_name: str
    triggered: bool
    action_taken: str
    reason: str


class AgentTrace(BaseModel):
    execution_id: str
    payment_id: str
    started_at: str
    completed_at: str
    total_duration_ms: int
    agents_run: list[AgentOutput]
    final_summary: str
    reasoning_trace: list[str]
    policy_decisions: list[PolicyDecision]
    guardrail_notes: list[str]
    mode: str                    # DETERMINISTIC / LLM_AUGMENTED


# ── AI Summary ────────────────────────────────────────────────────────────────

class AISummary(BaseModel):
    payment_id: str
    operator_summary: str
    what_went_wrong: str
    why_it_happened: str
    what_to_do: str
    risk_level: str
    urgency: str
    key_facts: list[str]
    confidence: float


# ── Combined AI Package ────────────────────────────────────────────────────────

class AIPackage(BaseModel):
    payment_id: str
    rca: RCAResult
    recommendations: list[Recommendation]
    repair_actions: list[RepairAction]
    ai_summary: AISummary
    agent_trace: AgentTrace


# ── Control Tower AI ──────────────────────────────────────────────────────────

class PriorityQueueItem(BaseModel):
    payment_id: str
    payment_reference: str
    priority_score: float
    urgency: str
    reason: str
    recommended_action: str
    anomaly_type: Optional[str]
    anomaly_severity: Optional[str]
    sla_breach: bool
    corridor: str
    amount: float


class CorridorRiskInsight(BaseModel):
    corridor: str
    risk_score: float
    risk_level: str
    primary_issue: str
    anomaly_count: int
    sla_breach_count: int
    avg_delay_seconds: float
    recommended_action: str
    trend: str                   # WORSENING / STABLE / IMPROVING


class NodeRiskWatchlistItem(BaseModel):
    node_id: str
    bank_name: str
    country: str
    node_type: str
    health_status: str
    risk_score: float
    anomaly_count: int
    delay_count: int
    avg_latency_ms: float
    risk_reason: str
    recommended_action: str


class SystemAnomalyInsight(BaseModel):
    insight_id: str
    category: str
    title: str
    description: str
    affected_payments: int
    affected_corridors: list[str]
    severity: str
    confidence: float
    recommended_action: str


class OperatorSummary(BaseModel):
    generated_at: str
    headline: str
    system_status: str
    key_alerts: list[str]
    top_issues: list[dict[str, Any]]
    recommended_actions: list[str]
    positive_signals: list[str]
    watch_items: list[str]
    ai_confidence: float

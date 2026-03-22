"""In-memory repository layer. Designed to be swapped with SQLite/Postgres later."""

from __future__ import annotations

from typing import Any

from ..domain.models import Anomaly, IntermediaryNode, Payment, PaymentEvent, PaymentLog


class InMemoryStore:
    """Thread-safe in-memory data store for all domain entities."""

    def __init__(self) -> None:
        self._payments: dict[str, Payment] = {}
        self._events: dict[str, list[PaymentEvent]] = {}
        self._logs: dict[str, list[PaymentLog]] = {}
        self._anomalies: dict[str, Anomaly] = {}
        self._nodes: dict[str, IntermediaryNode] = {}

    # ── Payments ────────────────────────────────────────────────

    def add_payment(self, payment: Payment) -> None:
        self._payments[payment.id] = payment

    def get_payment(self, payment_id: str) -> Payment | None:
        return self._payments.get(payment_id)

    def list_payments(self) -> list[Payment]:
        return list(self._payments.values())

    def update_payment(self, payment: Payment) -> None:
        self._payments[payment.id] = payment

    def filter_payments(
        self,
        *,
        status: str | None = None,
        stage: str | None = None,
        source_country: str | None = None,
        destination_country: str | None = None,
        anomaly_type: str | None = None,
        severity: str | None = None,
        search: str | None = None,
        corridor: str | None = None,
        priority: str | None = None,
        payment_type: str | None = None,
        sla_breach: bool | None = None,
        anomaly_only: bool | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Payment], int]:
        results = list(self._payments.values())

        if status:
            results = [p for p in results if p.current_status.value == status.upper()]
        if stage:
            results = [p for p in results if p.current_stage.value == stage.upper()]
        if source_country:
            results = [p for p in results if p.source_country == source_country.upper()]
        if destination_country:
            results = [p for p in results if p.destination_country == destination_country.upper()]
        if anomaly_type:
            results = [p for p in results if p.anomaly_type and p.anomaly_type.value == anomaly_type.upper()]
        if severity:
            results = [p for p in results if p.anomaly_severity and p.anomaly_severity.value == severity.upper()]
        if corridor:
            results = [p for p in results if p.corridor.upper() == corridor.upper()]
        if priority:
            results = [p for p in results if p.priority.value == priority.upper()]
        if payment_type:
            results = [p for p in results if p.payment_type.value == payment_type.upper()]
        if sla_breach is not None:
            results = [p for p in results if p.sla_breach == sla_breach]
        if anomaly_only:
            results = [p for p in results if p.anomaly_flag]
        if search:
            q = search.lower()
            results = [
                p for p in results
                if q in p.payment_reference.lower()
                or q in p.source_client_name.lower()
                or q in p.beneficiary_name.lower()
                or q in p.corridor.lower()
                or q in p.id.lower()
                or q in p.source_country.lower()
                or q in p.destination_country.lower()
            ]

        # Sorting
        reverse = sort_dir.lower() == "desc"
        if sort_by == "amount":
            results.sort(key=lambda p: p.amount, reverse=reverse)
        elif sort_by == "updated_at":
            results.sort(key=lambda p: p.updated_at, reverse=reverse)
        elif sort_by == "processing_time":
            results.sort(key=lambda p: (p.total_processing_seconds or 0), reverse=reverse)
        else:
            results.sort(key=lambda p: p.created_at, reverse=reverse)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end], total

    # ── Events ──────────────────────────────────────────────────

    def add_event(self, event: PaymentEvent) -> None:
        if event.payment_id not in self._events:
            self._events[event.payment_id] = []
        self._events[event.payment_id].append(event)

    def get_events(self, payment_id: str) -> list[PaymentEvent]:
        events = self._events.get(payment_id, [])
        return sorted(events, key=lambda e: e.timestamp)

    # ── Logs ────────────────────────────────────────────────────

    def add_log(self, log: PaymentLog) -> None:
        if log.payment_id not in self._logs:
            self._logs[log.payment_id] = []
        self._logs[log.payment_id].append(log)

    def get_logs(self, payment_id: str) -> list[PaymentLog]:
        logs = self._logs.get(payment_id, [])
        return sorted(logs, key=lambda l: l.timestamp)

    # ── Anomalies ───────────────────────────────────────────────

    def add_anomaly(self, anomaly: Anomaly) -> None:
        self._anomalies[anomaly.id] = anomaly

    def get_anomaly(self, anomaly_id: str) -> Anomaly | None:
        return self._anomalies.get(anomaly_id)

    def get_anomalies_for_payment(self, payment_id: str) -> list[Anomaly]:
        return [a for a in self._anomalies.values() if a.payment_id == payment_id]

    def list_anomalies(self) -> list[Anomaly]:
        return list(self._anomalies.values())

    def filter_anomalies(
        self,
        *,
        severity: str | None = None,
        anomaly_type: str | None = None,
        country: str | None = None,
        stage: str | None = None,
        status: str | None = None,
        corridor: str | None = None,
        node: str | None = None,
        action_status: str | None = None,
    ) -> list[Anomaly]:
        results = list(self._anomalies.values())
        if severity:
            results = [a for a in results if a.severity.value == severity.upper()]
        if anomaly_type:
            results = [a for a in results if a.type.value == anomaly_type.upper()]
        if country:
            results = [a for a in results if a.country and a.country.upper() == country.upper()]
        if stage:
            results = [a for a in results if a.stage.value == stage.upper()]
        if status:
            results = [a for a in results if a.status.value == status.upper()]
        if corridor:
            results = [a for a in results if a.corridor and a.corridor.upper() == corridor.upper()]
        if node:
            q = node.lower()
            results = [a for a in results if (
                (a.intermediary_bank and q in a.intermediary_bank.lower()) or
                (a.impacted_node and q in a.impacted_node.lower())
            )]
        if action_status:
            results = [a for a in results if a.action_status.value == action_status.upper()]
        results.sort(key=lambda a: a.detected_at, reverse=True)
        return results

    # ── Intermediary Nodes ──────────────────────────────────────

    def add_node(self, node: IntermediaryNode) -> None:
        self._nodes[node.id] = node

    def get_node(self, node_id: str) -> IntermediaryNode | None:
        return self._nodes.get(node_id)

    def list_nodes(self) -> list[IntermediaryNode]:
        return list(self._nodes.values())

    # ── Stats helpers ───────────────────────────────────────────

    def payment_count(self) -> int:
        return len(self._payments)

    def anomaly_count(self) -> int:
        return len(self._anomalies)


# Singleton store instance
store = InMemoryStore()

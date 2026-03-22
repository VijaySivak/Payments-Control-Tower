"""Journey and timeline service for payment visualization."""

from __future__ import annotations

from ..domain.enums import PaymentStage, STAGE_ORDER
from ..domain.models import Payment
from ..repositories.memory_store import store
from ..schemas.payment import (
    JourneyNodeSchema,
    MapFlowSchema,
    PaymentEventSchema,
    PaymentJourneySchema,
    PaymentLogSchema,
)
from ..utils.geo import get_coords, get_country_name


class JourneyService:

    def get_journey(self, payment_id: str) -> PaymentJourneySchema | None:
        payment = store.get_payment(payment_id)
        if not payment:
            return None

        events = store.get_events(payment_id)
        event_schemas = [
            PaymentEventSchema(
                id=e.id, payment_id=e.payment_id, timestamp=e.timestamp,
                stage=e.stage, event_type=e.event_type, status=e.status,
                message=e.message, details=e.details, actor=e.actor, severity=e.severity,
            )
            for e in events
        ]

        nodes = self._build_journey_nodes(payment)

        return PaymentJourneySchema(
            payment_id=payment.id,
            route_path=payment.route_path,
            route_type=payment.route_type,
            origin_country=payment.source_country,
            destination_country=payment.destination_country,
            current_stage=payment.current_stage,
            current_status=payment.current_status,
            delay_node=payment.delay_node,
            delay_country=payment.delay_country,
            nodes=nodes,
            events=event_schemas,
        )

    def _build_journey_nodes(self, payment: Payment) -> list[JourneyNodeSchema]:
        nodes = []
        current_stage_idx = STAGE_ORDER.index(payment.current_stage) if payment.current_stage in STAGE_ORDER else -1

        for i, country in enumerate(payment.route_path):
            coords = get_coords(country)
            is_origin = i == 0
            is_destination = i == len(payment.route_path) - 1
            is_intermediate = not is_origin and not is_destination
            is_delayed = payment.delay_country == country

            # Determine node stage based on position
            if is_origin:
                stage = PaymentStage.INITIATED
            elif is_destination:
                stage = payment.current_stage
            else:
                # Intermediate nodes map to routing/compliance/fx stages
                stage_map_idx = min(i + 1, len(STAGE_ORDER) - 1)
                stage = STAGE_ORDER[stage_map_idx] if stage_map_idx < len(STAGE_ORDER) else PaymentStage.ROUTING

            # Determine node status
            if payment.current_stage == PaymentStage.COMPLETED:
                node_status = "completed"
            elif is_delayed:
                node_status = "delayed"
            elif is_origin:
                node_status = "completed"
            elif i <= current_stage_idx:
                node_status = "completed"
            else:
                node_status = "pending"

            nodes.append(JourneyNodeSchema(
                country=country,
                node_name=get_country_name(country),
                node_type="origin" if is_origin else ("destination" if is_destination else "intermediary"),
                is_origin=is_origin,
                is_destination=is_destination,
                is_intermediate=is_intermediate,
                is_delayed=is_delayed,
                stage=stage,
                status=node_status,
                lat=coords["lat"],
                lng=coords["lng"],
            ))

        return nodes

    def get_timeline(self, payment_id: str) -> list[PaymentEventSchema]:
        events = store.get_events(payment_id)
        return [
            PaymentEventSchema(
                id=e.id, payment_id=e.payment_id, timestamp=e.timestamp,
                stage=e.stage, event_type=e.event_type, status=e.status,
                message=e.message, details=e.details, actor=e.actor, severity=e.severity,
            )
            for e in events
        ]

    def get_logs(self, payment_id: str) -> list[PaymentLogSchema]:
        logs = store.get_logs(payment_id)
        return [
            PaymentLogSchema(
                id=l.id, payment_id=l.payment_id, timestamp=l.timestamp,
                log_level=l.log_level, component=l.component,
                message=l.message, context=l.context,
            )
            for l in logs
        ]

    def get_map_flows(self) -> list[MapFlowSchema]:
        payments = store.list_payments()

        # Group by corridor + status combination for aggregated flows
        flow_map: dict[str, dict] = {}
        for p in payments:
            key = f"{p.source_country}-{p.destination_country}-{p.current_status.value}"
            if key not in flow_map:
                origin_coords = get_coords(p.source_country)
                dest_coords = get_coords(p.destination_country)

                route_coordinates = []
                for country in p.route_path:
                    c = get_coords(country)
                    route_coordinates.append({"lat": c["lat"], "lng": c["lng"], "country": country})

                flow_map[key] = {
                    "origin_country": p.source_country,
                    "destination_country": p.destination_country,
                    "route_countries": p.route_path,
                    "origin_lat": origin_coords["lat"],
                    "origin_lng": origin_coords["lng"],
                    "destination_lat": dest_coords["lat"],
                    "destination_lng": dest_coords["lng"],
                    "route_coordinates": route_coordinates,
                    "status": p.current_status,
                    "delayed_node": p.delay_node,
                    "delayed_country": p.delay_country,
                    "anomaly_severity": p.anomaly_severity,
                    "payment_count": 0,
                    "payment_ids": [],
                    "corridor": p.corridor,
                }
            flow_map[key]["payment_count"] += 1
            flow_map[key]["payment_ids"].append(p.id)
            # Keep worst severity
            if p.anomaly_severity and (
                flow_map[key]["anomaly_severity"] is None
                or _severity_rank(p.anomaly_severity) > _severity_rank(flow_map[key]["anomaly_severity"])
            ):
                flow_map[key]["anomaly_severity"] = p.anomaly_severity
                flow_map[key]["delayed_node"] = p.delay_node
                flow_map[key]["delayed_country"] = p.delay_country

        flows = []
        for key, data in flow_map.items():
            flows.append(MapFlowSchema(
                id=key,
                **data,
            ))

        return flows


def _severity_rank(s) -> int:
    from ..domain.enums import AnomalySeverity
    rank = {AnomalySeverity.LOW: 1, AnomalySeverity.MEDIUM: 2, AnomalySeverity.HIGH: 3, AnomalySeverity.CRITICAL: 4}
    return rank.get(s, 0)


journey_service = JourneyService()

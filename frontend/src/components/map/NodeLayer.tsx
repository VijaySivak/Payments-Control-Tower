"use client";
import type { MapFlow } from "@/lib/types";
import { project } from "./MapProjection";

interface NodeLayerProps {
  flows: MapFlow[];
  selectedFlowId: string | null;
  onNodeClick: (flow: MapFlow) => void;
  onNodeHover: (country: string | null) => void;
}

interface NodeInfo {
  country: string;
  x: number;
  y: number;
  isDelayed: boolean;
  hasAnomaly: boolean;
  anomalySeverity?: string;
  paymentIds: string[];
  role: "origin" | "destination" | "intermediary";
  flows: MapFlow[];
}

function SEVERITY_COLOR(s?: string) {
  if (s === "CRITICAL") return "#EF4444";
  if (s === "HIGH") return "#F97316";
  if (s === "MEDIUM") return "#F59E0B";
  return "#3B82F6";
}

export function NodeLayer({ flows, selectedFlowId, onNodeClick, onNodeHover }: NodeLayerProps) {
  const nodeMap = new Map<string, NodeInfo>();

  const upsert = (
    country: string,
    lat: number,
    lng: number,
    role: NodeInfo["role"],
    flow: MapFlow,
  ) => {
    if (!country || lat === 0 && lng === 0) return;
    const [x, y] = project(lat, lng);
    if (!nodeMap.has(country)) {
      nodeMap.set(country, { country, x, y, isDelayed: false, hasAnomaly: false, paymentIds: [], role, flows: [] });
    }
    const n = nodeMap.get(country)!;
    n.paymentIds.push(...flow.payment_ids);
    n.flows.push(flow);
    if (flow.delayed_country === country) n.isDelayed = true;
    if (flow.anomaly_severity) {
      n.hasAnomaly = true;
      if (!n.anomalySeverity) n.anomalySeverity = flow.anomaly_severity;
    }
    if (role === "origin" || role === "destination") n.role = role;
  };

  flows.forEach((flow) => {
    upsert(flow.origin_country, flow.origin_lat, flow.origin_lng, "origin", flow);
    upsert(flow.destination_country, flow.destination_lat, flow.destination_lng, "destination", flow);
    flow.route_coordinates.slice(1, -1).forEach((rc) => {
      if (rc.country) upsert(rc.country, rc.lat, rc.lng, "intermediary", flow);
    });
  });

  const nodes = Array.from(nodeMap.values());

  return (
    <g>
      <defs>
        <filter id="node-glow" x="-80%" y="-80%" width="260%" height="260%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {nodes.map((node) => {
        const isEndpoint = node.role === "origin" || node.role === "destination";
        const r = isEndpoint ? 5.5 : 3.5;
        const color = node.isDelayed
          ? "#F59E0B"
          : node.hasAnomaly
          ? SEVERITY_COLOR(node.anomalySeverity)
          : node.role === "origin"
          ? "#3B82F6"
          : node.role === "destination"
          ? "#10B981"
          : "#6366F1";

        const uniqueIds = Array.from(new Set(node.paymentIds));
        const representativeFlow = node.flows[0];

        return (
          <g
            key={node.country}
            style={{ cursor: "pointer" }}
            onClick={(e) => { e.stopPropagation(); if (representativeFlow) onNodeClick(representativeFlow); }}
            onMouseEnter={() => onNodeHover(node.country)}
            onMouseLeave={() => onNodeHover(null)}
          >
            {/* Outer pulse ring — delayed nodes */}
            {node.isDelayed && (
              <>
                <circle cx={node.x} cy={node.y} r={r + 7} fill="none" stroke="#F59E0B" strokeWidth={1} opacity={0.3} />
                <circle cx={node.x} cy={node.y} r={r + 12} fill="none" stroke="#F59E0B" strokeWidth={0.5} opacity={0.15} />
              </>
            )}

            {/* Anomaly pulse ring */}
            {node.hasAnomaly && !node.isDelayed && (
              <circle cx={node.x} cy={node.y} r={r + 6} fill="none" stroke={color} strokeWidth={1} opacity={0.35} />
            )}

            {/* Glow background for active nodes */}
            {isEndpoint && (
              <circle cx={node.x} cy={node.y} r={r + 2} fill={color} opacity={0.15} filter="url(#node-glow)" />
            )}

            {/* Main node circle */}
            <circle
              cx={node.x}
              cy={node.y}
              r={r}
              fill={color}
              stroke="rgba(6,11,24,0.85)"
              strokeWidth={1.5}
              opacity={0.95}
            />

            {/* Inner bright dot */}
            <circle cx={node.x} cy={node.y} r={r * 0.4} fill="white" opacity={0.5} />

            {/* Payment count badge for busy nodes */}
            {uniqueIds.length > 2 && isEndpoint && (
              <>
                <circle cx={node.x + r + 3} cy={node.y - r - 3} r={6} fill="#1e293b" stroke={color} strokeWidth={0.8} />
                <text
                  x={node.x + r + 3}
                  y={node.y - r - 3}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={5.5}
                  fill={color}
                  fontWeight="bold"
                >
                  {uniqueIds.length > 9 ? "9+" : uniqueIds.length}
                </text>
              </>
            )}

            {/* Delay warning icon */}
            {node.isDelayed && (
              <text x={node.x - 3.5} y={node.y - r - 5} fontSize={8} fill="#F59E0B">⚠</text>
            )}
          </g>
        );
      })}
    </g>
  );
}

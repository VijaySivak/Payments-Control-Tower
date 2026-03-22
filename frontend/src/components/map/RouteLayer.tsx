"use client";
import type { MapFlow } from "@/lib/types";
import { MAP_STATUS_COLORS, SEVERITY_MAP_COLORS } from "@/lib/constants";
import { mercatorProject, WORLD_MAP_WIDTH, WORLD_MAP_HEIGHT } from "./WorldMapBase";

interface RouteLayerProps {
  flows: MapFlow[];
  selectedFlowId?: string | null;
  onFlowClick?: (flow: MapFlow) => void;
  onFlowHover?: (flow: MapFlow | null) => void;
}

function cubicBezierPath(x1: number, y1: number, x2: number, y2: number): string {
  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const curveHeight = Math.min(dist * 0.22, 80);
  const cpX = midX;
  const cpY = midY - curveHeight;
  return `M ${x1} ${y1} Q ${cpX} ${cpY} ${x2} ${y2}`;
}

export function RouteLayer({ flows, selectedFlowId, onFlowClick, onFlowHover }: RouteLayerProps) {
  return (
    <g>
      {flows.map((flow) => {
        const [ox, oy] = mercatorProject(flow.origin_lat, flow.origin_lng, WORLD_MAP_WIDTH, WORLD_MAP_HEIGHT);
        const [dx, dy] = mercatorProject(flow.destination_lat, flow.destination_lng, WORLD_MAP_WIDTH, WORLD_MAP_HEIGHT);

        const isSelected = selectedFlowId === flow.id;
        const hasAnomaly = !!flow.anomaly_severity;
        const color = hasAnomaly
          ? SEVERITY_MAP_COLORS[flow.anomaly_severity!] ?? "#3B82F6"
          : MAP_STATUS_COLORS[flow.status] ?? "#3B82F6";

        const strokeWidth = isSelected ? 2.5 : (flow.payment_count > 3 ? 1.8 : 1.2);
        const opacity = isSelected ? 1 : (hasAnomaly ? 0.85 : 0.6);

        const path = cubicBezierPath(ox, oy, dx, dy);

        // Handle multi-hop: if route has intermediate countries, draw segments
        const routeCoords = flow.route_coordinates;
        const segments: Array<[number, number, number, number]> = [];
        if (routeCoords.length > 2) {
          for (let i = 0; i < routeCoords.length - 1; i++) {
            const [ax, ay] = mercatorProject(routeCoords[i].lat, routeCoords[i].lng, WORLD_MAP_WIDTH, WORLD_MAP_HEIGHT);
            const [bx, by] = mercatorProject(routeCoords[i + 1].lat, routeCoords[i + 1].lng, WORLD_MAP_WIDTH, WORLD_MAP_HEIGHT);
            segments.push([ax, ay, bx, by]);
          }
        }

        return (
          <g
            key={flow.id}
            style={{ cursor: "pointer" }}
            onClick={(e) => { e.stopPropagation(); onFlowClick?.(flow); }}
            onMouseEnter={() => onFlowHover?.(flow)}
            onMouseLeave={() => onFlowHover?.(null)}
          >
            {/* Glow effect for selected/anomalous */}
            {(isSelected || hasAnomaly) && (
              <path
                d={routeCoords.length > 2
                  ? segments.map(([ax, ay, bx, by]) => cubicBezierPath(ax, ay, bx, by)).join(" ")
                  : path}
                fill="none"
                stroke={color}
                strokeWidth={strokeWidth + 3}
                opacity={0.2}
                strokeLinecap="round"
              />
            )}

            {/* Main route line */}
            {routeCoords.length > 2 ? (
              segments.map(([ax, ay, bx, by], i) => (
                <path
                  key={i}
                  d={cubicBezierPath(ax, ay, bx, by)}
                  fill="none"
                  stroke={color}
                  strokeWidth={strokeWidth}
                  opacity={opacity}
                  strokeLinecap="round"
                  strokeDasharray={hasAnomaly ? "4,3" : undefined}
                />
              ))
            ) : (
              <path
                d={path}
                fill="none"
                stroke={color}
                strokeWidth={strokeWidth}
                opacity={opacity}
                strokeLinecap="round"
                strokeDasharray={hasAnomaly ? "4,3" : undefined}
              />
            )}

            {/* Arrow at destination */}
            <circle
              cx={dx}
              cy={dy}
              r={isSelected ? 3.5 : 2.5}
              fill={color}
              opacity={opacity + 0.1}
            />
          </g>
        );
      })}
    </g>
  );
}

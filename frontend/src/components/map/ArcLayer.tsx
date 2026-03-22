"use client";
import { useId } from "react";
import type { MapFlow } from "@/lib/types";
import { project, arcPath, syntheticIntermediate, flowColor } from "./MapProjection";

interface ArcLayerProps {
  flows: MapFlow[];
  selectedFlowId: string | null;
  hoveredFlowId: string | null;
  onFlowClick: (flow: MapFlow) => void;
  onFlowHover: (flow: MapFlow | null) => void;
}

interface Segment {
  x1: number; y1: number;
  x2: number; y2: number;
  pathD: string;
}

function buildSegments(flow: MapFlow): Segment[] {
  const coords = flow.route_coordinates;
  const points =
    coords.length >= 2
      ? coords
      : [
          { lat: flow.origin_lat, lng: flow.origin_lng },
          syntheticIntermediate(flow.origin_lat, flow.origin_lng, flow.destination_lat, flow.destination_lng, 0.5),
          { lat: flow.destination_lat, lng: flow.destination_lng },
        ];

  const segments: Segment[] = [];
  for (let i = 0; i < points.length - 1; i++) {
    const [x1, y1] = project(points[i].lat, points[i].lng);
    const [x2, y2] = project(points[i + 1].lat, points[i + 1].lng);
    segments.push({ x1, y1, x2, y2, pathD: arcPath(x1, y1, x2, y2) });
  }
  return segments;
}

function SingleArc({
  flow,
  isSelected,
  isHovered,
  onFlowClick,
  onFlowHover,
  filterId,
  glowId,
}: {
  flow: MapFlow;
  isSelected: boolean;
  isHovered: boolean;
  onFlowClick: (f: MapFlow) => void;
  onFlowHover: (f: MapFlow | null) => void;
  filterId: string;
  glowId: string;
}) {
  const uid = useId().replace(/:/g, "");
  const color = flowColor(flow.status, flow.anomaly_severity);
  const segments = buildSegments(flow);
  const active = isSelected || isHovered;
  const strokeWidth = active ? 2.2 : flow.payment_count > 4 ? 1.6 : 1.1;
  const opacity = active ? 1 : 0.55;
  const animDuration = flow.payment_count > 5 ? "2.2s" : "3.4s";

  return (
    <g
      style={{ cursor: "pointer" }}
      onClick={(e) => { e.stopPropagation(); onFlowClick(flow); }}
      onMouseEnter={() => onFlowHover(flow)}
      onMouseLeave={() => onFlowHover(null)}
    >
      {segments.map((seg, i) => {
        const pathId = `arc-${uid}-${i}`;
        return (
          <g key={i}>
            {/* Glow halo behind active arcs */}
            {active && (
              <path
                d={seg.pathD}
                fill="none"
                stroke={color}
                strokeWidth={strokeWidth + 5}
                opacity={0.18}
                strokeLinecap="round"
                filter={`url(#${glowId})`}
              />
            )}

            {/* Main arc line */}
            <path
              id={pathId}
              d={seg.pathD}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              opacity={opacity}
              strokeLinecap="round"
              strokeDasharray={
                flow.status === "FAILED" || flow.status === "DELAYED"
                  ? "5,3"
                  : undefined
              }
            />

            {/* Invisible fat hit area */}
            <path
              d={seg.pathD}
              fill="none"
              stroke="transparent"
              strokeWidth={12}
            />

            {/* Traveling dot along arc */}
            {(flow.status === "IN_PROGRESS" || flow.status === "DELAYED" || active) && (
              <circle r={active ? 3 : 2} fill={color} opacity={0.95} filter={`url(#${filterId})`}>
                <animateMotion
                  dur={animDuration}
                  repeatCount="indefinite"
                  keyTimes="0;1"
                  calcMode="linear"
                >
                  <mpath href={`#${pathId}`} />
                </animateMotion>
              </circle>
            )}
          </g>
        );
      })}
    </g>
  );
}

export function ArcLayer({
  flows,
  selectedFlowId,
  hoveredFlowId,
  onFlowClick,
  onFlowHover,
}: ArcLayerProps) {
  const dotFilterId = "arc-dot-glow";
  const haloFilterId = "arc-halo-glow";

  // Sort: active arcs render on top
  const sorted = [...flows].sort((a, b) => {
    const aActive = a.id === selectedFlowId || a.id === hoveredFlowId ? 1 : 0;
    const bActive = b.id === selectedFlowId || b.id === hoveredFlowId ? 1 : 0;
    return aActive - bActive;
  });

  return (
    <g>
      <defs>
        <filter id={dotFilterId} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id={haloFilterId} x="-80%" y="-80%" width="260%" height="260%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {sorted.map((flow) => (
        <SingleArc
          key={flow.id}
          flow={flow}
          isSelected={selectedFlowId === flow.id}
          isHovered={hoveredFlowId === flow.id}
          onFlowClick={onFlowClick}
          onFlowHover={onFlowHover}
          filterId={dotFilterId}
          glowId={haloFilterId}
        />
      ))}
    </g>
  );
}

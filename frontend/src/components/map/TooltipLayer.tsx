"use client";
import type { MapFlow } from "@/lib/types";
import { flowColor, MAP_WIDTH, MAP_HEIGHT } from "./MapProjection";

interface TooltipLayerProps {
  flow: MapFlow | null;
  mouseX: number;
  mouseY: number;
}

const STATUS_LABEL: Record<string, string> = {
  COMPLETED: "Completed",
  IN_PROGRESS: "In Progress",
  DELAYED: "Delayed",
  FAILED: "Failed",
  ON_HOLD: "On Hold",
  PENDING: "Pending",
};

export function TooltipLayer({ flow, mouseX, mouseY }: TooltipLayerProps) {
  if (!flow) return null;

  const TW = 170;
  const TH = flow.delayed_country ? 88 : 72;
  const PAD = 10;

  // Clamp so tooltip stays inside SVG
  const tx = Math.min(Math.max(mouseX - TW / 2, PAD), MAP_WIDTH - TW - PAD);
  const ty = Math.max(mouseY - TH - 12, PAD);

  const color = flowColor(flow.status, flow.anomaly_severity);

  return (
    <g style={{ pointerEvents: "none" }}>
      {/* Drop shadow */}
      <rect x={tx + 2} y={ty + 2} width={TW} height={TH} rx={5} fill="black" opacity={0.3} />
      {/* Background */}
      <rect
        x={tx} y={ty} width={TW} height={TH} rx={5}
        fill="#07101f"
        stroke={color}
        strokeWidth={0.8}
        opacity={0.97}
      />
      {/* Color accent bar */}
      <rect x={tx} y={ty} width={4} height={TH} rx={2} fill={color} opacity={0.9} />

      {/* Corridor */}
      <text x={tx + 12} y={ty + 15} fontSize={8.5} fill="#e2e8f0" fontWeight="bold" fontFamily="monospace">
        {flow.corridor}
      </text>

      {/* Route */}
      <text x={tx + 12} y={ty + 28} fontSize={7} fill="#94a3b8">
        {flow.route_countries.join(" → ")}
      </text>

      {/* Status dot + label */}
      <circle cx={tx + 13} cy={ty + 41} r={3} fill={color} />
      <text x={tx + 20} y={ty + 44} fontSize={7} fill={color} fontWeight="600">
        {STATUS_LABEL[flow.status] ?? flow.status}
      </text>

      {/* Payment count */}
      <text x={tx + 90} y={ty + 44} fontSize={7} fill="#64748b">
        {flow.payment_count} pmt{flow.payment_count !== 1 ? "s" : ""}
      </text>

      {/* Anomaly */}
      {flow.anomaly_severity && (
        <text x={tx + 12} y={ty + 57} fontSize={7} fill="#f97316">
          ▲ {flow.anomaly_severity} severity anomaly
        </text>
      )}

      {/* Delay */}
      {flow.delayed_country && (
        <text x={tx + 12} y={ty + 70} fontSize={7} fill="#fbbf24">
          ⚠ Stuck at {flow.delayed_country}
        </text>
      )}

      {/* Click hint */}
      <text x={tx + TW - 8} y={ty + TH - 6} fontSize={6} fill="#334155" textAnchor="end">
        click for details
      </text>
    </g>
  );
}

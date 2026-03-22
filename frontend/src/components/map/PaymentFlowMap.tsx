"use client";
import { useState, useCallback } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
} from "react-simple-maps";
import type { MapFlow } from "@/lib/types";
import { ArcLayer } from "./ArcLayer";
import { NodeLayer } from "./NodeLayer";
import { TooltipLayer } from "./TooltipLayer";
import { MapLegend } from "./MapLegend";
import { MapFilters, applyFilters, DEFAULT_FILTERS } from "./MapFilters";
import { PaymentSidePanel } from "./PaymentSidePanel";
import { MAP_WIDTH, MAP_HEIGHT } from "./MapProjection";
import { Globe, Activity } from "lucide-react";

const GEO_URL = "/countries-110m.json";

interface PaymentFlowMapProps {
  flows: MapFlow[];
  title?: string;
}

export function PaymentFlowMap({ flows, title = "Payment Flow Map" }: PaymentFlowMapProps) {
  const [hoveredFlow, setHoveredFlow] = useState<MapFlow | null>(null);
  const [selectedFlow, setSelectedFlow] = useState<MapFlow | null>(null);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [mousePos, setMousePos] = useState<[number, number]>([0, 0]);
  const filteredFlows = applyFilters(flows, filters);

  const totalPayments = filteredFlows.reduce((s, f) => s + f.payment_count, 0);
  const delayedCount = filteredFlows.filter((f) => f.delayed_country).length;
  const anomalyCount = filteredFlows.filter((f) => f.anomaly_severity).length;

  const handleFlowClick = useCallback((flow: MapFlow) => {
    setSelectedFlow((prev) => (prev?.id === flow.id ? null : flow));
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent<SVGRectElement>) => {
    const svg = e.currentTarget.closest("svg");
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const scaleX = MAP_WIDTH / rect.width;
    const scaleY = MAP_HEIGHT / rect.height;
    setMousePos([(e.clientX - rect.left) * scaleX, (e.clientY - rect.top) * scaleY]);
  }, []);

  return (
    <div className="space-y-3">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-blue-400" />
          <div>
            <h3 className="text-sm font-semibold text-white">{title}</h3>
            <p className="text-[10px] text-slate-500 mt-0.5">
              {filteredFlows.length} corridors · {totalPayments} payments
              {delayedCount > 0 && <span className="text-amber-400"> · {delayedCount} delayed</span>}
              {anomalyCount > 0 && <span className="text-red-400"> · {anomalyCount} anomalies</span>}
            </p>
          </div>
        </div>
        <MapLegend />
      </div>

      {/* Filter bar */}
      <MapFilters flows={flows} filters={filters} onChange={setFilters} />

      {/* Map container */}
      <div className="relative rounded-xl overflow-hidden border border-white/10 bg-[#060d1a]">

        {/* Grid overlay */}
        <div
          className="absolute inset-0 pointer-events-none z-0"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px)," +
              "linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />

        {/* Map */}
        <ComposableMap
          width={MAP_WIDTH}
          height={MAP_HEIGHT}
          projection="geoMercator"
          projectionConfig={{ scale: 147, center: [0, 0] }}
          style={{ width: "100%", height: "auto", display: "block" }}
        >
          {/* Global SVG defs (grid gradient, glow filter) */}
          <defs>
            <radialGradient id="mapVignette" cx="50%" cy="50%" r="70%">
              <stop offset="0%" stopColor="transparent" />
              <stop offset="100%" stopColor="#060d1a" stopOpacity="0.5" />
            </radialGradient>
            <filter id="mapGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Ocean background */}
          <rect width={MAP_WIDTH} height={MAP_HEIGHT} fill="#07101f" />

          {/* Country outlines — react-simple-maps handles geo rendering */}
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  style={{
                    default: {
                      fill: "#101e35",
                      stroke: "rgba(255,255,255,0.08)",
                      strokeWidth: 0.4,
                      outline: "none",
                    },
                    hover: {
                      fill: "#162847",
                      stroke: "rgba(255,255,255,0.15)",
                      strokeWidth: 0.5,
                      outline: "none",
                    },
                    pressed: {
                      fill: "#101e35",
                      outline: "none",
                    },
                  }}
                />
              ))
            }
          </Geographies>

          {/* Vignette overlay */}
          <rect width={MAP_WIDTH} height={MAP_HEIGHT} fill="url(#mapVignette)" style={{ pointerEvents: "none" }} />

          {/* ── Custom overlay layers ── */}
          {/* Invisible mouse-tracking rect to capture moves over ocean */}
          <rect
            width={MAP_WIDTH}
            height={MAP_HEIGHT}
            fill="transparent"
            onMouseMove={handleMouseMove}
            onClick={() => setSelectedFlow(null)}
          />

          <ArcLayer
            flows={filteredFlows}
            selectedFlowId={selectedFlow?.id ?? null}
            hoveredFlowId={hoveredFlow?.id ?? null}
            onFlowClick={handleFlowClick}
            onFlowHover={setHoveredFlow}
          />

          <NodeLayer
            flows={filteredFlows}
            selectedFlowId={selectedFlow?.id ?? null}
            onNodeClick={handleFlowClick}
            onNodeHover={() => {}}
          />

          {/* Tooltip — always rendered last (on top) */}
          <TooltipLayer
            flow={hoveredFlow}
            mouseX={mousePos[0]}
            mouseY={mousePos[1]}
          />
        </ComposableMap>

        {/* Side panel slides in from right */}
        <PaymentSidePanel
          flow={selectedFlow}
          onClose={() => setSelectedFlow(null)}
        />

        {/* Status bar */}
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-3 py-1.5 bg-[#060d1a]/85 backdrop-blur border-t border-white/8">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-[10px] text-slate-500">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
              {filteredFlows.filter((f) => f.status === "COMPLETED").length} completed
            </span>
            <span className="flex items-center gap-1 text-[10px] text-slate-500">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 inline-block" />
              {filteredFlows.filter((f) => f.status === "IN_PROGRESS").length} live
            </span>
            {delayedCount > 0 && (
              <span className="flex items-center gap-1 text-[10px] text-amber-500">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block" />
                {delayedCount} delayed
              </span>
            )}
            {anomalyCount > 0 && (
              <span className="flex items-center gap-1 text-[10px] text-red-400">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
                {anomalyCount} anomalies
              </span>
            )}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-slate-600">
            <Activity className="w-2.5 h-2.5" />
            <span>{totalPayments} payments · {filteredFlows.length} corridors</span>
          </div>
        </div>
      </div>
    </div>
  );
}

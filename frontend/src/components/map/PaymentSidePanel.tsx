"use client";
import { useRouter } from "next/navigation";
import type { MapFlow } from "@/lib/types";
import {
  X, ArrowRight, AlertTriangle, Clock, CheckCircle2,
  XCircle, Pause, Activity, ExternalLink, type LucideIcon,
} from "lucide-react";

interface PaymentSidePanelProps {
  flow: MapFlow | null;
  onClose: () => void;
}

const STATUS_META: Record<string, { icon: LucideIcon, color: string, label: string }> = {
  COMPLETED:   { icon: CheckCircle2,  color: "text-emerald-400", label: "Completed" },
  IN_PROGRESS: { icon: Activity,      color: "text-blue-400",    label: "In Progress" },
  DELAYED:     { icon: Clock,         color: "text-amber-400",   label: "Delayed" },
  FAILED:      { icon: XCircle,       color: "text-red-400",     label: "Failed" },
  ON_HOLD:     { icon: Pause,         color: "text-indigo-400",  label: "On Hold" },
  PENDING:     { icon: Clock,         color: "text-slate-400",   label: "Pending" },
};

const SEVERITY_META: Record<string, { color: string; bg: string }> = {
  CRITICAL: { color: "text-red-400",    bg: "bg-red-900/30 border-red-700/40" },
  HIGH:     { color: "text-orange-400", bg: "bg-orange-900/30 border-orange-700/40" },
  MEDIUM:   { color: "text-amber-400",  bg: "bg-amber-900/30 border-amber-700/40" },
  LOW:      { color: "text-blue-400",   bg: "bg-blue-900/30 border-blue-700/40" },
};

export function PaymentSidePanel({ flow, onClose }: PaymentSidePanelProps) {
  const router = useRouter();

  const visible = flow !== null;

  return (
    <div
      className={`absolute top-0 right-0 h-full w-72 z-30 transition-transform duration-300 ease-out ${
        visible ? "translate-x-0" : "translate-x-full"
      }`}
    >
      {flow && (
        <div className="h-full bg-[#07101f]/97 backdrop-blur border-l border-white/10 flex flex-col overflow-hidden rounded-r-xl">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 flex-shrink-0">
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">Flow Details</span>
            </div>
            <button
              onClick={onClose}
              className="w-6 h-6 flex items-center justify-center rounded text-slate-500 hover:text-slate-200 hover:bg-white/10 transition flex-shrink-0"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Scrollable body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Corridor + status */}
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Corridor</p>
              <p className="text-sm font-bold text-white font-mono">{flow.corridor}</p>
              <div className="flex items-center gap-2 mt-2">
                {(() => {
                  const meta = STATUS_META[flow.status] ?? STATUS_META.PENDING;
                  const Icon = meta.icon;
                  return (
                    <span className={`flex items-center gap-1 text-xs font-semibold ${meta.color}`}>
                      <Icon className="w-3 h-3" />
                      {meta.label}
                    </span>
                  );
                })()}
                {flow.anomaly_severity && (
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${
                    SEVERITY_META[flow.anomaly_severity]?.bg ?? ""
                  } ${SEVERITY_META[flow.anomaly_severity]?.color ?? ""}`}>
                    {flow.anomaly_severity}
                  </span>
                )}
              </div>
            </div>

            {/* Route path */}
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Route</p>
              <div className="flex items-center flex-wrap gap-1">
                {flow.route_countries.map((c, i) => (
                  <span key={i} className="flex items-center gap-1">
                    <span
                      className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                        c === flow.delayed_country
                          ? "bg-amber-900/40 text-amber-300 border border-amber-700/40"
                          : i === 0
                          ? "bg-blue-900/30 text-blue-300 border border-blue-700/30"
                          : i === flow.route_countries.length - 1
                          ? "bg-emerald-900/30 text-emerald-300 border border-emerald-700/30"
                          : "bg-white/5 text-slate-300 border border-white/10"
                      }`}
                    >
                      {c}
                      {c === flow.delayed_country && " ⚠"}
                    </span>
                    {i < flow.route_countries.length - 1 && (
                      <ArrowRight className="w-2.5 h-2.5 text-slate-600 flex-shrink-0" />
                    )}
                  </span>
                ))}
              </div>
            </div>

            {/* Delay info */}
            {flow.delayed_country && (
              <div className="rounded-lg border border-amber-700/35 bg-amber-900/15 p-3">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-semibold text-amber-300">Payment Stuck</p>
                    <p className="text-[11px] text-amber-200/80 mt-0.5">
                      Delayed at <span className="font-mono font-bold">{flow.delayed_country}</span>
                    </p>
                    {flow.delayed_node && (
                      <p className="text-[10px] text-amber-200/60 mt-0.5 font-mono">{flow.delayed_node}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-white/5 rounded-lg p-2.5 border border-white/8">
                <p className="text-[10px] text-slate-500">Payments</p>
                <p className="text-lg font-bold text-white tabular-nums">{flow.payment_count}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-2.5 border border-white/8">
                <p className="text-[10px] text-slate-500">Hops</p>
                <p className="text-lg font-bold text-white tabular-nums">{flow.route_countries.length}</p>
              </div>
            </div>

            {/* Payment IDs */}
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">
                Payment IDs ({flow.payment_ids.length})
              </p>
              <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                {flow.payment_ids.slice(0, 12).map((id) => (
                  <button
                    key={id}
                    onClick={() => router.push(`/payments/${id}`)}
                    className="w-full flex items-center justify-between px-2 py-1.5 rounded bg-white/5 hover:bg-white/10 border border-white/8 hover:border-blue-500/40 transition group"
                  >
                    <span className="text-[10px] font-mono text-slate-400 group-hover:text-slate-200 truncate">
                      {id.slice(0, 18)}…
                    </span>
                    <ExternalLink className="w-2.5 h-2.5 text-slate-600 group-hover:text-blue-400 flex-shrink-0" />
                  </button>
                ))}
                {flow.payment_ids.length > 12 && (
                  <p className="text-[10px] text-slate-600 text-center py-1">
                    +{flow.payment_ids.length - 12} more
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Footer CTA */}
          <div className="flex-shrink-0 px-4 py-3 border-t border-white/10">
            <button
              onClick={() => router.push(`/payments?search=${flow.corridor}`)}
              className="w-full py-2 rounded-lg bg-blue-600/20 hover:bg-blue-600/35 border border-blue-500/30 text-xs font-semibold text-blue-300 hover:text-blue-200 transition"
            >
              View All in Corridor →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

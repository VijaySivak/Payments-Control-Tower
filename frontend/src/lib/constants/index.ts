import type { AnomalySeverity, AnomalyStatus, AnomalyType, PaymentPriority, PaymentStage, PaymentStatus } from "../types";

export const STAGE_COLORS: Record<PaymentStage, string> = {
  INITIATED: "text-slate-400",
  VALIDATION: "text-blue-400",
  COMPLIANCE: "text-purple-400",
  FX: "text-cyan-400",
  ROUTING: "text-indigo-400",
  SETTLEMENT: "text-amber-400",
  RECONCILIATION: "text-orange-400",
  COMPLETED: "text-emerald-400",
  FAILED: "text-red-400",
  ON_HOLD: "text-yellow-400",
};

export const STAGE_BG: Record<PaymentStage, string> = {
  INITIATED: "bg-slate-800/60 text-slate-300 border-slate-600",
  VALIDATION: "bg-blue-900/40 text-blue-300 border-blue-600",
  COMPLIANCE: "bg-purple-900/40 text-purple-300 border-purple-600",
  FX: "bg-cyan-900/40 text-cyan-300 border-cyan-600",
  ROUTING: "bg-indigo-900/40 text-indigo-300 border-indigo-600",
  SETTLEMENT: "bg-amber-900/40 text-amber-300 border-amber-600",
  RECONCILIATION: "bg-orange-900/40 text-orange-300 border-orange-600",
  COMPLETED: "bg-emerald-900/40 text-emerald-300 border-emerald-600",
  FAILED: "bg-red-900/40 text-red-300 border-red-600",
  ON_HOLD: "bg-yellow-900/40 text-yellow-300 border-yellow-600",
};

export const STATUS_BG: Record<PaymentStatus, string> = {
  PENDING: "bg-slate-800/60 text-slate-300 border-slate-600",
  IN_PROGRESS: "bg-blue-900/40 text-blue-300 border-blue-600",
  COMPLETED: "bg-emerald-900/40 text-emerald-300 border-emerald-600",
  FAILED: "bg-red-900/40 text-red-300 border-red-600",
  ON_HOLD: "bg-yellow-900/40 text-yellow-300 border-yellow-600",
  DELAYED: "bg-orange-900/40 text-orange-300 border-orange-600",
};

export const SEVERITY_BG: Record<AnomalySeverity, string> = {
  LOW: "bg-blue-900/40 text-blue-300 border-blue-600",
  MEDIUM: "bg-yellow-900/40 text-yellow-300 border-yellow-600",
  HIGH: "bg-orange-900/40 text-orange-300 border-orange-600",
  CRITICAL: "bg-red-900/40 text-red-300 border-red-600",
};

export const SEVERITY_DOT: Record<AnomalySeverity, string> = {
  LOW: "bg-blue-400",
  MEDIUM: "bg-yellow-400",
  HIGH: "bg-orange-400",
  CRITICAL: "bg-red-400",
};

export const ANOMALY_STATUS_BG: Record<AnomalyStatus, string> = {
  OPEN: "bg-red-900/40 text-red-300 border-red-600",
  INVESTIGATING: "bg-yellow-900/40 text-yellow-300 border-yellow-600",
  RESOLVED: "bg-emerald-900/40 text-emerald-300 border-emerald-600",
};

export const PRIORITY_BG: Record<PaymentPriority, string> = {
  LOW: "bg-slate-800/60 text-slate-300 border-slate-600",
  MEDIUM: "bg-blue-900/40 text-blue-300 border-blue-600",
  HIGH: "bg-amber-900/40 text-amber-300 border-amber-600",
  CRITICAL: "bg-red-900/40 text-red-300 border-red-600",
};

export const CHART_COLORS = [
  "#3B82F6", "#8B5CF6", "#06B6D4", "#10B981",
  "#F59E0B", "#EF4444", "#EC4899", "#6366F1",
];

export const STAGE_ORDER: PaymentStage[] = [
  "INITIATED", "VALIDATION", "COMPLIANCE", "FX",
  "ROUTING", "SETTLEMENT", "RECONCILIATION", "COMPLETED",
];

export const ANOMALY_TYPE_LABELS: Record<AnomalyType, string> = {
  SANCTIONS_FALSE_POSITIVE: "Sanctions Hit",
  GATEWAY_TIMEOUT: "Gateway Timeout",
  VALIDATION_ERROR: "Validation Error",
  FX_DELAY: "FX Delay",
  MISSING_INTERMEDIARY: "Missing Intermediary",
  SETTLEMENT_DELAY: "Settlement Delay",
  RECONCILIATION_MISMATCH: "Recon Mismatch",
};

export const MAP_STATUS_COLORS: Record<string, string> = {
  COMPLETED: "#10B981",
  IN_PROGRESS: "#3B82F6",
  DELAYED: "#F59E0B",
  ON_HOLD: "#EAB308",
  FAILED: "#EF4444",
  PENDING: "#64748B",
};

export const SEVERITY_MAP_COLORS: Record<string, string> = {
  CRITICAL: "#EF4444",
  HIGH: "#F97316",
  MEDIUM: "#EAB308",
  LOW: "#3B82F6",
};

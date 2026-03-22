import type { AnomalySeverity, AnomalyStatus, AnomalyType, PaymentStage, PaymentStatus, PaymentPriority } from "../types";

export function formatCurrency(amount: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatAmount(amount: number): string {
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(2)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(1)}K`;
  return amount.toFixed(2);
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(new Date(iso));
}

export function formatDateShort(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
  return `${(seconds / 86400).toFixed(1)}d`;
}

export function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function stageLabel(stage: PaymentStage): string {
  const map: Record<PaymentStage, string> = {
    INITIATED: "Initiated",
    VALIDATION: "Validation",
    COMPLIANCE: "Compliance",
    FX: "FX",
    ROUTING: "Routing",
    SETTLEMENT: "Settlement",
    RECONCILIATION: "Reconciliation",
    COMPLETED: "Completed",
    FAILED: "Failed",
    ON_HOLD: "On Hold",
  };
  return map[stage] ?? stage;
}

export function statusLabel(status: PaymentStatus): string {
  const map: Record<PaymentStatus, string> = {
    PENDING: "Pending",
    IN_PROGRESS: "In Progress",
    COMPLETED: "Completed",
    FAILED: "Failed",
    ON_HOLD: "On Hold",
    DELAYED: "Delayed",
  };
  return map[status] ?? status;
}

export function anomalyTypeLabel(type: AnomalyType): string {
  const map: Record<AnomalyType, string> = {
    SANCTIONS_FALSE_POSITIVE: "Sanctions Hit",
    GATEWAY_TIMEOUT: "Gateway Timeout",
    VALIDATION_ERROR: "Validation Error",
    FX_DELAY: "FX Delay",
    MISSING_INTERMEDIARY: "Missing Intermediary",
    SETTLEMENT_DELAY: "Settlement Delay",
    RECONCILIATION_MISMATCH: "Recon Mismatch",
  };
  return map[type] ?? type;
}

export function priorityLabel(p: PaymentPriority): string {
  const map: Record<PaymentPriority, string> = {
    LOW: "Low",
    MEDIUM: "Medium",
    HIGH: "High",
    CRITICAL: "Critical",
  };
  return map[p] ?? p;
}

export function anomalyStatusLabel(s: AnomalyStatus): string {
  const map: Record<AnomalyStatus, string> = {
    OPEN: "Open",
    INVESTIGATING: "Investigating",
    RESOLVED: "Resolved",
  };
  return map[s] ?? s;
}

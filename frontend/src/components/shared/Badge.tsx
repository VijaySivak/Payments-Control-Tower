"use client";
import { clsx } from "clsx";
import type { AnomalySeverity, AnomalyStatus, AnomalyType, PaymentPriority, PaymentStage, PaymentStatus } from "@/lib/types";
import {
  ANOMALY_STATUS_BG,
  PRIORITY_BG,
  SEVERITY_BG,
  STAGE_BG,
  STATUS_BG,
} from "@/lib/constants";
import {
  anomalyStatusLabel,
  anomalyTypeLabel,
  priorityLabel,
  stageLabel,
  statusLabel,
} from "@/lib/formatters";

interface BadgeProps {
  className?: string;
  children: React.ReactNode;
  variant?: string;
}

export function Badge({ className, children }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        className
      )}
    >
      {children}
    </span>
  );
}

export function StageBadge({ stage }: { stage: PaymentStage }) {
  return <Badge className={STAGE_BG[stage]}>{stageLabel(stage)}</Badge>;
}

export function StatusBadge({ status }: { status: PaymentStatus }) {
  return <Badge className={STATUS_BG[status]}>{statusLabel(status)}</Badge>;
}

export function SeverityBadge({ severity }: { severity: AnomalySeverity }) {
  return <Badge className={SEVERITY_BG[severity]}>{severity}</Badge>;
}

export function AnomalyTypeBadge({ type }: { type: AnomalyType }) {
  return (
    <Badge className="bg-rose-900/40 text-rose-300 border-rose-600">
      {anomalyTypeLabel(type)}
    </Badge>
  );
}

export function PriorityBadge({ priority }: { priority: PaymentPriority }) {
  return <Badge className={PRIORITY_BG[priority]}>{priorityLabel(priority)}</Badge>;
}

export function AnomalyStatusBadge({ status }: { status: AnomalyStatus }) {
  return <Badge className={ANOMALY_STATUS_BG[status]}>{anomalyStatusLabel(status)}</Badge>;
}

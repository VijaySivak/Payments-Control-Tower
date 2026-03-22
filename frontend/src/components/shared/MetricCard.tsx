"use client";
import { clsx } from "clsx";
import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon?: LucideIcon;
  trend?: "up" | "down" | "neutral";
  trendLabel?: string;
  variant?: "default" | "warning" | "critical" | "success";
  onClick?: () => void;
  className?: string;
}

const variantStyles = {
  default: "border-white/10 hover:border-blue-500/40",
  warning: "border-amber-500/30 hover:border-amber-400/60",
  critical: "border-red-500/30 hover:border-red-400/60",
  success: "border-emerald-500/30 hover:border-emerald-400/60",
};

const iconVariant = {
  default: "text-blue-400 bg-blue-500/10",
  warning: "text-amber-400 bg-amber-500/10",
  critical: "text-red-400 bg-red-500/10",
  success: "text-emerald-400 bg-emerald-500/10",
};

export function MetricCard({
  label,
  value,
  subValue,
  icon: Icon,
  trend,
  trendLabel,
  variant = "default",
  onClick,
  className,
}: MetricCardProps) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        "relative bg-white/5 backdrop-blur-sm border rounded-xl p-5 transition-all duration-200",
        variantStyles[variant],
        onClick && "cursor-pointer hover:bg-white/8 active:scale-[0.98]",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider truncate">
            {label}
          </p>
          <p className="mt-1.5 text-2xl font-bold text-white tabular-nums">
            {value}
          </p>
          {subValue && (
            <p className="mt-0.5 text-xs text-slate-500">{subValue}</p>
          )}
          {trend && trendLabel && (
            <div className="mt-2 flex items-center gap-1">
              <span
                className={clsx(
                  "text-xs font-medium",
                  trend === "up" && "text-emerald-400",
                  trend === "down" && "text-red-400",
                  trend === "neutral" && "text-slate-400"
                )}
              >
                {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trendLabel}
              </span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={clsx("p-2 rounded-lg flex-shrink-0 ml-3", iconVariant[variant])}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
    </div>
  );
}

"use client";
import { clsx } from "clsx";
import type { LucideIcon } from "lucide-react";

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  className?: string;
}

export function SectionHeader({ title, subtitle, icon: Icon, action, className }: SectionHeaderProps) {
  return (
    <div className={clsx("flex items-center justify-between", className)}>
      <div className="flex items-center gap-2.5">
        {Icon && (
          <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <Icon className="w-4 h-4 text-blue-400" />
          </div>
        )}
        <div>
          <h2 className="text-sm font-semibold text-white">{title}</h2>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}

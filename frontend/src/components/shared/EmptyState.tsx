"use client";
import { Search } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon = Search, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-4 rounded-full bg-white/5 border border-white/10 mb-4">
        <Icon className="w-8 h-8 text-slate-500" />
      </div>
      <h3 className="text-sm font-semibold text-slate-300">{title}</h3>
      {description && (
        <p className="mt-1 text-xs text-slate-500 max-w-xs">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-4 rounded-full bg-red-900/20 border border-red-700/30 mb-4">
        <span className="text-2xl">⚠</span>
      </div>
      <h3 className="text-sm font-semibold text-red-400">Failed to load data</h3>
      <p className="mt-1 text-xs text-slate-500 max-w-xs">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 text-xs font-medium bg-white/10 hover:bg-white/15 border border-white/20 rounded-lg text-slate-300 transition"
        >
          Retry
        </button>
      )}
    </div>
  );
}

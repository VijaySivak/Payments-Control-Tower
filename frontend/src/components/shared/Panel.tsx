"use client";
import { clsx } from "clsx";

interface PanelProps {
  children: React.ReactNode;
  className?: string;
  noPad?: boolean;
}

export function Panel({ children, className, noPad }: PanelProps) {
  return (
    <div
      className={clsx(
        "bg-white/5 border border-white/10 rounded-xl backdrop-blur-sm",
        !noPad && "p-5",
        className
      )}
    >
      {children}
    </div>
  );
}

export function PanelHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={clsx("border-b border-white/10 px-5 py-4", className)}>
      {children}
    </div>
  );
}

export function PanelBody({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={clsx("p-5", className)}>{children}</div>;
}

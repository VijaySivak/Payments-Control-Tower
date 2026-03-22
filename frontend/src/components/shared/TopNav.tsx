"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  CreditCard,
  LayoutDashboard,
  Play,
  Zap,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/payments", label: "Payments", icon: CreditCard, exact: false },
  { href: "/anomalies", label: "Anomalies", icon: AlertTriangle, exact: false },
  { href: "/ai-insights", label: "AI Insights", icon: BrainCircuit, exact: false },
  { href: "/replay", label: "Replay", icon: Play, exact: false },
];

export function TopNav() {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 border-b border-white/10 bg-[#060B18]/90 backdrop-blur-xl">
      <div className="max-w-screen-2xl mx-auto px-6 h-full flex items-center justify-between">
        {/* Logo / Brand */}
        <Link href="/" className="flex items-center gap-2.5 flex-shrink-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div className="hidden sm:block">
            <span className="text-sm font-bold text-white leading-none">
              Payments
            </span>
            <span className="block text-[10px] text-slate-400 leading-none mt-0.5 tracking-wider uppercase">
              Control Tower
            </span>
          </div>
        </Link>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon, exact }) => {
            const active = exact
              ? pathname === href
              : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150",
                  active
                    ? "bg-blue-500/15 text-blue-300 border border-blue-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                )}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden md:inline">{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Status indicator */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-xs text-slate-400 hidden sm:inline">Live</span>
          </div>
        </div>
      </div>
    </header>
  );
}

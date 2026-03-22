"use client";
import { useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useApi } from "@/hooks/useApi";
import { paymentsApi } from "@/lib/api/payments";
import { StageBadge, StatusBadge, SeverityBadge, PriorityBadge, AnomalyTypeBadge } from "@/components/shared/Badge";
import { Panel } from "@/components/shared/Panel";
import { PageLoader } from "@/components/shared/LoadingSkeleton";
import { EmptyState, ErrorState } from "@/components/shared/EmptyState";
import { formatCurrency, formatRelativeTime } from "@/lib/formatters";
import { SEVERITY_DOT } from "@/lib/constants";
import type { PaymentFilters } from "@/lib/api/payments";
import type { PaymentStage, PaymentStatus, AnomalySeverity } from "@/lib/types";
import { Search, SlidersHorizontal, X, ChevronLeft, ChevronRight, Timer, AlertOctagon, CheckCircle2 } from "lucide-react";
import { Suspense } from "react";
import { SLABadge } from "@/components/shared/SLABadge";

const STAGES: PaymentStage[] = ["INITIATED","VALIDATION","COMPLIANCE","FX","ROUTING","SETTLEMENT","RECONCILIATION","COMPLETED","FAILED","ON_HOLD"];
const STATUSES: PaymentStatus[] = ["PENDING","IN_PROGRESS","COMPLETED","FAILED","ON_HOLD","DELAYED"];
const SEVERITIES: AnomalySeverity[] = ["LOW","MEDIUM","HIGH","CRITICAL"];
const PRIORITIES = ["LOW","MEDIUM","HIGH","CRITICAL"];
const PAYMENT_TYPES = ["SWIFT","WIRE","ACH","SEPA","RTGS","INSTANT"];
const SORT_OPTIONS = [
  { value: "created_at", label: "Created" },
  { value: "amount", label: "Amount" },
  { value: "updated_at", label: "Updated" },
  { value: "total_processing_seconds", label: "Processing Time" },
];

function PaymentsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [filters, setFilters] = useState<PaymentFilters>({
    status: searchParams.get("status") ?? undefined,
    stage: searchParams.get("stage") ?? undefined,
    source_country: searchParams.get("source_country") ?? undefined,
    destination_country: searchParams.get("destination_country") ?? undefined,
    severity: searchParams.get("severity") ?? undefined,
    search: searchParams.get("search") ?? undefined,
    corridor: searchParams.get("corridor") ?? undefined,
    priority: searchParams.get("priority") ?? undefined,
    payment_type: searchParams.get("payment_type") ?? undefined,
    sla_breach: searchParams.get("sla_breach") === "true" ? true : undefined,
    anomaly_only: searchParams.get("anomaly_only") === "true" ? true : undefined,
    sort_by: "created_at",
    sort_dir: "desc",
    page: 1,
    page_size: 25,
  });

  const [showFilters, setShowFilters] = useState(false);
  const [localSearch, setLocalSearch] = useState(filters.search ?? "");

  const { data, loading, error, refetch } = useApi(
    () => paymentsApi.list(filters),
    [JSON.stringify(filters)]
  );

  const updateFilter = useCallback((key: keyof PaymentFilters, value: string | number | undefined) => {
    setFilters((f) => ({ ...f, [key]: value || undefined, page: 1 }));
  }, []);

  const clearFilters = () => {
    setFilters({ page: 1, page_size: 25 });
    setLocalSearch("");
  };

  const activeFilters = Object.entries(filters).filter(
    ([k, v]) => v !== undefined && !["page", "page_size"].includes(k)
  );

  return (
    <div className="max-w-screen-2xl mx-auto px-6 py-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Payments</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {data ? `${data.total.toLocaleString()} payments` : "Loading..."}
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/15 rounded-lg text-sm text-slate-300 transition"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filters
          {activeFilters.length > 0 && (
            <span className="bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {activeFilters.length}
            </span>
          )}
        </button>
      </div>

      {/* Search + Filters */}
      <Panel>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={localSearch}
              placeholder="Search by reference, client, beneficiary..."
              onChange={(e) => setLocalSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && updateFilter("search", localSearch)}
              className="w-full bg-white/5 border border-white/15 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:bg-white/8"
            />
          </div>
          <button
            onClick={() => updateFilter("search", localSearch)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium text-white transition"
          >
            Search
          </button>
        </div>

        {/* Quick preset buttons */}
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          {[
            { label: "SLA Breach", icon: Timer, active: !!filters.sla_breach, action: () => updateFilter("sla_breach", filters.sla_breach ? undefined : true as any) },
            { label: "Anomalies Only", icon: AlertOctagon, active: !!filters.anomaly_only, action: () => updateFilter("anomaly_only", filters.anomaly_only ? undefined : true as any) },
            { label: "In Progress", icon: CheckCircle2, active: filters.status === "IN_PROGRESS", action: () => updateFilter("status", filters.status === "IN_PROGRESS" ? undefined : "IN_PROGRESS") },
            { label: "On Hold", icon: AlertOctagon, active: filters.status === "ON_HOLD", action: () => updateFilter("status", filters.status === "ON_HOLD" ? undefined : "ON_HOLD") },
          ].map(({ label, icon: Icon, active, action }) => (
            <button
              key={label}
              onClick={action}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                active
                  ? "bg-blue-500/20 border-blue-500/50 text-blue-300"
                  : "bg-white/5 border-white/10 text-slate-400 hover:text-slate-200"
              }`}
            >
              <Icon className="w-3 h-3" />
              {label}
            </button>
          ))}
        </div>

        {showFilters && (
          <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Status</label>
              <select value={filters.status ?? ""} onChange={(e) => updateFilter("status", e.target.value)}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="">All statuses</option>
                {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Stage</label>
              <select value={filters.stage ?? ""} onChange={(e) => updateFilter("stage", e.target.value)}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="">All stages</option>
                {STAGES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Priority</label>
              <select value={filters.priority ?? ""} onChange={(e) => updateFilter("priority", e.target.value)}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="">All priorities</option>
                {PRIORITIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Payment Type</label>
              <select value={filters.payment_type ?? ""} onChange={(e) => updateFilter("payment_type", e.target.value)}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="">All types</option>
                {PAYMENT_TYPES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Source Country</label>
              <input type="text" placeholder="e.g. US" value={filters.source_country ?? ""}
                onChange={(e) => updateFilter("source_country", e.target.value.toUpperCase())}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Anomaly Severity</label>
              <select value={filters.severity ?? ""} onChange={(e) => updateFilter("severity", e.target.value)}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="">All severities</option>
                {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Corridor</label>
              <input type="text" placeholder="e.g. US-GB" value={filters.corridor ?? ""}
                onChange={(e) => updateFilter("corridor", e.target.value.toUpperCase())}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Sort By</label>
              <select value={filters.sort_by ?? "created_at"} onChange={(e) => updateFilter("sort_by", e.target.value)}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Sort Direction</label>
              <select value={filters.sort_dir ?? "desc"} onChange={(e) => updateFilter("sort_dir", e.target.value)}
                className="w-full bg-[#0c1629] border border-white/15 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-blue-500/50">
                <option value="desc">Newest first</option>
                <option value="asc">Oldest first</option>
              </select>
            </div>
            {activeFilters.length > 0 && (
              <div className="flex items-end">
                <button onClick={clearFilters} className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300">
                  <X className="w-3 h-3" /> Clear all
                </button>
              </div>
            )}
          </div>
        )}
      </Panel>

      {/* Table */}
      {error ? (
        <ErrorState message={error} onRetry={refetch} />
      ) : loading && !data ? (
        <PageLoader />
      ) : data && data.payments.length === 0 ? (
        <EmptyState title="No payments found" description="Try adjusting your filters or search query" />
      ) : data ? (
        <Panel noPad>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  {["Reference", "Client / Beneficiary", "Route", "Amount", "Stage", "Status", "Priority", "Anomaly", "SLA", "Updated"].map((h) => (
                    <th key={h} className="text-left text-xs font-medium text-slate-400 px-4 py-3 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {data.payments.map((p) => (
                  <tr
                    key={p.id}
                    onClick={() => router.push(`/payments/${p.id}`)}
                    className="hover:bg-white/5 cursor-pointer transition group"
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono text-xs text-blue-300 group-hover:text-blue-200">{p.payment_reference}</span>
                    </td>
                    <td className="px-4 py-3 max-w-[200px]">
                      <div className="text-xs text-slate-200 truncate">{p.source_client_name}</div>
                      <div className="text-xs text-slate-500 truncate">{p.beneficiary_name}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-xs font-mono text-slate-400">{p.source_country} → {p.destination_country}</span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-xs font-semibold text-white tabular-nums">
                        {formatCurrency(p.amount, p.source_currency)}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <StageBadge stage={p.current_stage} />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <StatusBadge status={p.current_status} />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <PriorityBadge priority={p.priority} />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {p.anomaly_flag && p.anomaly_type ? (
                        <div className="flex items-center gap-1.5">
                          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${p.anomaly_severity ? SEVERITY_DOT[p.anomaly_severity] : "bg-slate-500"}`} />
                          <AnomalyTypeBadge type={p.anomaly_type} />
                        </div>
                      ) : (
                        <span className="text-xs text-slate-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {p.sla_breach ? (
                        <SLABadge breach={true} recovered={p.recovered} breachSeconds={undefined} />
                      ) : (
                        <span className="text-xs text-slate-600">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-xs text-slate-500">
                      {formatRelativeTime(p.updated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-4 py-3 border-t border-white/10 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              {((filters.page! - 1) * filters.page_size!) + 1}–{Math.min(filters.page! * filters.page_size!, data.total)} of {data.total.toLocaleString()}
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={filters.page === 1}
                onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
                className="p-1.5 rounded-lg border border-white/15 text-slate-400 hover:text-white hover:border-white/30 disabled:opacity-30 disabled:cursor-not-allowed transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs text-slate-400">
                Page {filters.page} / {data.total_pages}
              </span>
              <button
                disabled={filters.page === data.total_pages}
                onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
                className="p-1.5 rounded-lg border border-white/15 text-slate-400 hover:text-white hover:border-white/30 disabled:opacity-30 disabled:cursor-not-allowed transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </Panel>
      ) : null}
    </div>
  );
}

export default function PaymentsPage() {
  return (
    <Suspense fallback={<PageLoader />}>
      <PaymentsContent />
    </Suspense>
  );
}

"use client";
import { useState, useRef, useEffect } from "react";
import type { MapFlow } from "@/lib/types";
import { Filter, X, ChevronDown } from "lucide-react";

export interface MapFilterState {
  statuses: string[];
  countries: string[];
  minPayments: number;
}

export const DEFAULT_FILTERS: MapFilterState = {
  statuses: [],
  countries: [],
  minPayments: 0,
};

const ALL_STATUSES = [
  { value: "IN_PROGRESS", label: "In Progress", color: "#3B82F6" },
  { value: "COMPLETED",   label: "Completed",   color: "#10B981" },
  { value: "DELAYED",     label: "Delayed",     color: "#F59E0B" },
  { value: "FAILED",      label: "Failed",      color: "#EF4444" },
  { value: "ON_HOLD",     label: "On Hold",     color: "#6366F1" },
  { value: "PENDING",     label: "Pending",     color: "#64748B" },
];

interface MapFiltersProps {
  flows: MapFlow[];
  filters: MapFilterState;
  onChange: (f: MapFilterState) => void;
}

export function applyFilters(flows: MapFlow[], filters: MapFilterState): MapFlow[] {
  return flows.filter((f) => {
    if (filters.statuses.length && !filters.statuses.includes(f.status)) return false;
    if (filters.countries.length) {
      const countries = f.route_countries;
      if (!filters.countries.some((c) => countries.includes(c))) return false;
    }
    if (f.payment_count < filters.minPayments) return false;
    return true;
  });
}

export function MapFilters({ flows, filters, onChange }: MapFiltersProps) {
  const [showCountries, setShowCountries] = useState(false);
  const countryDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!showCountries) return;
    const handler = (e: MouseEvent) => {
      if (countryDropdownRef.current && !countryDropdownRef.current.contains(e.target as Node)) {
        setShowCountries(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [showCountries]);

  const uniqueCountries = Array.from(
    new Set(flows.flatMap((f) => f.route_countries))
  ).sort();

  const activeCount =
    filters.statuses.length +
    filters.countries.length +
    (filters.minPayments > 0 ? 1 : 0);

  const toggleStatus = (s: string) => {
    const next = filters.statuses.includes(s)
      ? filters.statuses.filter((x) => x !== s)
      : [...filters.statuses, s];
    onChange({ ...filters, statuses: next });
  };

  const toggleCountry = (c: string) => {
    const next = filters.countries.includes(c)
      ? filters.countries.filter((x) => x !== c)
      : [...filters.countries, c];
    onChange({ ...filters, countries: next });
  };

  const reset = () => onChange(DEFAULT_FILTERS);

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Status chips */}
      <div className="flex items-center gap-1 flex-wrap">
        {ALL_STATUSES.map(({ value, label, color }) => {
          const active = filters.statuses.includes(value);
          return (
            <button
              key={value}
              onClick={() => toggleStatus(value)}
              className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border transition-all ${
                active
                  ? "bg-white/15 border-white/30 text-white"
                  : "bg-white/5 border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200"
              }`}
            >
              <span
                className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: active ? color : "#64748B" }}
              />
              {label}
            </button>
          );
        })}
      </div>

      {/* Country filter */}
      <div className="relative" ref={countryDropdownRef}>
        <button
          onClick={() => setShowCountries((p) => !p)}
          className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border transition-all ${
            filters.countries.length > 0
              ? "bg-white/15 border-white/30 text-white"
              : "bg-white/5 border-white/10 text-slate-400 hover:border-white/20 hover:text-slate-200"
          }`}
        >
          <Filter className="w-2.5 h-2.5" />
          Countries {filters.countries.length > 0 && `(${filters.countries.length})`}
          <ChevronDown className="w-2.5 h-2.5" />
        </button>
        {showCountries && (
          <div className="absolute top-full left-0 mt-1 z-50 w-48 bg-[#0c1629] border border-white/15 rounded-lg shadow-2xl overflow-hidden">
            <div className="max-h-48 overflow-y-auto py-1">
              {uniqueCountries.map((c) => {
                const active = filters.countries.includes(c);
                return (
                  <button
                    key={c}
                    onClick={() => toggleCountry(c)}
                    className={`w-full text-left px-3 py-1.5 text-[11px] font-mono flex items-center gap-2 hover:bg-white/8 transition ${
                      active ? "text-blue-300" : "text-slate-400"
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                        active ? "bg-blue-400" : "bg-white/20"
                      }`}
                    />
                    {c}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Min payments slider */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-slate-500">≥</span>
        <input
          type="range"
          min={0}
          max={10}
          value={filters.minPayments}
          onChange={(e) => onChange({ ...filters, minPayments: Number(e.target.value) })}
          className="w-16 h-1 accent-blue-500 cursor-pointer"
        />
        <span className="text-[10px] text-slate-400 w-4">{filters.minPayments}</span>
        <span className="text-[10px] text-slate-500">pmt</span>
      </div>

      {/* Reset */}
      {activeCount > 0 && (
        <button
          onClick={reset}
          className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] text-slate-400 hover:text-white border border-white/10 hover:border-white/25 bg-white/5 transition"
        >
          <X className="w-2.5 h-2.5" />
          Clear ({activeCount})
        </button>
      )}
    </div>
  );
}

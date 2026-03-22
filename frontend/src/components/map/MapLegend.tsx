"use client";

export function MapLegend() {
  const items = [
    { color: "#10B981", label: "Completed" },
    { color: "#3B82F6", label: "In Progress" },
    { color: "#F59E0B", label: "Delayed" },
    { color: "#EF4444", label: "Failed / Critical" },
    { color: "#6366F1", label: "Intermediary" },
  ];

  return (
    <div className="flex items-center gap-4 flex-wrap">
      {items.map(({ color, label }) => (
        <div key={label} className="flex items-center gap-1.5">
          <div
            className="w-3 h-1.5 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="text-xs text-slate-400">{label}</span>
        </div>
      ))}
    </div>
  );
}

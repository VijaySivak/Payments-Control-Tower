// Manual Mercator projection that matches react-simple-maps internals
// ComposableMap: width=800, height=430, projectionConfig={{ scale: 147, center: [0, 0] }}

export const MAP_WIDTH = 800;
export const MAP_HEIGHT = 430;
export const MAP_SCALE = 147;

/** Convert lat/lng to SVG x/y coordinates */
export function project(lat: number, lng: number): [number, number] {
  const x = MAP_SCALE * (lng * Math.PI / 180) + MAP_WIDTH / 2;
  const latRad = lat * Math.PI / 180;
  const y = -MAP_SCALE * Math.log(Math.tan(Math.PI / 4 + latRad / 2)) + MAP_HEIGHT / 2;
  return [x, y];
}

/** Quadratic bezier arc path between two SVG points, curving toward the north */
export function arcPath(
  x1: number, y1: number,
  x2: number, y2: number,
  curvature = 0.28,
): string {
  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist < 1) return `M ${x1} ${y1} L ${x2} ${y2}`;
  const offset = Math.min(dist * curvature, 85);
  // Perpendicular offset: rotate 90° CCW and scale, always curving upward
  const norm = dist;
  const cpX = midX - (dy / norm) * offset;
  const cpY = midY + (dx / norm) * offset - offset * 0.6;
  return `M ${x1} ${y1} Q ${cpX} ${cpY} ${x2} ${y2}`;
}

/** Generate a synthetic intermediate node at a fraction along the arc */
export function syntheticIntermediate(
  lat1: number, lng1: number,
  lat2: number, lng2: number,
  t = 0.5,
): { lat: number; lng: number } {
  return {
    lat: lat1 + (lat2 - lat1) * t,
    lng: lng1 + (lng2 - lng1) * t,
  };
}

export function flowColor(status: string, anomalySeverity?: string | null): string {
  if (anomalySeverity === "CRITICAL") return "#EF4444";
  if (anomalySeverity === "HIGH") return "#F97316";
  switch (status) {
    case "COMPLETED":   return "#10B981";
    case "IN_PROGRESS": return "#3B82F6";
    case "DELAYED":     return "#F59E0B";
    case "ON_HOLD":     return "#6366F1";
    case "FAILED":      return "#EF4444";
    default:            return "#64748B";
  }
}

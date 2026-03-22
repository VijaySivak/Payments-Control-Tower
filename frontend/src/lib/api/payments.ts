import { apiClient } from "./client";
import type {
  AdvancedSimulationRequest,
  AdvancedSimulationResponse,
  AIPackage,
  AISummary,
  AgentTrace,
  Anomaly,
  CorridorRiskInsight,
  CountryData,
  DelayHotspot,
  EnhancedCorridor,
  ExceptionPattern,
  MapFlow,
  NodeHealth,
  NodeRiskWatchlistItem,
  ObservabilityPackage,
  OperatorSummary,
  OverviewMetrics,
  Payment,
  PaymentEvent,
  PaymentJourney,
  PaymentListResponse,
  PaymentLog,
  PaymentSummary,
  PriorityQueueItem,
  RCAResult,
  Recommendation,
  RepairAction,
  ReplayComparisonResponse,
  ReplayOverrideRequest,
  SimulationRequest,
  SimulationResponse,
  StageMetrics,
  SystemAnomalyInsight,
  SystemHealth,
} from "../types";

export interface PaymentFilters {
  status?: string;
  stage?: string;
  source_country?: string;
  destination_country?: string;
  anomaly_type?: string;
  severity?: string;
  search?: string;
  corridor?: string;
  priority?: string;
  payment_type?: string;
  sla_breach?: boolean;
  anomaly_only?: boolean;
  sort_by?: string;
  sort_dir?: string;
  page?: number;
  page_size?: number;
}

export interface AnomalyFilters {
  severity?: string;
  anomaly_type?: string;
  country?: string;
  stage?: string;
  status?: string;
  corridor?: string;
  node?: string;
  action_status?: string;
}

export interface LogFilters {
  level?: string;
  component?: string;
  search?: string;
}

function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const q = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== "")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join("&");
  return q ? `?${q}` : "";
}

// Payments
export const paymentsApi = {
  list: (filters: PaymentFilters = {}) =>
    apiClient.get<PaymentListResponse>(`/payments${buildQuery(filters as Record<string, string | number | boolean | undefined>)}`),

  get: (id: string) => apiClient.get<Payment>(`/payments/${id}`),

  journey: (id: string) => apiClient.get<PaymentJourney>(`/payments/${id}/journey`),

  timeline: (id: string) => apiClient.get<PaymentEvent[]>(`/payments/${id}/timeline`),

  logs: (id: string, filters: LogFilters = {}) =>
    apiClient.get<PaymentLog[]>(`/payments/${id}/logs${buildQuery(filters as Record<string, string | undefined>)}`),

  events: (id: string) => apiClient.get<PaymentEvent[]>(`/payments/${id}/events`),

  anomalies: (id: string) => apiClient.get<Anomaly[]>(`/payments/${id}/anomalies`),

  observability: (id: string) =>
    apiClient.get<ObservabilityPackage>(`/payments/${id}/observability`),

  simulate: (request: SimulationRequest) =>
    apiClient.post<SimulationResponse>("/payments/simulate", request),

  simulateAdvanced: (request: AdvancedSimulationRequest) =>
    apiClient.post<AdvancedSimulationResponse>("/payments/simulate-advanced", request),

  replay: (id: string) =>
    apiClient.post<SimulationResponse>(`/payments/${id}/replay`, {}),

  replayAdvanced: (id: string, request: ReplayOverrideRequest = {}) =>
    apiClient.post<ReplayComparisonResponse>(`/payments/${id}/replay-advanced`, request),
};

// Control Tower
export const controlTowerApi = {
  overview: () => apiClient.get<OverviewMetrics>("/control-tower/overview"),

  systemHealth: () => apiClient.get<SystemHealth>("/control-tower/system-health"),

  livePayments: (limit = 20) =>
    apiClient.get<PaymentSummary[]>(`/control-tower/live-payments?limit=${limit}`),

  anomalies: (filters: AnomalyFilters = {}) =>
    apiClient.get<Anomaly[]>(`/control-tower/anomalies${buildQuery(filters as Record<string, string | undefined>)}`),

  corridors: () => apiClient.get<EnhancedCorridor[]>("/control-tower/corridors"),

  countries: () => apiClient.get<CountryData[]>("/control-tower/countries"),

  mapFlows: () => apiClient.get<MapFlow[]>("/control-tower/map-flows"),

  stageMetrics: () => apiClient.get<StageMetrics[]>("/control-tower/stage-metrics"),

  nodeHealth: () => apiClient.get<NodeHealth[]>("/control-tower/node-health"),

  delayHotspots: () => apiClient.get<DelayHotspot>("/control-tower/delay-hotspots"),

  exceptionPatterns: () => apiClient.get<ExceptionPattern>("/control-tower/exception-patterns"),
};

// AI Intelligence (Phase 3)
export const aiApi = {
  // Payment-level AI
  paymentRCA: (id: string) => apiClient.get<RCAResult>(`/payments/${id}/rca`),
  paymentRecommendations: (id: string) => apiClient.get<Recommendation[]>(`/payments/${id}/recommendations`),
  paymentRepairActions: (id: string) => apiClient.get<RepairAction[]>(`/payments/${id}/repair-actions`),
  paymentAgentTrace: (id: string) => apiClient.get<AgentTrace>(`/payments/${id}/agent-trace`),
  paymentAISummary: (id: string) => apiClient.get<AISummary>(`/payments/${id}/ai-summary`),
  paymentAIPackage: (id: string) => apiClient.get<AIPackage>(`/payments/${id}/ai-package`),

  // Anomaly-level AI
  anomalyRCA: (id: string) => apiClient.get<RCAResult>(`/anomalies/${id}/rca`),
  anomalyRecommendations: (id: string) => apiClient.get<Recommendation[]>(`/anomalies/${id}/recommendations`),

  // Control tower AI
  priorityQueue: (limit = 15) => apiClient.get<PriorityQueueItem[]>(`/ai/priority-queue?limit=${limit}`),
  systemAnomalyInsights: () => apiClient.get<SystemAnomalyInsight[]>("/ai/system-anomaly-insights"),
  corridorRiskInsights: () => apiClient.get<CorridorRiskInsight[]>("/ai/corridor-risk-insights"),
  nodeRiskWatchlist: () => apiClient.get<NodeRiskWatchlistItem[]>("/ai/node-risk-watchlist"),
  operatorSummary: () => apiClient.get<OperatorSummary>("/ai/operator-summary"),
};

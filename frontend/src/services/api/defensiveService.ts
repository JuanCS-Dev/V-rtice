import { apiClient } from "@/lib/api/client";

// ========= TYPES (baseado no backend real) =========

export interface BehavioralAnalysisRequest {
  events: Array<{
    timestamp: string;
    event_type: string;
    user_id?: string;
    ip_address?: string;
    user_agent?: string;
    endpoint?: string;
    method?: string;
    status_code?: number;
    response_time?: number;
  }>;
}

export interface BehavioralAnalysisResponse {
  analysis_id: string;
  is_anomaly: boolean;
  confidence: number; // 0-1
  risk_score: number; // 0-100
  anomaly_type?: "rate" | "pattern" | "geo" | "time" | "behavioral";
  explanation: string;
  recommendations: string[];
}

export interface TrafficAnalysisRequest {
  traffic_data: {
    source_ip: string;
    dest_ip: string;
    source_port: number;
    dest_port: number;
    protocol: string;
    packet_size: number;
    timestamp: string;
  }[];
  analysis_window?: number; // seconds
}

export interface TrafficAnalysisResponse {
  analysis_id: string;
  anomalies_detected: number;
  threats: Array<{
    type: "ddos" | "port_scan" | "data_exfil" | "malware_c2";
    severity: "critical" | "high" | "medium" | "low";
    source_ip: string;
    confidence: number;
    description: string;
  }>;
  recommendations: string[];
}

export interface BaselineStatus {
  is_trained: boolean;
  last_trained: string | null;
  training_samples: number;
  accuracy: number | null;
  model_version: string | null;
}

export interface BehavioralMetrics {
  total_events_analyzed: number;
  anomalies_detected: number;
  false_positives: number;
  accuracy: number;
  avg_response_time: number;
  last_updated: string;
}

export interface TrafficMetrics {
  total_packets: number;
  total_bytes: number;
  unique_sources: number;
  unique_destinations: number;
  protocols: Record<string, number>;
  top_talkers: Array<{ ip: string; bytes: number }>;
  anomalies_count: number;
}

// ========= DEFENSIVE SERVICE =========

export const defensiveService = {
  // Behavioral Analysis
  async analyzeBehavior(
    request: BehavioralAnalysisRequest,
  ): Promise<BehavioralAnalysisResponse> {
    const response = await apiClient.post<BehavioralAnalysisResponse>(
      "/api/defensive/behavioral/analyze",
      request,
    );
    return response.data;
  },

  async analyzeBehaviorBatch(
    requests: BehavioralAnalysisRequest[],
  ): Promise<BehavioralAnalysisResponse[]> {
    const response = await apiClient.post<BehavioralAnalysisResponse[]>(
      "/api/defensive/behavioral/analyze-batch",
      { batch: requests },
    );
    return response.data;
  },

  async trainBaseline(
    trainingData: any,
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(
      "/api/defensive/behavioral/train-baseline",
      trainingData,
    );
    return response.data;
  },

  async getBaselineStatus(): Promise<BaselineStatus> {
    const response = await apiClient.get<BaselineStatus>(
      "/api/defensive/behavioral/baseline-status",
    );
    return response.data;
  },

  async getBehavioralMetrics(): Promise<BehavioralMetrics> {
    const response = await apiClient.get<BehavioralMetrics>(
      "/api/defensive/behavioral/metrics",
    );
    return response.data;
  },

  // Traffic Analysis
  async analyzeTraffic(
    request: TrafficAnalysisRequest,
  ): Promise<TrafficAnalysisResponse> {
    const response = await apiClient.post<TrafficAnalysisResponse>(
      "/api/defensive/traffic/analyze",
      request,
    );
    return response.data;
  },

  async analyzeTrafficBatch(
    requests: TrafficAnalysisRequest[],
  ): Promise<TrafficAnalysisResponse[]> {
    const response = await apiClient.post<TrafficAnalysisResponse[]>(
      "/api/defensive/traffic/analyze-batch",
      { batch: requests },
    );
    return response.data;
  },

  async getTrafficMetrics(): Promise<TrafficMetrics> {
    const response = await apiClient.get<TrafficMetrics>(
      "/api/defensive/traffic/metrics",
    );
    return response.data;
  },
};

import { apiClient } from "@/lib/api/client";

// ========= TYPES (baseado no backend real - 14 endpoints) =========

export interface ThreatDetectRequest {
  data: {
    source: string;
    indicators: string[];
    severity?: "low" | "medium" | "high" | "critical";
  };
}

export interface Threat {
  threat_id: string;
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  source: string;
  indicators: string[];
  detected_at: string;
  status: "active" | "contained" | "eliminated";
  confidence: number;
  description: string;
}

export interface ImmuneAgent {
  agent_id: string;
  type:
    | "b_cell"
    | "t_cell_helper"
    | "t_cell_cytotoxic"
    | "t_regulatory"
    | "dendritic"
    | "macrophage"
    | "neutrophil";
  status: "active" | "inactive" | "engaged";
  activity_level: number; // 0-100
  threats_handled: number;
  last_activity: string;
  capabilities: string[];
}

export interface HomeostasisStatus {
  balance_score: number; // 0-100
  immune_pressure: number; // 0-100
  system_load: number; // 0-100
  threat_level: "low" | "medium" | "high" | "critical";
  auto_regulation: boolean;
  last_adjustment: string;
}

export interface HomeostasisAdjustRequest {
  parameter: "sensitivity" | "response_time" | "agent_count";
  value: number;
  reason?: string;
}

export interface LymphNode {
  node_id: string;
  location: string;
  agents_count: number;
  threats_processed: number;
  status: "healthy" | "stressed" | "overloaded";
  capacity: number; // 0-100
}

export interface Antibody {
  antibody_id: string;
  antigen_pattern: string;
  created_at: string;
  usage_count: number;
  effectiveness: number; // 0-100
  last_used: string | null;
}

export interface ImmuneMetrics {
  total_threats: number;
  active_threats: number;
  eliminated_threats: number;
  total_agents: number;
  active_agents: number;
  homeostasis_score: number;
  avg_response_time: number; // seconds
  antibody_count: number;
  system_health: number; // 0-100
}

// ========= IMMUNIS SERVICE =========

export const immunisService = {
  // Threat Management
  async detectThreat(request: ThreatDetectRequest): Promise<Threat> {
    const response = await apiClient.post<Threat>(
      "/api/immune/threats/detect",
      request,
    );
    return response.data;
  },

  async listThreats(filters?: {
    severity?: string;
    status?: string;
    limit?: number;
  }): Promise<Threat[]> {
    const response = await apiClient.get<Threat[]>("/api/immune/threats", {
      params: filters,
    });
    return response.data;
  },

  async getThreat(threatId: string): Promise<Threat> {
    const response = await apiClient.get<Threat>(
      `/api/immune/threats/${threatId}`,
    );
    return response.data;
  },

  // Immune Agents
  async listAgents(filters?: {
    type?: string;
    status?: string;
  }): Promise<ImmuneAgent[]> {
    const response = await apiClient.get<ImmuneAgent[]>("/api/immune/agents", {
      params: filters,
    });
    return response.data;
  },

  async getAgent(agentId: string): Promise<ImmuneAgent> {
    const response = await apiClient.get<ImmuneAgent>(
      `/api/immune/agents/${agentId}`,
    );
    return response.data;
  },

  // Homeostasis Control
  async getHomeostasisStatus(): Promise<HomeostasisStatus> {
    const response = await apiClient.get<HomeostasisStatus>(
      "/api/immune/homeostasis",
    );
    return response.data;
  },

  async adjustHomeostasis(
    request: HomeostasisAdjustRequest,
  ): Promise<{ success: boolean; new_value: number }> {
    const response = await apiClient.post(
      "/api/immune/homeostasis/adjust",
      request,
    );
    return response.data;
  },

  // Lymph Nodes
  async listLymphNodes(): Promise<LymphNode[]> {
    const response = await apiClient.get<LymphNode[]>("/api/immune/lymphnodes");
    return response.data;
  },

  async getLymphNode(nodeId: string): Promise<LymphNode> {
    const response = await apiClient.get<LymphNode>(
      `/api/immune/lymphnodes/${nodeId}`,
    );
    return response.data;
  },

  // Immunological Memory
  async getAntibodies(filters?: {
    pattern?: string;
    min_effectiveness?: number;
  }): Promise<Antibody[]> {
    const response = await apiClient.get<Antibody[]>(
      "/api/immune/memory/antibodies",
      { params: filters },
    );
    return response.data;
  },

  async searchMemory(query: string): Promise<any> {
    const response = await apiClient.get("/api/immune/memory/search", {
      params: { query },
    });
    return response.data;
  },

  // Metrics & Stats
  async getMetrics(): Promise<ImmuneMetrics> {
    const response = await apiClient.get<ImmuneMetrics>("/api/immune/metrics");
    return response.data;
  },

  async getStats(): Promise<any> {
    const response = await apiClient.get("/api/immune/stats");
    return response.data;
  },
};

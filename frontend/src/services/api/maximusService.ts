import { apiClient } from "@/lib/api/client";

// ========= TYPES =========

export interface AIChatRequest {
  message: string;
  conversation_id?: string;
  context?: Record<string, any>;
}

export interface AIChatResponse {
  response: string;
  conversation_id: string;
  tool_calls?: Array<{
    tool_name: string;
    parameters: Record<string, any>;
    result: any;
  }>;
  metadata: {
    model: string;
    tokens_used: number;
    processing_time: number;
  };
}

export interface AITool {
  name: string;
  description: string;
  parameters: Record<string, any>;
  category: string;
}

export interface OraclePredict {
  prediction_id: string;
  target: string;
  prediction_type: "threat" | "anomaly" | "incident";
  probability: number; // 0-1
  confidence: number; // 0-100
  timeframe: string;
  indicators: string[];
  recommendations: string[];
  created_at: string;
}

export interface AuroraInvestigation {
  investigation_id: string;
  target: string;
  status: "queued" | "running" | "completed" | "failed";
  services_used: string[];
  findings: Array<{
    service: string;
    data: any;
    relevance: number;
  }>;
  summary?: string;
  started_at: string;
  completed_at?: string;
}

// ========= MAXIMUS AI SERVICE =========

export const maximusService = {
  // AI Chat
  async chat(request: AIChatRequest): Promise<AIChatResponse> {
    const response = await apiClient.post<AIChatResponse>(
      "/api/ai/chat",
      request,
    );
    return response.data;
  },

  async getAIInfo(): Promise<any> {
    const response = await apiClient.get("/api/ai/");
    return response.data;
  },

  async getTools(): Promise<AITool[]> {
    const response = await apiClient.get<AITool[]>("/api/ai/tools");
    return response.data;
  },

  // Aurora Orchestrator
  async investigate(
    target: string,
    services?: string[],
  ): Promise<AuroraInvestigation> {
    const response = await apiClient.post<AuroraInvestigation>(
      "/api/aurora/investigate",
      {
        target,
        services,
      },
    );
    return response.data;
  },

  async getInvestigation(
    investigationId: string,
  ): Promise<AuroraInvestigation> {
    const response = await apiClient.get<AuroraInvestigation>(
      `/api/aurora/investigation/${investigationId}`,
    );
    return response.data;
  },

  async getAvailableServices(): Promise<string[]> {
    const response = await apiClient.get<string[]>("/api/aurora/services");
    return response.data;
  },
};

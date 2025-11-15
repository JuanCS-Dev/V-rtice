import { apiClient } from "@/lib/api/client";

// ========= TYPES (Reactive Fabric - Real-time Security Intelligence) =========

export interface TimelineEvent {
  event_id: string;
  timestamp: string;
  event_type: "threat" | "anomaly" | "incident" | "resolution";
  severity: "low" | "medium" | "high" | "critical";
  source: string;
  title: string;
  description: string;
  metadata: Record<string, any>;
  related_events: string[];
}

export interface IntelligenceFusion {
  fusion_id: string;
  created_at: string;
  sources: Array<{
    source_name: string;
    data_points: number;
    confidence: number;
  }>;
  insights: Array<{
    type: string;
    description: string;
    confidence: number;
    supporting_evidence: string[];
  }>;
  threat_level: "low" | "medium" | "high" | "critical";
  recommendations: string[];
  correlation_score: number; // 0-100
}

export interface HITLConsoleTask {
  task_id: string;
  created_at: string;
  status: "pending" | "in_progress" | "completed" | "escalated";
  priority: "low" | "medium" | "high" | "critical";
  task_type: "review" | "decision" | "validation" | "investigation";
  title: string;
  description: string;
  context: Record<string, any>;
  ai_recommendation?: string;
  human_decision?: string;
  assigned_to?: string;
  completed_at?: string;
}

export interface HITLDecision {
  decision: "approve" | "reject" | "modify" | "escalate";
  notes?: string;
  modifications?: Record<string, any>;
}

export interface HoneypotGrid {
  grid_id: string;
  name: string;
  status: "active" | "inactive" | "compromised";
  honeypots: Array<{
    honeypot_id: string;
    type: "ssh" | "http" | "ftp" | "smtp" | "rdp" | "custom";
    ip_address: string;
    port: number;
    status: "active" | "inactive" | "attacked";
    interactions: number;
    last_interaction?: string;
  }>;
  total_interactions: number;
  threat_actors: number;
  created_at: string;
}

export interface HoneypotInteraction {
  interaction_id: string;
  honeypot_id: string;
  timestamp: string;
  source_ip: string;
  source_port: number;
  interaction_type: "scan" | "probe" | "exploit" | "command" | "data_exfil";
  payload?: string;
  severity: "low" | "medium" | "high" | "critical";
  metadata: Record<string, any>;
}

export interface CreateHoneypotRequest {
  name: string;
  type: "ssh" | "http" | "ftp" | "smtp" | "rdp" | "custom";
  port: number;
  config?: Record<string, any>;
}

export interface FusionRequest {
  sources: string[]; // Array of service names to fuse
  target?: string;
  timeframe?: string;
}

// ========= REACTIVE FABRIC SERVICE =========

export const reactiveFabricService = {
  // Threat Timeline
  async getTimeline(filters?: {
    event_type?: string;
    severity?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<TimelineEvent[]> {
    const response = await apiClient.get<TimelineEvent[]>(
      "/api/fabric/timeline",
      {
        params: filters,
      },
    );
    return response.data;
  },

  async getTimelineEvent(eventId: string): Promise<TimelineEvent> {
    const response = await apiClient.get<TimelineEvent>(
      `/api/fabric/timeline/${eventId}`,
    );
    return response.data;
  },

  async addTimelineEvent(
    event: Omit<TimelineEvent, "event_id">,
  ): Promise<TimelineEvent> {
    const response = await apiClient.post<TimelineEvent>(
      "/api/fabric/timeline",
      event,
    );
    return response.data;
  },

  // Intelligence Fusion
  async createFusion(request: FusionRequest): Promise<IntelligenceFusion> {
    const response = await apiClient.post<IntelligenceFusion>(
      "/api/fabric/fusion",
      request,
    );
    return response.data;
  },

  async getFusion(fusionId: string): Promise<IntelligenceFusion> {
    const response = await apiClient.get<IntelligenceFusion>(
      `/api/fabric/fusion/${fusionId}`,
    );
    return response.data;
  },

  async listFusions(filters?: {
    threat_level?: string;
    limit?: number;
  }): Promise<IntelligenceFusion[]> {
    const response = await apiClient.get<IntelligenceFusion[]>(
      "/api/fabric/fusions",
      {
        params: filters,
      },
    );
    return response.data;
  },

  // Human-in-the-Loop Console
  async getHITLTasks(filters?: {
    status?: string;
    priority?: string;
    task_type?: string;
  }): Promise<HITLConsoleTask[]> {
    const response = await apiClient.get<HITLConsoleTask[]>(
      "/api/fabric/hitl/tasks",
      {
        params: filters,
      },
    );
    return response.data;
  },

  async getHITLTask(taskId: string): Promise<HITLConsoleTask> {
    const response = await apiClient.get<HITLConsoleTask>(
      `/api/fabric/hitl/tasks/${taskId}`,
    );
    return response.data;
  },

  async submitHITLDecision(
    taskId: string,
    decision: HITLDecision,
  ): Promise<{ success: boolean }> {
    const response = await apiClient.post(
      `/api/fabric/hitl/tasks/${taskId}/decision`,
      decision,
    );
    return response.data;
  },

  async assignHITLTask(
    taskId: string,
    userId: string,
  ): Promise<{ success: boolean }> {
    const response = await apiClient.post(
      `/api/fabric/hitl/tasks/${taskId}/assign`,
      {
        user_id: userId,
      },
    );
    return response.data;
  },

  // Honeypot Grid
  async listHoneypotGrids(): Promise<HoneypotGrid[]> {
    const response = await apiClient.get<HoneypotGrid[]>(
      "/api/fabric/honeypot/grids",
    );
    return response.data;
  },

  async getHoneypotGrid(gridId: string): Promise<HoneypotGrid> {
    const response = await apiClient.get<HoneypotGrid>(
      `/api/fabric/honeypot/grids/${gridId}`,
    );
    return response.data;
  },

  async createHoneypot(
    request: CreateHoneypotRequest,
  ): Promise<{ honeypot_id: string }> {
    const response = await apiClient.post(
      "/api/fabric/honeypot/create",
      request,
    );
    return response.data;
  },

  async getHoneypotInteractions(
    honeypotId: string,
    filters?: {
      interaction_type?: string;
      severity?: string;
      limit?: number;
    },
  ): Promise<HoneypotInteraction[]> {
    const response = await apiClient.get<HoneypotInteraction[]>(
      `/api/fabric/honeypot/${honeypotId}/interactions`,
      { params: filters },
    );
    return response.data;
  },

  async deleteHoneypot(honeypotId: string): Promise<{ success: boolean }> {
    const response = await apiClient.delete(
      `/api/fabric/honeypot/${honeypotId}`,
    );
    return response.data;
  },

  // Real-time Stats
  async getFabricStats(): Promise<{
    active_honeypots: number;
    total_interactions: number;
    pending_hitl_tasks: number;
    recent_fusions: number;
    timeline_events_24h: number;
  }> {
    const response = await apiClient.get("/api/fabric/stats");
    return response.data;
  },
};

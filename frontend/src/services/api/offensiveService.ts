import { apiClient } from "@/lib/api/client";

// ========= TYPES (baseado no backend real) =========

export interface NmapScanRequest {
  target: string;
  scan_type?: "quick" | "intense" | "ping" | "custom";
  ports?: string;
  arguments?: string;
}

export interface NmapScanResponse {
  scan_id: string;
  status: "queued" | "running" | "completed" | "failed";
  target: string;
  start_time: string;
  results?: {
    hosts: Array<{
      ip: string;
      hostname?: string;
      state: string;
      ports: Array<{
        port: number;
        protocol: string;
        state: string;
        service: string;
        version?: string;
      }>;
    }>;
  };
}

export interface VulnScanRequest {
  target: string;
  scan_type: "basic" | "full" | "web" | "network";
  depth?: "shallow" | "medium" | "deep";
}

export interface VulnScanResponse {
  scan_id: string;
  status: "running" | "completed" | "failed";
  target: string;
  vulnerabilities: Array<{
    id: string;
    title: string;
    severity: "critical" | "high" | "medium" | "low" | "info";
    cvss_score?: number;
    description: string;
    affected_component: string;
    remediation?: string;
  }>;
  summary: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

export interface SocialEngCampaignRequest {
  name: string;
  template_id: string;
  target_emails: string[];
  subject: string;
  content: string;
  schedule_time?: string;
}

export interface SocialEngCampaignResponse {
  campaign_id: string;
  name: string;
  status: "draft" | "scheduled" | "running" | "completed";
  created_at: string;
  target_count: number;
}

export interface MalwareAnalysisRequest {
  type: "file" | "hash" | "url";
  data: string; // base64 file, hash string, or URL
}

export interface MalwareAnalysisResponse {
  analysis_id: string;
  verdict: "clean" | "suspicious" | "malicious";
  confidence: number; // 0-100
  threats_detected: string[];
  signatures_matched: string[];
  behavioral_indicators: string[];
  report_url?: string;
}

// ========= OFFENSIVE SERVICE =========

export const offensiveService = {
  // Network Scanning (Nmap)
  async startNmapScan(request: NmapScanRequest): Promise<NmapScanResponse> {
    const response = await apiClient.post<NmapScanResponse>(
      "/api/nmap/scan",
      request,
    );
    return response.data;
  },

  async getNmapProfiles(): Promise<
    Array<{ name: string; description: string }>
  > {
    const response =
      await apiClient.get<Array<{ name: string; description: string }>>(
        "/api/nmap/profiles",
      );
    return response.data;
  },

  // Vulnerability Scanning
  async startVulnScan(request: VulnScanRequest): Promise<VulnScanResponse> {
    const response = await apiClient.post<VulnScanResponse>(
      "/api/vuln-scanner/scan",
      request,
    );
    return response.data;
  },

  async getVulnScanStatus(scanId: string): Promise<VulnScanResponse> {
    const response = await apiClient.get<VulnScanResponse>(
      `/api/vuln-scanner/scan/${scanId}`,
    );
    return response.data;
  },

  async getExploits(filters?: {
    severity?: string;
    platform?: string;
  }): Promise<any[]> {
    const response = await apiClient.get("/api/vuln-scanner/exploits", {
      params: filters,
    });
    return response.data;
  },

  async executeExploit(exploitId: string, target: string): Promise<any> {
    const response = await apiClient.post("/api/vuln-scanner/exploit", {
      exploit_id: exploitId,
      target,
    });
    return response.data;
  },

  // Social Engineering
  async createCampaign(
    request: SocialEngCampaignRequest,
  ): Promise<SocialEngCampaignResponse> {
    const response = await apiClient.post<SocialEngCampaignResponse>(
      "/api/social-eng/campaign",
      request,
    );
    return response.data;
  },

  async getCampaign(campaignId: string): Promise<SocialEngCampaignResponse> {
    const response = await apiClient.get<SocialEngCampaignResponse>(
      `/api/social-eng/campaign/${campaignId}`,
    );
    return response.data;
  },

  async getTemplates(): Promise<
    Array<{ id: string; name: string; description: string }>
  > {
    const response = await apiClient.get("/api/social-eng/templates");
    return response.data;
  },

  async getCampaignAnalytics(campaignId: string): Promise<any> {
    const response = await apiClient.get(
      `/api/social-eng/analytics/${campaignId}`,
    );
    return response.data;
  },

  // Malware Analysis
  async analyzeMalware(
    request: MalwareAnalysisRequest,
  ): Promise<MalwareAnalysisResponse> {
    let endpoint = "";
    switch (request.type) {
      case "file":
        endpoint = "/api/malware/analyze-file";
        break;
      case "hash":
        endpoint = "/api/malware/analyze-hash";
        break;
      case "url":
        endpoint = "/api/malware/analyze-url";
        break;
    }
    const response = await apiClient.post<MalwareAnalysisResponse>(endpoint, {
      data: request.data,
    });
    return response.data;
  },
};

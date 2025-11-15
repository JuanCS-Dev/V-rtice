import { apiClient } from "@/lib/api/client";

// ========= TYPES (SSL/TLS Certificate Analysis) =========

export interface SSLCheckRequest {
  domain: string;
  port?: number;
}

export interface SSLCertificate {
  domain: string;
  issuer: {
    common_name: string;
    organization: string;
    country: string;
  };
  subject: {
    common_name: string;
    organization?: string;
    country?: string;
  };
  valid_from: string;
  valid_until: string;
  days_remaining: number;
  serial_number: string;
  signature_algorithm: string;
  version: number;
  san_domains: string[]; // Subject Alternative Names
  is_valid: boolean;
  is_expired: boolean;
  is_self_signed: boolean;
  is_wildcard: boolean;
}

export interface SSLCheckResponse {
  domain: string;
  port: number;
  timestamp: string;
  certificate: SSLCertificate;
  chain: SSLCertificate[];
  protocol_version: string; // TLS 1.2, TLS 1.3, etc.
  cipher_suite: string;
  vulnerabilities: Array<{
    type: string;
    severity: "low" | "medium" | "high" | "critical";
    description: string;
    cve?: string;
  }>;
  score: number; // 0-100 (SSL Labs-style)
  grade: "A+" | "A" | "A-" | "B" | "C" | "D" | "E" | "F" | "T";
  warnings: string[];
  recommendations: string[];
}

export interface SSLMonitor {
  monitor_id: string;
  domain: string;
  port: number;
  check_interval: number; // minutes
  notify_before_expiry: number; // days
  last_check: string;
  next_check: string;
  status: "active" | "paused" | "failed";
  last_result?: SSLCheckResponse;
  created_at: string;
}

export interface CreateMonitorRequest {
  domain: string;
  port?: number;
  check_interval?: number; // minutes (default: 1440 = 24h)
  notify_before_expiry?: number; // days (default: 30)
}

export interface SSLHistory {
  domain: string;
  checks: Array<{
    timestamp: string;
    days_remaining: number;
    is_valid: boolean;
    score: number;
    grade: string;
  }>;
}

export interface BulkSSLCheckRequest {
  domains: Array<{
    domain: string;
    port?: number;
  }>;
}

export interface BulkSSLCheckResponse {
  total: number;
  completed: number;
  failed: number;
  results: Array<{
    domain: string;
    port: number;
    success: boolean;
    result?: SSLCheckResponse;
    error?: string;
  }>;
}

// ========= SSL SERVICE =========

export const sslService = {
  // Certificate Checking
  async checkSSL(request: SSLCheckRequest): Promise<SSLCheckResponse> {
    const response = await apiClient.post<SSLCheckResponse>(
      "/api/ssl/check",
      request,
    );
    return response.data;
  },

  async bulkCheckSSL(
    request: BulkSSLCheckRequest,
  ): Promise<BulkSSLCheckResponse> {
    const response = await apiClient.post<BulkSSLCheckResponse>(
      "/api/ssl/check/bulk",
      request,
    );
    return response.data;
  },

  // Certificate Monitoring
  async listMonitors(filters?: {
    status?: string;
    limit?: number;
  }): Promise<SSLMonitor[]> {
    const response = await apiClient.get<SSLMonitor[]>("/api/ssl/monitors", {
      params: filters,
    });
    return response.data;
  },

  async getMonitor(monitorId: string): Promise<SSLMonitor> {
    const response = await apiClient.get<SSLMonitor>(
      `/api/ssl/monitors/${monitorId}`,
    );
    return response.data;
  },

  async createMonitor(request: CreateMonitorRequest): Promise<SSLMonitor> {
    const response = await apiClient.post<SSLMonitor>(
      "/api/ssl/monitors",
      request,
    );
    return response.data;
  },

  async updateMonitor(
    monitorId: string,
    request: Partial<CreateMonitorRequest>,
  ): Promise<SSLMonitor> {
    const response = await apiClient.patch<SSLMonitor>(
      `/api/ssl/monitors/${monitorId}`,
      request,
    );
    return response.data;
  },

  async deleteMonitor(monitorId: string): Promise<{ success: boolean }> {
    const response = await apiClient.delete(`/api/ssl/monitors/${monitorId}`);
    return response.data;
  },

  async pauseMonitor(monitorId: string): Promise<{ success: boolean }> {
    const response = await apiClient.post(
      `/api/ssl/monitors/${monitorId}/pause`,
    );
    return response.data;
  },

  async resumeMonitor(monitorId: string): Promise<{ success: boolean }> {
    const response = await apiClient.post(
      `/api/ssl/monitors/${monitorId}/resume`,
    );
    return response.data;
  },

  async triggerMonitorCheck(monitorId: string): Promise<SSLCheckResponse> {
    const response = await apiClient.post<SSLCheckResponse>(
      `/api/ssl/monitors/${monitorId}/check`,
    );
    return response.data;
  },

  // History & Analytics
  async getHistory(domain: string, days?: number): Promise<SSLHistory> {
    const response = await apiClient.get<SSLHistory>("/api/ssl/history", {
      params: { domain, days: days || 90 },
    });
    return response.data;
  },

  async getExpiringCertificates(days?: number): Promise<
    Array<{
      domain: string;
      port: number;
      days_remaining: number;
      expires_at: string;
    }>
  > {
    const response = await apiClient.get("/api/ssl/expiring", {
      params: { days: days || 30 },
    });
    return response.data;
  },

  // Statistics
  async getStats(): Promise<{
    total_monitors: number;
    active_monitors: number;
    certificates_expiring_30d: number;
    certificates_expiring_7d: number;
    failed_checks_24h: number;
    average_score: number;
  }> {
    const response = await apiClient.get("/api/ssl/stats");
    return response.data;
  },

  // Certificate Details
  async getCertificateChain(
    domain: string,
    port?: number,
  ): Promise<SSLCertificate[]> {
    const response = await apiClient.get<SSLCertificate[]>("/api/ssl/chain", {
      params: { domain, port: port || 443 },
    });
    return response.data;
  },

  async validateCertificate(certificatePem: string): Promise<{
    is_valid: boolean;
    errors: string[];
    certificate: SSLCertificate;
  }> {
    const response = await apiClient.post("/api/ssl/validate", {
      certificate_pem: certificatePem,
    });
    return response.data;
  },
};

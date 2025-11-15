/**
 * Global TypeScript types for Vértice v3.3.1
 */

// ========= User & Authentication =========
export interface User {
  id: string;
  username: string;
  email: string;
  roles: string[];
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in?: number;
  refresh_token?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

// ========= API Response Wrapper =========
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  detail: string;
  error_code: string;
  timestamp: string;
  request_id: string;
  path: string;
  validation_errors?: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}

// ========= Pagination =========
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

// ========= Health Check =========
export interface HealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  service_name: string;
  timestamp: string;
  version?: string;
  dependencies?: Record<string, string>;
}

// ========= WebSocket Events =========
export type WSEventType =
  | "scan_progress"
  | "threat_detected"
  | "alert_created"
  | "consciousness_stream"
  | "maximus_prediction"
  | "execution_status";

export interface WSEvent<T = unknown> {
  type: WSEventType;
  data: T;
  timestamp: string;
  request_id?: string;
}

// ========= Scan Types =========
export interface ScanConfig {
  target: string;
  scan_type: "quick" | "standard" | "deep" | "custom";
  timeout?: number;
  ports?: string;
  options?: Record<string, unknown>;
}

export interface ScanResult {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  started_at: string;
  completed_at?: string;
  results?: unknown;
  error?: string;
}

// ========= Threat Intelligence =========
export interface Threat {
  id: string;
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  source: string;
  target?: string;
  description: string;
  indicators: string[];
  created_at: string;
  status: "active" | "mitigated" | "resolved";
}

export interface ThreatMetrics {
  total: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  recent: Threat[];
}

// ========= Immunis Types =========
export interface ImmuneAgent {
  id: string;
  type:
    | "neutrophil"
    | "macrophage"
    | "dendritic"
    | "t_helper"
    | "t_cytotoxic"
    | "b_cell"
    | "t_reg";
  status: "active" | "inactive" | "exhausted";
  threats_detected: number;
  threats_neutralized: number;
  last_activity: string;
}

export interface HomeostasisStatus {
  balance: number; // -1 to 1
  inflammation_level: number; // 0 to 100
  tolerance_level: number; // 0 to 100
  status: "optimal" | "stressed" | "critical";
}

// ========= OSINT Types =========
export interface OSINTResult {
  source: string;
  data: unknown;
  confidence: number;
  timestamp: string;
}

export interface DomainInfo {
  domain: string;
  registrar?: string;
  creation_date?: string;
  expiration_date?: string;
  name_servers?: string[];
  dns_records?: Record<string, string[]>;
  whois?: string;
}

export interface IPInfo {
  ip: string;
  country?: string;
  city?: string;
  isp?: string;
  asn?: string;
  reputation?: number;
  is_vpn?: boolean;
  is_proxy?: boolean;
  threat_level?: string;
}

// ========= UI State =========
export interface UIState {
  sidebarOpen: boolean;
  theme: "light" | "dark";
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: "success" | "warning" | "error" | "info";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// ========= Route Types =========
export type RouteRole = "admin" | "analyst" | "offensive" | "public";

export interface RouteConfig {
  path: string;
  element: React.ComponentType;
  roles?: RouteRole[];
  children?: RouteConfig[];
}

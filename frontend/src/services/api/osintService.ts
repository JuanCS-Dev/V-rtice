import { apiClient } from "@/lib/api/client";

// ========= TYPES (baseado no backend real) =========

export interface EmailAnalysisRequest {
  email: string;
}

export interface EmailAnalysisResponse {
  email: string;
  is_valid: boolean;
  is_disposable: boolean;
  is_business: boolean;
  domain: string;
  breaches: Array<{
    name: string;
    date: string;
    data_classes: string[];
  }>;
  reputation_score: number; // 0-100
  social_profiles: Array<{
    platform: string;
    url: string;
  }>;
}

export interface PhoneAnalysisRequest {
  phone: string;
  country_code?: string;
}

export interface PhoneAnalysisResponse {
  phone: string;
  is_valid: boolean;
  country: string;
  carrier: string;
  line_type: "mobile" | "landline" | "voip" | "unknown";
  location: {
    city?: string;
    region?: string;
    country: string;
  };
  spam_score: number; // 0-100
}

export interface GoogleSearchRequest {
  query: string;
  search_type: "basic" | "advanced" | "documents" | "images" | "social";
  num_results?: number;
  operators?: Record<string, string>;
}

export interface GoogleSearchResponse {
  query: string;
  results: Array<{
    title: string;
    url: string;
    snippet: string;
    source?: string;
  }>;
  total_results: number;
  search_time: number;
}

export interface ImageAnalysisRequest {
  image_url?: string;
  image_base64?: string;
}

export interface ImageAnalysisResponse {
  analysis_id: string;
  reverse_search_results: Array<{
    source: string;
    url: string;
    similarity: number;
    context?: string;
  }>;
  metadata: {
    width?: number;
    height?: number;
    format?: string;
    exif_data?: Record<string, any>;
  };
}

export interface UsernameSearchRequest {
  username: string;
  platforms?: string[]; // Se vazio, busca em todos
}

export interface UsernameSearchResponse {
  username: string;
  found_on: Array<{
    platform: string;
    profile_url: string;
    exists: boolean;
    details?: {
      name?: string;
      bio?: string;
      followers?: number;
      location?: string;
    };
  }>;
}

export interface ComprehensiveSearchRequest {
  target: string;
  search_types: ("email" | "phone" | "username" | "domain" | "ip")[];
}

export interface ComprehensiveSearchResponse {
  target: string;
  results: {
    email?: EmailAnalysisResponse;
    phone?: PhoneAnalysisResponse;
    username?: UsernameSearchResponse;
    domain?: any;
    ip?: any;
  };
  timestamp: string;
}

export interface IPAnalysisRequest {
  ip: string;
}

export interface IPAnalysisResponse {
  ip: string;
  geo: {
    country: string;
    city?: string;
    region?: string;
    latitude?: number;
    longitude?: number;
    timezone?: string;
  };
  asn: {
    number: number;
    organization: string;
  };
  reputation: {
    is_malicious: boolean;
    is_proxy: boolean;
    is_vpn: boolean;
    is_tor: boolean;
    threat_score: number; // 0-100
  };
  whois?: any;
}

export interface DomainAnalysisRequest {
  domain: string;
}

export interface DomainAnalysisResponse {
  domain: string;
  whois: {
    registrar?: string;
    created_date?: string;
    expiry_date?: string;
    registrant?: string;
  };
  dns: {
    a_records: string[];
    mx_records: string[];
    ns_records: string[];
    txt_records: string[];
  };
  reputation: {
    is_malicious: boolean;
    threat_categories: string[];
    trust_score: number; // 0-100
  };
  ssl_info?: {
    is_valid: boolean;
    issuer?: string;
    expiry_date?: string;
  };
}

// ========= OSINT SERVICE =========

export const osintService = {
  // Email Analysis
  async analyzeEmail(
    request: EmailAnalysisRequest,
  ): Promise<EmailAnalysisResponse> {
    const response = await apiClient.post<EmailAnalysisResponse>(
      "/api/email/analyze",
      request,
    );
    return response.data;
  },

  // Phone Analysis
  async analyzePhone(
    request: PhoneAnalysisRequest,
  ): Promise<PhoneAnalysisResponse> {
    const response = await apiClient.post<PhoneAnalysisResponse>(
      "/api/phone/analyze",
      request,
    );
    return response.data;
  },

  // Google OSINT
  async googleSearch(
    request: GoogleSearchRequest,
  ): Promise<GoogleSearchResponse> {
    const endpoint = `/api/google/search/${request.search_type}`;
    const response = await apiClient.post<GoogleSearchResponse>(
      endpoint,
      request,
    );
    return response.data;
  },

  async getGoogleDorks(): Promise<
    Array<{ category: string; patterns: string[] }>
  > {
    const response = await apiClient.get("/api/google/dorks/patterns");
    return response.data;
  },

  async getGoogleStats(): Promise<any> {
    const response = await apiClient.get("/api/google/stats");
    return response.data;
  },

  // Image Analysis
  async analyzeImage(
    request: ImageAnalysisRequest,
  ): Promise<ImageAnalysisResponse> {
    const response = await apiClient.post<ImageAnalysisResponse>(
      "/api/image/analyze",
      request,
    );
    return response.data;
  },

  // Username Search
  async searchUsername(
    request: UsernameSearchRequest,
  ): Promise<UsernameSearchResponse> {
    const response = await apiClient.post<UsernameSearchResponse>(
      "/api/username/search",
      request,
    );
    return response.data;
  },

  // Comprehensive Search
  async comprehensiveSearch(
    request: ComprehensiveSearchRequest,
  ): Promise<ComprehensiveSearchResponse> {
    const response = await apiClient.post<ComprehensiveSearchResponse>(
      "/api/search/comprehensive",
      request,
    );
    return response.data;
  },

  // IP Intelligence
  async analyzeIP(request: IPAnalysisRequest): Promise<IPAnalysisResponse> {
    const response = await apiClient.post<IPAnalysisResponse>(
      "/api/ip/analyze",
      request,
    );
    return response.data;
  },

  async getMyIP(): Promise<{ ip: string }> {
    const response = await apiClient.get<{ ip: string }>("/api/ip/my-ip");
    return response.data;
  },

  async analyzeMyIP(): Promise<IPAnalysisResponse> {
    const response = await apiClient.post<IPAnalysisResponse>(
      "/api/ip/analyze-my-ip",
    );
    return response.data;
  },

  // Domain Intelligence
  async analyzeDomain(
    request: DomainAnalysisRequest,
  ): Promise<DomainAnalysisResponse> {
    const response = await apiClient.post<DomainAnalysisResponse>(
      "/api/domain/analyze",
      request,
    );
    return response.data;
  },

  // Social Profile
  async analyzeSocialProfile(username: string, platform: string): Promise<any> {
    const response = await apiClient.post("/api/social/profile", {
      username,
      platform,
    });
    return response.data;
  },

  // Auto Investigation
  async autoInvestigate(target: string): Promise<any> {
    const response = await apiClient.post("/api/investigate/auto", { target });
    return response.data;
  },

  // Stats
  async getStats(): Promise<any> {
    const response = await apiClient.get("/api/osint/stats");
    return response.data;
  },
};

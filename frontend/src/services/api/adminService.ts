import { apiClient } from "@/lib/api/client";

// ========= TYPES (Admin & User Management) =========

export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  roles: string[];
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
  metadata?: Record<string, any>;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  roles?: string[];
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface UpdateUserRequest {
  email?: string;
  full_name?: string;
  roles?: string[];
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateRoleRequest {
  name: string;
  description: string;
  permissions: string[];
}

export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: "create" | "read" | "update" | "delete" | "execute";
  description: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  username: string;
  action: string;
  resource: string;
  resource_id?: string;
  ip_address: string;
  user_agent: string;
  success: boolean;
  details?: Record<string, any>;
}

export interface SystemSettings {
  id: string;
  key: string;
  value: any;
  category: "security" | "performance" | "features" | "integrations";
  description: string;
  updated_at: string;
  updated_by: string;
}

export interface UpdateSettingRequest {
  value: any;
}

export interface SystemHealth {
  status: "healthy" | "degraded" | "critical";
  uptime: number; // seconds
  services: Array<{
    name: string;
    status: "up" | "down" | "degraded";
    response_time?: number;
    last_check: string;
  }>;
  resources: {
    cpu_usage: number; // 0-100
    memory_usage: number; // 0-100
    disk_usage: number; // 0-100
  };
  errors_last_hour: number;
  warnings_last_hour: number;
}

// ========= ADMIN SERVICE =========

export const adminService = {
  // User Management
  async listUsers(filters?: {
    role?: string;
    is_active?: boolean;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ users: User[]; total: number }> {
    const response = await apiClient.get("/api/admin/users", {
      params: filters,
    });
    return response.data;
  },

  async getUser(userId: string): Promise<User> {
    const response = await apiClient.get<User>(`/api/admin/users/${userId}`);
    return response.data;
  },

  async createUser(request: CreateUserRequest): Promise<User> {
    const response = await apiClient.post<User>("/api/admin/users", request);
    return response.data;
  },

  async updateUser(userId: string, request: UpdateUserRequest): Promise<User> {
    const response = await apiClient.patch<User>(
      `/api/admin/users/${userId}`,
      request,
    );
    return response.data;
  },

  async deleteUser(userId: string): Promise<{ success: boolean }> {
    const response = await apiClient.delete(`/api/admin/users/${userId}`);
    return response.data;
  },

  async resetPassword(
    userId: string,
    newPassword: string,
  ): Promise<{ success: boolean }> {
    const response = await apiClient.post(
      `/api/admin/users/${userId}/reset-password`,
      {
        new_password: newPassword,
      },
    );
    return response.data;
  },

  // Role Management
  async listRoles(): Promise<Role[]> {
    const response = await apiClient.get<Role[]>("/api/admin/roles");
    return response.data;
  },

  async getRole(roleId: string): Promise<Role> {
    const response = await apiClient.get<Role>(`/api/admin/roles/${roleId}`);
    return response.data;
  },

  async createRole(request: CreateRoleRequest): Promise<Role> {
    const response = await apiClient.post<Role>("/api/admin/roles", request);
    return response.data;
  },

  async updateRole(
    roleId: string,
    request: Partial<CreateRoleRequest>,
  ): Promise<Role> {
    const response = await apiClient.patch<Role>(
      `/api/admin/roles/${roleId}`,
      request,
    );
    return response.data;
  },

  async deleteRole(roleId: string): Promise<{ success: boolean }> {
    const response = await apiClient.delete(`/api/admin/roles/${roleId}`);
    return response.data;
  },

  // Permission Management
  async listPermissions(): Promise<Permission[]> {
    const response = await apiClient.get<Permission[]>(
      "/api/admin/permissions",
    );
    return response.data;
  },

  async getPermission(permissionId: string): Promise<Permission> {
    const response = await apiClient.get<Permission>(
      `/api/admin/permissions/${permissionId}`,
    );
    return response.data;
  },

  // Audit Logs
  async getAuditLogs(filters?: {
    user_id?: string;
    action?: string;
    resource?: string;
    start_date?: string;
    end_date?: string;
    success?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{ logs: AuditLog[]; total: number }> {
    const response = await apiClient.get("/api/admin/audit", {
      params: filters,
    });
    return response.data;
  },

  async getAuditLog(logId: string): Promise<AuditLog> {
    const response = await apiClient.get<AuditLog>(`/api/admin/audit/${logId}`);
    return response.data;
  },

  // System Settings
  async listSettings(category?: string): Promise<SystemSettings[]> {
    const response = await apiClient.get<SystemSettings[]>(
      "/api/admin/settings",
      {
        params: { category },
      },
    );
    return response.data;
  },

  async getSetting(key: string): Promise<SystemSettings> {
    const response = await apiClient.get<SystemSettings>(
      `/api/admin/settings/${key}`,
    );
    return response.data;
  },

  async updateSetting(
    key: string,
    request: UpdateSettingRequest,
  ): Promise<SystemSettings> {
    const response = await apiClient.patch<SystemSettings>(
      `/api/admin/settings/${key}`,
      request,
    );
    return response.data;
  },

  // System Health & Monitoring
  async getSystemHealth(): Promise<SystemHealth> {
    const response = await apiClient.get<SystemHealth>("/api/admin/health");
    return response.data;
  },

  async getSystemStats(): Promise<{
    total_users: number;
    active_users: number;
    total_roles: number;
    audit_logs_24h: number;
    failed_logins_24h: number;
  }> {
    const response = await apiClient.get("/api/admin/stats");
    return response.data;
  },

  // Bulk Operations
  async bulkDeleteUsers(userIds: string[]): Promise<{ deleted: number }> {
    const response = await apiClient.post("/api/admin/users/bulk-delete", {
      user_ids: userIds,
    });
    return response.data;
  },

  async bulkUpdateUsers(
    userIds: string[],
    updates: UpdateUserRequest,
  ): Promise<{ updated: number }> {
    const response = await apiClient.post("/api/admin/users/bulk-update", {
      user_ids: userIds,
      updates,
    });
    return response.data;
  },
};

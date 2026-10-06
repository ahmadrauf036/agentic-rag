import { supabase } from "@/lib/supabase";
import type { AdminSession, AdminStats, AdminUser, DocumentInfo, Role, RoleChangeResult, SessionInfo, SessionMessage, UploadResult, UsageSummary, UserUsage } from "@/types";

const BASE_URL = import.meta.env.VITE_API_URL;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function parseError(res: Response): Promise<ApiError> {
  let message = res.statusText || `Request failed (${res.status})`;
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") message = body.detail;
  } catch {
    /* non-JSON error body */
  }
  return new ApiError(res.status, message);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const isForm = init.body instanceof FormData;

  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...(await getAuthHeaders()),
      ...init.headers,
    },
  });

  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  sessions: {
    list: () => request<SessionInfo[]>("/sessions"),
    get: (id: string) => request<SessionInfo>(`/sessions/${id}`),
    messages: (id: string) => request<SessionMessage[]>(`/sessions/${id}/messages`),
    remove: (id: string) =>
      request<{ success: boolean; detail: string }>(`/sessions/${id}`, { method: "DELETE" }),
  },
  documents: {
    list: () => request<DocumentInfo[]>("/documents"),
    upload: (files: File[]) => {
      const body = new FormData();
      files.forEach((f) => body.append("files", f)); // repeated field name
      return request<UploadResult>("/ingestion/upload", { method: "POST", body });
    },
    dependents: (hash: string) =>
    request<unknown>(`/documents/${encodeURIComponent(hash)}/dependents`),
     remove: (hash: string) =>
    request<{ success: boolean; detail: string; paused_sessions: number }>(
      `/documents/${encodeURIComponent(hash)}`,
      { method: "DELETE" },
    ),
    // remove(): added in A3, after /dependents ships
  },
  admin: {
    users: () => request<AdminUser[]>("/admin/users"),
    setRole: (userId: string, role: Role) =>
      request<RoleChangeResult>(`/admin/users/${userId}/role`, {
        method: "POST",
        body: JSON.stringify({ role }),
      }),
      stats: () => request<AdminStats>("/admin/stats"),
  sessions: () => request<AdminSession[]>("/admin/sessions"),
  },
  usage: {
  me: (days = 30) => request<UsageSummary>(`/usage?days=${days}`),
  all: (days = 30) => request<UserUsage[]>(`/usage/all?days=${days}`),
},
};



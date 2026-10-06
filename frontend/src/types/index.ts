/* ---------- Sessions & messages ---------- */

export interface SessionInfo {
  thread_id: string;
  title: string;
  selected_files: string[];
  page: number | null;
  paused_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface Source {
  source: string;
  page: number | null;
  snippet: string;
}

export interface SessionMessage {
  role: "user" | "assistant";
  content: string;
  // Only document_search produces structured sources.
  // Verify whether GET /sessions/{id}/messages returns this.
  sources?: Source[] | null;
}

/* ---------- Documents ---------- */

export interface DocumentInfo {
  source: string;      // filename shown to the user
  file_hash: string;   // unique id
  chunk_count: number;
}
/* ---------- Chat streaming ---------- */

export type ToolName =
  | "document_search"
  | "calculator"
  | "memory_search"
  | "recent_sessions"
  | "recent_messages";

export interface ChatStreamRequest {
  thread_id: string;
  message: string;
  selected_files?: string[];
  page?: number | null;
}

export type SSEEvent =
  | { type: "tool_start"; data: { tool: ToolName; args: Record<string, unknown> } }
  | { type: "tool_end"; data: { tool: ToolName; result: string } }
  | { type: "sources"; data: { tool: ToolName; sources: Source[] } }
  | { type: "token"; data: { text: string } }
  | { type: "done"; data: { thread_id: string } }
  | { type: "error"; data: { detail: string } };


export interface ChatMessage extends SessionMessage {
  id: string;
  durationMs?: number; // client-measured, only for answers from this session
}

/* ---------- Admin ---------- */

export type Role = "admin" | "user";

export interface AdminUser {
  id: string;
  email: string;
  role: Role;
  created_at: string;
  last_sign_in_at: string | null;
}

export interface RoleChangeResult {
  success: boolean;
  user_id: string;
  new_role: Role;
}

// Used by the A2 upload UI
export interface UploadResult {
  success: boolean;
  detail: string;
  num_chunks: number;
  files: { source: string; file_hash: string; num_chunks: number }[];
  unpaused_sessions: number;
}


export interface AdminStats {
  total_users: number;
  total_admins: number;
  total_documents: number;
  total_chunks: number;
  total_sessions: number;
  paused_sessions: number;
}

export type AdminSession = SessionInfo & { user_id: string };

export interface UsageSummary {
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  request_count: number;
}

export interface UserUsage extends UsageSummary {
  user_id: string;
}
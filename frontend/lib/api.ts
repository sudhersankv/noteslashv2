const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export type Project = { id: string; name: string };

export type ProjectStatus = {
  status: "empty" | "pending" | "processing" | "ready" | "failed";
  transcript_count: number;
  chunk_count: number;
  insight_count: number;
  content_type?: string;
  tags?: string[];
  message?: string;
};

export type Citation = {
  chunk_id: string;
  transcript_id: string;
  filename?: string;
  text: string;
  speaker?: string;
  similarity?: number;
};

export type InsightItem = {
  id: string;
  type: string;
  title: string;
  description?: string;
  frequency?: number;
  confidence?: number;
  evidence: { chunk_id: string; filename?: string; quote: string }[];
};

export type InsightsResponse = {
  summary: string;
  content_type?: string;
  tags?: string[];
  themes: InsightItem[];
  pain_points: InsightItem[];
  feature_requests: InsightItem[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  message_id?: string;
};

export type VoiceSession = {
  client_secret: string;
  expires_at?: number;
  model: string;
};

export type EvalResponse = {
  id?: string;
  metrics: {
    insights_total: number;
    grounded: number;
    unsupported: number;
    grounding_score: number;
  };
  unsupported_items: { insight_id: string; insight_title: string; reason: string }[];
};

export type ReportResponse = { id?: string; markdown: string };

export const api = {
  createProject: (name: string) =>
    request<Project>("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }),

  createSample: () => request<{ project: Project }>("/api/projects/sample", { method: "POST" }),

  upload: async (projectId: string, files: File[], pasteText?: string) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    if (pasteText?.trim()) form.append("paste_text", pasteText.trim());
    return request<{ uploaded: number }>(`/api/projects/${projectId}/upload`, {
      method: "POST",
      body: form,
    });
  },

  process: (projectId: string) =>
    request<{ status: string }>(`/api/projects/${projectId}/process`, { method: "POST" }),

  status: (projectId: string) => request<ProjectStatus>(`/api/projects/${projectId}/status`),

  insights: (projectId: string) => request<InsightsResponse>(`/api/projects/${projectId}/insights`),

  chat: (projectId: string, message: string) =>
    request<ChatResponse>(`/api/projects/${projectId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    }),

  chatHistory: (projectId: string) =>
    request<{ messages: ChatMessage[] }>(`/api/projects/${projectId}/chat`),

  voiceSession: (projectId: string) =>
    request<VoiceSession>(`/api/projects/${projectId}/voice/session`, { method: "POST" }),

  voiceTool: (projectId: string, query: string) =>
    request<{ snippets: { chunk_id: string; text: string; filename?: string }[] }>(
      `/api/projects/${projectId}/voice/tool`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      }
    ),

  evaluate: (projectId: string) =>
    request<EvalResponse>(`/api/projects/${projectId}/evaluate`, { method: "POST" }),

  latestEval: (projectId: string) =>
    request<EvalResponse>(`/api/projects/${projectId}/evaluate/latest`),

  report: (projectId: string) =>
    request<ReportResponse>(`/api/projects/${projectId}/report`, { method: "POST" }),

  latestReport: (projectId: string) =>
    request<ReportResponse>(`/api/projects/${projectId}/report/latest`),
};

export const REALTIME_MODEL =
  process.env.NEXT_PUBLIC_REALTIME_MODEL || "gpt-realtime";

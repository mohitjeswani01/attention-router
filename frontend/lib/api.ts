/**
 * Typed API client for Attention Router backend.
 * Uses NEXT_PUBLIC_API_BASE_URL env var with http://localhost:8000 fallback.
 */

const API_BASE =
  (typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_BASE_URL
    : process.env.NEXT_PUBLIC_API_BASE_URL) || "http://localhost:8000";

const API_V1 = `${API_BASE}/api/v1`;

// ── Types ──────────────────────────────────────────────────────────────

export interface AttentionItem {
  id: string;
  session_id: string;
  urgency_score: number;
  reason: string;
  idle_seconds: number;
  created_at: string;
  resolved: boolean;
  resolved_at: string | null;
}

export interface PolicyRule {
  id: string;
  name: string;
  condition_type: string;
  pattern: string;
  action: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApprovalDecision {
  id: string;
  session_id: string | null;
  pr_id: string | null;
  rule_id: string | null;
  decision: string;
  reason: string | null;
  decided_at: string;
}

export interface DigestPR {
  pr_id: string;
  pr_number: number;
  repo: string;
  title: string;
  risk_score: number;
  risk_factors: string[];
  summary: string;
}

export interface DigestResponse {
  summary: string;
  ready_to_merge: DigestPR[];
  needs_review: DigestPR[];
  in_progress: DigestPR[];
}

export interface PRRiskDetail {
  pr_id: string;
  pr_number: number;
  repo: string;
  title: string;
  risk_score: number;
  risk_factors: string[];
  summary: string;
  generated_at: string;
}

// ── Fetch wrapper ──────────────────────────────────────────────────────

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_V1}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    throw new ApiError(`API ${res.status}: ${res.statusText}`, res.status);
  }
  return res.json() as Promise<T>;
}

// ── Attention Queue ────────────────────────────────────────────────────

export function fetchQueue(limit = 50): Promise<AttentionItem[]> {
  return request<AttentionItem[]>(`/attention/queue?limit=${limit}`);
}

export function resolveItem(itemId: string): Promise<AttentionItem> {
  return request<AttentionItem>(`/attention/${itemId}/resolve`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

// ── Policy Gate ────────────────────────────────────────────────────────

export function fetchPolicyRules(): Promise<PolicyRule[]> {
  return request<PolicyRule[]>("/policy/rules");
}

export function fetchDecisions(limit = 50): Promise<ApprovalDecision[]> {
  return request<ApprovalDecision[]>(`/policy/decisions?limit=${limit}`);
}

// ── Merge Digest ───────────────────────────────────────────────────────

export function fetchDigest(): Promise<DigestResponse> {
  return request<DigestResponse>("/digest/today");
}

export function fetchPRDetail(prId: string): Promise<PRRiskDetail> {
  return request<PRRiskDetail>(`/digest/pr/${prId}`);
}

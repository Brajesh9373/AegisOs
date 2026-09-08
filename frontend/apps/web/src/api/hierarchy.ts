import { ApiClientError, type ApiErrorResponse } from './client';

/**
 * Agent hierarchy service — live HOE-led engineering teams backed by
 * persistent DSH SDK sessions in the Python (ECMS) backend.
 *
 * The ECMS backend is a separate origin from the `/api` BFF, so this module
 * uses its own base URL (override with VITE_ECMS_API_URL) while following
 * the same auth-token and error-shape conventions as ApiClient.
 *
 * Latency profile (warm): team spawn ~2s, message round-trip ~5s.
 * `sendMessage` long-polls the response; use `useTeamStatus` for progress
 * while a run is in flight.
 */

const ECMS_API_URL = import.meta.env.VITE_ECMS_API_URL || 'http://localhost:8000';

export interface TeamMemberSpec {
  profile_id: string;
  agent_id: string;
}

export interface HierarchyAgentInfo {
  agent_id: string;
  profile_id: string;
  role: string;
  session_id: string;
  pid: number | null;
  status: 'idle' | 'working' | 'dead';
}

export interface HierarchyTeam {
  team_id: string;
  created_at: number;
  agents: HierarchyAgentInfo[];
}

export interface HierarchyAgentStatus {
  agent_id: string;
  status: 'idle' | 'working' | 'dead';
  pending_messages: number;
  active_requests: number;
  session_id: string;
  last_heartbeat: number;
}

export interface HierarchyMessageResponse {
  team_id: string;
  agent_id: string;
  response: string;
  duration_ms: number;
}

export interface HierarchyDelegateResponse {
  team_id: string;
  from_agent: string;
  to_agent: string;
  response: string | null;
  duration_ms: number;
}

export interface HierarchyKickoffDelegation {
  label: string;
  task: string;
  to_agent: string;
  response: string | null;
}

export interface HierarchyKickoffResponse {
  team_id: string;
  project_id: string;
  breakdown: string;
  delegations: HierarchyKickoffDelegation[];
  review_note: string;
}

function toApiError(res: Response, details: string): ApiErrorResponse {
  return {
    code: `HTTP-${res.status}`,
    message: details || 'Hierarchy request failed.',
    details: res.statusText,
    traceId: 'hierarchy-' + Date.now()
  };
}

async function ecmsRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${ECMS_API_URL}${path}`, { ...options, headers });
  } catch (err: unknown) {
    throw new ApiClientError({
      code: 'NET-001',
      message: 'Unable to reach the agent backend (ECMS). Is it running on :8000?',
      details: err instanceof Error ? err.message : String(err),
      traceId: 'hierarchy-' + Date.now()
    });
  }

  if (!res.ok) {
    let message = 'Hierarchy request failed.';
    try {
      const body = await res.json();
      if (typeof body?.detail === 'string') message = body.detail;
    } catch {
      /* keep default */
    }
    throw new ApiClientError(toApiError(res, message));
  }
  return res.json() as Promise<T>;
}

const get = <T>(path: string) => ecmsRequest<T>(path);
const post = <T>(path: string, body: unknown) =>
  ecmsRequest<T>(path, { method: 'POST', body: JSON.stringify(body) });
const del = <T>(path: string) => ecmsRequest<T>(path, { method: 'DELETE' });

/** Spawn a team (default: HOE + frontend + backend engineers). */
export function createTeam(members?: TeamMemberSpec[]): Promise<HierarchyTeam> {
  return post<HierarchyTeam>('/api/hierarchy/teams', members ? { members } : {});
}

export function listTeams(): Promise<HierarchyTeam[]> {
  return get<HierarchyTeam[]>('/api/hierarchy/teams');
}

export function getTeam(teamId: string): Promise<HierarchyTeam> {
  return get<HierarchyTeam>(`/api/hierarchy/teams/${teamId}`);
}

export function deleteTeam(teamId: string): Promise<{ team_id: string; stopped: boolean }> {
  return del(`/api/hierarchy/teams/${teamId}`);
}

/**
 * Send a message to one agent and long-poll for its AI response.
 * Resolves in ~5s warm; pass a larger timeout for cold/first runs.
 */
export function sendMessage(
  teamId: string,
  agentId: string,
  content: string,
  opts: { senderName?: string; timeout?: number } = {}
): Promise<HierarchyMessageResponse> {
  return post<HierarchyMessageResponse>(`/api/hierarchy/teams/${teamId}/messages`, {
    agent_id: agentId,
    content,
    sender_name: opts.senderName ?? 'AegisOS',
    timeout: opts.timeout ?? 180
  });
}

/** Parent delegates a task to a child agent and waits for the result. */
export function delegateTask(
  teamId: string,
  fromAgent: string,
  toAgent: string,
  task: string,
  timeout = 300
): Promise<HierarchyDelegateResponse> {
  return post<HierarchyDelegateResponse>(`/api/hierarchy/teams/${teamId}/delegate`, {
    from_agent: fromAgent,
    to_agent: toAgent,
    task,
    timeout
  });
}

/** Autonomously start a bound project team (breakdown, delegate, review). */
export function kickoffTeam(
  projectId: string,
  opts: { brief?: string; timeoutEach?: number } = {}
): Promise<HierarchyKickoffResponse> {
  return post<HierarchyKickoffResponse>(`/api/hierarchy/teams/by-project/${projectId}/kickoff`, {
    brief: opts.brief,
    timeout_each: opts.timeoutEach ?? 300
  });
}

export function teamStatus(teamId: string): Promise<HierarchyAgentStatus[]> {
  return get<HierarchyAgentStatus[]>(`/api/hierarchy/teams/${teamId}/status`);
}

// ── react-query bindings live in hooks/useHierarchy.ts ────────────────
// (kept out of this module so non-React consumers can import the service
// without pulling in react-query).

export const hierarchyKeys = {
  teams: ['hierarchy', 'teams'] as const,
  team: (teamId: string) => ['hierarchy', 'team', teamId] as const,
  status: (teamId: string) => ['hierarchy', 'status', teamId] as const
};

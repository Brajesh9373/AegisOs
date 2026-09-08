import type { Express, NextFunction, Request, Response } from 'express';
import { ecms } from '../ecms.js';

/**
 * ECMS-owned routes, registered explicitly (one handler per endpoint) ahead
 * of the legacy mocks below so Express matches them first: the discovery
 * flow, the live DSH hierarchy, and the workspace surfaces whose ECMS shape
 * the frontend expects. Every handler keeps BFF edge auth (requireAuth) and
 * translates ECMS answers/errors 1:1 through the typed client.
 */

type Handler = (req: Request, res: Response, next: NextFunction) => void;
type Wrap = (fn: (...args: any[]) => any) => Handler;
type Guard = (req: Request, res: Response, next: NextFunction) => void;

function queryString(query: unknown): string {
  const params = new URLSearchParams()
  if (query !== null && typeof query === 'object') {
    for (const [key, value] of Object.entries(query as Record<string, unknown>)) {
      if (value === undefined || value === null) continue
      if (Array.isArray(value)) {
        for (const item of value) params.append(key, String(item))
      } else {
        params.set(key, String(value))
      }
    }
  }
  const serialized = params.toString()
  return serialized.length > 0 ? `?${serialized}` : ''
}

function forward(method: string, upstreamPath: (req: Request) => string) {
  return async (req: Request, res: Response) => {
    const path = upstreamPath(req) + queryString(req.query)
    const answer = await ecms<unknown>(path, {
      method,
      body: req.body,
      authorization: req.headers.authorization,
    })
    res.json(answer)
  }
}

function readRawBody(req: Request): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = []
    req.on('data', (chunk: Buffer) => chunks.push(chunk))
    req.on('end', () => resolve(Buffer.concat(chunks)))
    req.on('error', reject)
  })
}

export function registerEcmsRoutes(
  app: Express,
  requireAuth: Guard,
  asyncHandler: Wrap,
): void {
  const get = (path: string, upstream: string | ((req: Request) => string)) =>
    app.get(path, requireAuth, asyncHandler(forward('GET', typeof upstream === 'string' ? () => upstream : upstream)))
  const post = (path: string, upstream: string | ((req: Request) => string)) =>
    app.post(path, requireAuth, asyncHandler(forward('POST', typeof upstream === 'string' ? () => upstream : upstream)))
  const del = (path: string, upstream: string | ((req: Request) => string)) =>
    app.delete(path, requireAuth, asyncHandler(forward('DELETE', typeof upstream === 'string' ? () => upstream : upstream)))
  const id = (req: Request) => String(req.params.id)
  const sid = (req: Request) => String(req.params.sid)

  // ── Discovery flow (ECMS is the system of record) ──
  post('/api/discovery/sessions', '/api/discovery/sessions')
  post('/api/discovery/:sid/ingest', (req) => `/api/discovery/${sid(req)}/ingest`)
  post('/api/discovery/:sid/analyze', (req) => `/api/discovery/${sid(req)}/analyze`)
  post('/api/discovery/:sid/chat', (req) => `/api/discovery/${sid(req)}/chat`)
  post('/api/discovery/:sid/finalize', (req) => `/api/discovery/${sid(req)}/finalize`)
  post('/api/discovery/:sid/link-project', (req) => `/api/discovery/${sid(req)}/link-project`)
  post('/api/discovery/:sid/design-team', (req) => `/api/discovery/${sid(req)}/design-team`)
  post('/api/discovery/projects/:id/design-team', (req) => `/api/discovery/projects/${id(req)}/design-team`)
  get('/api/discovery/:sid', (req) => `/api/discovery/${sid(req)}`)
  get('/api/discovery/:sid/finalize-status', (req) => `/api/discovery/${sid(req)}/finalize-status`)
  get('/api/discovery/projects/:id/team', (req) => `/api/discovery/projects/${id(req)}/team`)

  // Audio upload: multipart body forwarded byte-for-byte, not JSON.
  app.post(
    '/api/discovery/transcribe',
    requireAuth,
    asyncHandler(async (req: Request, res: Response) => {
      const { ECMS_BACKEND_URL, ECMS_SERVICE_TOKEN } = process.env as Record<string, string | undefined>
      const base = (ECMS_BACKEND_URL || 'http://localhost:8000').replace(/\/+$/, '')
      const headers: Record<string, string> = {}
      if (req.headers['content-type']) headers['content-type'] = req.headers['content-type'] as string
      if (req.headers.authorization) headers['Authorization'] = req.headers.authorization as string
      if (ECMS_SERVICE_TOKEN) headers['x-ecms-service-token'] = ECMS_SERVICE_TOKEN
      const body = await readRawBody(req)
      let upstream: globalThis.Response
      try {
        upstream = await fetch(`${base}/api/discovery/transcribe`, { method: 'POST', headers, body })
      } catch (err: any) {
        res.status(502).json({ error: 'ECMS backend unreachable', details: String(err?.message || err) })
        return
      }
      res.status(upstream.status)
      const contentType = upstream.headers.get('content-type')
      if (contentType) res.set('content-type', contentType)
      res.send(await upstream.text())
    }),
  )

  // ── Live DSH hierarchy ──
  get('/api/hierarchy/teams', '/api/hierarchy/teams')
  post('/api/hierarchy/teams', '/api/hierarchy/teams')
  post('/api/hierarchy/teams/spawn-for-project', '/api/hierarchy/teams/spawn-for-project')
  get('/api/hierarchy/teams/by-project/:projectId', (req) => `/api/hierarchy/teams/by-project/${req.params.projectId}`)
  get('/api/hierarchy/teams/:teamId', (req) => `/api/hierarchy/teams/${req.params.teamId}`)
  del('/api/hierarchy/teams/:teamId', (req) => `/api/hierarchy/teams/${req.params.teamId}`)
  post('/api/hierarchy/teams/:teamId/messages', (req) => `/api/hierarchy/teams/${req.params.teamId}/messages`)
  post('/api/hierarchy/teams/:teamId/delegate', (req) => `/api/hierarchy/teams/${req.params.teamId}/delegate`)
  post('/api/hierarchy/teams/by-project/:projectId/kickoff', (req) => `/api/hierarchy/teams/by-project/${req.params.projectId}/kickoff`)
  get('/api/hierarchy/teams/:teamId/status', (req) => `/api/hierarchy/teams/${req.params.teamId}/status`)
  get('/api/hierarchy/procedures', '/api/hierarchy/procedures')
  post('/api/hierarchy/procedures', '/api/hierarchy/procedures')
  get('/api/hierarchy/preferences', '/api/hierarchy/preferences')
  post('/api/hierarchy/preferences', '/api/hierarchy/preferences')
  get('/api/hierarchy/patterns', '/api/hierarchy/patterns')
  post('/api/hierarchy/patterns', '/api/hierarchy/patterns')
  get('/api/hierarchy/memory/search', '/api/hierarchy/memory/search')

  // ── Workspace execution (ECMS shape; replaces the legacy mocks below) ──
  get('/api/projects/:id/workspace', (req) => `/api/projects/${id(req)}/workspace`)
  post('/api/projects/:id/workspace/chat', (req) => `/api/projects/${id(req)}/workspace/chat`)
  get('/api/projects/:id/documents/:docId', (req) => `/api/projects/${id(req)}/documents/${req.params.docId}`)
}

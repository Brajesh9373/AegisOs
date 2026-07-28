import type { KnowledgeGraphEdge, KnowledgeGraphNode } from './graphTypes';

export interface KnowledgeGraphSnapshotManifest {
  state: 'missing' | 'building' | 'ready' | 'failed';
  stale: boolean;
  error: string | null;
  snapshot: null | {
    version: string;
    schema_version: number;
    point_count: number;
    link_count: number;
    points_bytes: number;
    links_bytes: number;
    points_checksum: string;
    links_checksum: string;
    points_url: string;
    links_url: string;
    generated_at: string | null;
    source_watermark: string | null;
    capacity: {
      supported: boolean;
      max_nodes: number;
      max_links: number;
    };
  };
}

export interface DecodedKnowledgeGraphSnapshot {
  manifest: KnowledgeGraphSnapshotManifest;
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchBuffer(url: string, signal: AbortSignal): Promise<ArrayBuffer> {
  const isSameOrigin = new URL(url, window.location.origin).origin === window.location.origin;
  const isSignedArtifact = new URL(url, window.location.origin).searchParams.has('X-Amz-Signature');
  const response = await fetch(url, {
    headers: isSameOrigin && !isSignedArtifact ? authHeaders() : {},
    signal,
  });
  if (!response.ok) throw new Error(`Snapshot download failed (${response.status})`);
  return response.arrayBuffer();
}

export async function sha256Hex(buffer: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
}

export async function verifySnapshotBuffer(
  buffer: ArrayBuffer,
  expectedBytes: number,
  expectedChecksum: string,
  artifact: 'points' | 'links',
): Promise<void> {
  if (buffer.byteLength !== expectedBytes) {
    throw new Error(
      `Snapshot ${artifact} size mismatch (expected ${expectedBytes}, received ${buffer.byteLength})`,
    );
  }
  const actualChecksum = await sha256Hex(buffer);
  if (actualChecksum.toLowerCase() !== expectedChecksum.toLowerCase()) {
    throw new Error(`Snapshot ${artifact} checksum mismatch`);
  }
}

function decodeInWorker(
  pointsBuffer: ArrayBuffer,
  linksBuffer: ArrayBuffer,
  signal: AbortSignal,
): Promise<{ nodes: KnowledgeGraphNode[]; edges: KnowledgeGraphEdge[] }> {
  return new Promise((resolve, reject) => {
    const worker = new Worker(
      new URL('./snapshotDecoder.worker.ts', import.meta.url),
      { type: 'module' },
    );
    const abort = () => {
      worker.terminate();
      reject(new DOMException('Snapshot load aborted', 'AbortError'));
    };
    signal.addEventListener('abort', abort, { once: true });
    worker.onerror = () => {
      signal.removeEventListener('abort', abort);
      worker.terminate();
      reject(new Error('Snapshot decoder worker failed'));
    };
    worker.onmessage = (
      event: MessageEvent<{
        nodes?: KnowledgeGraphNode[];
        edges?: KnowledgeGraphEdge[];
        error?: string;
      }>,
    ) => {
      signal.removeEventListener('abort', abort);
      worker.terminate();
      if (event.data.error || !event.data.nodes || !event.data.edges) {
        reject(new Error(event.data.error || 'Snapshot decoder returned invalid data'));
        return;
      }
      resolve({ nodes: event.data.nodes, edges: event.data.edges });
    };
    worker.postMessage(
      { pointsBuffer, linksBuffer },
      [pointsBuffer, linksBuffer],
    );
  });
}

export async function loadKnowledgeGraphSnapshot(
  signal: AbortSignal,
): Promise<DecodedKnowledgeGraphSnapshot> {
  const manifestResponse = await fetch('/api/knowledge-graph/v2/manifest', {
    headers: authHeaders(),
    cache: 'no-store',
    signal,
  });
  if (!manifestResponse.ok) {
    throw new Error(`Snapshot manifest failed (${manifestResponse.status})`);
  }
  const manifest = await manifestResponse.json() as KnowledgeGraphSnapshotManifest;
  if (!manifest.snapshot) {
    throw new Error(
      manifest.state === 'building'
        ? 'The first organization graph snapshot is still building.'
        : manifest.error || 'No organization graph snapshot is available yet.',
    );
  }
  if (!manifest.snapshot.capacity.supported) {
    throw new Error(
      `This graph exceeds the qualified interactive capacity `
      + `(${manifest.snapshot.capacity.max_nodes.toLocaleString()} nodes / `
      + `${manifest.snapshot.capacity.max_links.toLocaleString()} edges).`,
    );
  }

  const [pointsBuffer, linksBuffer] = await Promise.all([
    fetchBuffer(manifest.snapshot.points_url, signal),
    fetchBuffer(manifest.snapshot.links_url, signal),
  ]);
  if (signal.aborted) throw new DOMException('Snapshot load aborted', 'AbortError');

  await Promise.all([
    verifySnapshotBuffer(
      pointsBuffer,
      manifest.snapshot.points_bytes,
      manifest.snapshot.points_checksum,
      'points',
    ),
    verifySnapshotBuffer(
      linksBuffer,
      manifest.snapshot.links_bytes,
      manifest.snapshot.links_checksum,
      'links',
    ),
  ]);
  if (signal.aborted) throw new DOMException('Snapshot load aborted', 'AbortError');

  const { nodes, edges } = await decodeInWorker(pointsBuffer, linksBuffer, signal);
  return { manifest, nodes, edges };
}

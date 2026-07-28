/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { Suspense, useEffect, useState, useMemo } from 'react';
import { Typography, Tag, Spin, Empty, Input, Button, Space, Tooltip, Progress, Drawer, List, Alert } from 'antd';
import {
  PauseOutlined,
  CaretRightOutlined,
  SearchOutlined,
  NodeIndexOutlined,
  ApartmentOutlined,
  BranchesOutlined,
  CloseOutlined,
  FullscreenOutlined,
} from '@ant-design/icons';
import { D3Graph } from './D3Graph';
import { GraphBenchmarkBadge } from './knowledgeGraph/GraphBenchmarkBadge';
import {
  createSyntheticGraph,
  parseBenchmarkDatasetSize,
} from './knowledgeGraph/syntheticGraph';

const LazyCosmosGraph = React.lazy(async () => {
  const module = await import('./knowledgeGraph/CosmosGraph');
  return { default: module.CosmosGraph };
});

const { Text } = Typography;

const CATEGORY_COLORS: Record<string, string> = {
  backend: '#2563EB',
  frontend: '#7C3AED',
  security: '#DC2626',
  documentation: '#16A34A',
  configuration: '#F59E0B',
  testing: '#EC4899',
  database: '#0891B2',
  'ci/cd': '#EA580C',
  infrastructure: '#6366F1',
  dependencies: '#8B5CF6',
  code: '#3B82F6',
  data: '#14B8A6',
  other: '#64748B',
};

function categorizeNode(node: any): string {
  const id: string = (node.id || '').toLowerCase();
  const label: string = (node.label || '').toLowerCase();
  const rawType: string = (node.group || node.type || '').toLowerCase();
  const path = `${id} ${label}`;

  if (rawType === 'file' || rawType === 'document' || rawType === 'heading') {
    if (/(\.test\.|\.spec\.|__tests__|tests?\/|spec\/|jest\.config|vitest\.config|pytest|\.test$)/.test(path)) return 'testing';
    if (/(\.md$|\.rst$|\.txt$|docs?\/|readme|changelog|license|contributing|\.adoc$)/.test(path)) return 'documentation';
    if (/(\.ya?ml$|\.yml$|\.json$|\.toml$|\.ini$|\.env|\.cfg$|\.conf$|config\/|\.config\.|tsconfig|pyproject|\.prettierrc|\.eslintrc|\.editorconfig)/.test(path)) return 'configuration';
    if (/(dockerfile|docker-compose|\.dockerignore|\.github\/|pipeline\/|jenkinsfile|\.gitlab-ci|\.circleci|\.husky\/|pre-commit)/.test(path)) return 'ci/cd';
    if (/(terraform|\.tf$|\.tfvars|k8s|kubernetes|helm\/|chart\.yaml|values\.yaml|\.k8s\.|deploy\/|infra\/)/.test(path)) return 'infrastructure';
    if (/(package\.json|package-lock|yarn\.lock|pnpm-lock|requirements\.txt|poetry\.lock|cargo\.lock|go\.sum|gemfile\.lock|composer\.lock|\.npmrc|\.nvmrc|pyproject\.toml)/.test(path)) return 'dependencies';
    if (/(auth|security|crypto|jwt|oauth|session|token|permission|role|access.control|cors|csrf|xss|sanitiz|encrypt|decrypt|hash\.|bcrypt)/.test(path)) return 'security';
    if (/(migration|schema|\.sql$|alembic|prisma|sequelize|typeorm|drizzle|knex|flyway|liquibase|models\/|db\/|\.database\.)/.test(path)) return 'database';
    if (/(frontend\/|client\/|ui\/|components?\/|pages?\/|views?\/|\.tsx$|\.jsx$|\.vue$|\.svelte$|styles?\/|\.css$|\.scss$|\.less$|tailwind|styled|emotion|app\/|layouts?\/)/.test(path)) return 'frontend';
    if (/(backend\/|server\/|api\/|controllers?\/|services?\/|routes?\/|middleware\/|handlers?\/|\.py$|\.go$|\.rs$|\.java$|fastapi|express|django|flask|spring)/.test(path)) return 'backend';
  }

  if (['function', 'class', 'method', 'module', 'repository'].includes(rawType)) return 'code';
  if (['table', 'column'].includes(rawType)) return 'data';
  if (['api'].includes(rawType)) return 'backend';
  if (['import'].includes(rawType)) return 'dependencies';
  if (['concept'].includes(rawType)) return 'documentation';
  if (['workspace', 'connection'].includes(rawType)) return 'infrastructure';
  if (['episode', 'person', 'commit', 'unknown'].includes(rawType)) return 'other';

  return 'other';
}

function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category] || '#64748B';
}

function normalizeRepoUrl(value: string): string {
  return (value || '').toLowerCase().replace(/\.git$/, '').replace(/\/$/, '');
}

function repoNameFromUrl(value: string): string {
  const parts = normalizeRepoUrl(value).split('/').filter(Boolean);
  return parts[parts.length - 1] || '';
}

function reportGraphClientMetric(
  renderer: 'cosmos' | 'd3',
  event: 'ready' | 'load_failed' | 'webgl_fallback' | 'unmounted',
  durationMs?: number,
): void {
  const token = localStorage.getItem('auth_token');
  if (!token) return;
  void fetch('/api/knowledge-graph/v2/client-metrics', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      renderer,
      event,
      duration_ms: durationMs === undefined ? null : Math.round(durationMs),
    }),
    keepalive: true,
  }).catch(() => undefined);
}

interface KnowledgeGraphProps {
  height?: number;
  refreshKey?: number;
}

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ height = 700, refreshKey = 0 }) => {
  const proofConfig = useMemo(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    return {
      enabled: isLocalHost && searchParams.get('knowledgeRenderer') === 'cosmos',
      benchmark: isLocalHost && (
        searchParams.get('knowledgeBenchmark') === '1'
        || searchParams.get('knowledgeRenderer') === 'cosmos'
      ),
      datasetSize: parseBenchmarkDatasetSize(searchParams.get('knowledgeDataset')),
    };
  }, []);
  const [rawNodes, setRawNodes] = useState<any[]>([]);
  const [rawEdges, setRawEdges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const [paused, setPaused] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [fitRequestKey, setFitRequestKey] = useState(0);
  const [loadStartedAt, setLoadStartedAt] = useState(() => performance.now());
  const [snapshotNotice, setSnapshotNotice] = useState<string | null>(null);
  const [graphError, setGraphError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [selectedMetadata, setSelectedMetadata] = useState<Record<string, any> | null>(null);
  const [configuredRenderer, setConfiguredRenderer] = useState<'d3' | 'cosmos' | null>(
    proofConfig.enabled ? 'cosmos' : null,
  );
  const cosmosEnabled = proofConfig.enabled || configuredRenderer === 'cosmos';

  useEffect(() => {
    if (proofConfig.enabled) return;
    const controller = new AbortController();
    const token = localStorage.getItem('auth_token');
    void fetch('/api/knowledge-graph/v2/config', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: controller.signal,
    })
      .then((response) => response.ok ? response.json() : { renderer: 'd3' })
      .then((config: { renderer?: string }) => {
        const supportsWebgl2 = Boolean(document.createElement('canvas').getContext('webgl2'));
        if (config.renderer === 'cosmos' && !supportsWebgl2) {
          setSnapshotNotice('WebGL2 is unavailable; using the compatibility renderer.');
          reportGraphClientMetric('cosmos', 'webgl_fallback');
          setConfiguredRenderer('d3');
          return;
        }
        setConfiguredRenderer(config.renderer === 'cosmos' ? 'cosmos' : 'd3');
      })
      .catch((error) => {
        if (!(error instanceof DOMException && error.name === 'AbortError')) {
          setConfiguredRenderer('d3');
        }
      });
    return () => controller.abort();
  }, [proofConfig.enabled]);

  useEffect(() => {
    if (configuredRenderer === null) return;
    const controller = new AbortController();
    const fetchGraph = async () => {
      const startedAt = performance.now();
      setLoadStartedAt(startedAt);
      setGraphError(null);
      try {
        if (proofConfig.enabled && proofConfig.datasetSize) {
          const fixture = createSyntheticGraph(proofConfig.datasetSize);
          setRawNodes(fixture.nodes);
          setRawEdges(fixture.edges);
          return;
        }
        if (cosmosEnabled) {
          const { loadKnowledgeGraphSnapshot } = await import(
            './knowledgeGraph/snapshotClient'
          );
          const decoded = await loadKnowledgeGraphSnapshot(controller.signal);
          setRawNodes(decoded.nodes);
          setRawEdges(decoded.edges);
          setSnapshotNotice(
            decoded.manifest.stale
              ? `Showing last ready snapshot while a newer build is ${decoded.manifest.state}.`
              : null,
          );
          return;
        }
        const token = localStorage.getItem('auth_token');
        const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
        const [graphResult, connectionsResult] = await Promise.allSettled([
          fetch('/legacy-graph/data', { headers }),
          fetch('/api/connections', { headers }),
        ]);
        let connections: any[] = [];
        const connectionsResp = connectionsResult.status === 'fulfilled' ? connectionsResult.value : null;
        if (connectionsResp?.ok) connections = await connectionsResp.json();
        const sourceConnections = connections.filter((connection) => connection.repo_url);
        const connectionScopes = sourceConnections.map((connection) => ({
          number: connection.number,
          sourceGroup: `connection:${connection.number}`,
          repoUrl: normalizeRepoUrl(connection.repo_url || ''),
          repoName: repoNameFromUrl(connection.repo_url || ''),
          resourceId: normalizeRepoUrl(connection.config?.resource_id || ''),
        }));
        const connectionNodes = sourceConnections.flatMap((connection) => {
          const provider = connection.provider || 'git';
          const repoUrl = connection.repo_url || '';
          const repoName = repoUrl.split('/').filter(Boolean).slice(-2).join('/') || repoUrl;
          return [
            {
              id: `connection:${connection.number}`,
              label: `${String(provider).toUpperCase()} #${connection.number}`,
              group: 'connection',
              source_group: `connection:${connection.number}`,
              node_confidence: 1,
            },
            {
              id: `connection:${connection.number}:repo`,
              label: repoName,
              group: 'repository',
              source_group: `connection:${connection.number}`,
              node_confidence: 1,
            },
          ];
        });
        const connectionEdges = sourceConnections.map((connection) => ({
          id: `connection-edge:${connection.number}`,
          source: `connection:${connection.number}`,
          target: `connection:${connection.number}:repo`,
          label: 'indexes',
        }));
        let graphNodes: any[] = [];
        let graphEdges: any[] = [];
        const graphResp = graphResult.status === 'fulfilled' ? graphResult.value : null;
        if (graphResp?.ok) {
          const data = await graphResp.json();
          const edges = (data.edges || []).map((e: any) => ({
            id: e.id || `${e.from_}-${e.to}`,
            source: e.from_ || e.source || '',
            target: e.to || e.target || '',
            label: e.label || e.type || 'related',
          }));
          graphEdges = edges;
          const adjacency = new Map<string, Set<string>>();
          edges.forEach((e: any) => {
            if (!adjacency.has(e.source)) adjacency.set(e.source, new Set());
            if (!adjacency.has(e.target)) adjacency.set(e.target, new Set());
            adjacency.get(e.source)!.add(e.target);
            adjacency.get(e.target)!.add(e.source);
          });
          const connNum = connections.length > 0 ? connections[0].number : 1;
          const resolveSourceGroup = (node: any): string | null => {
            if (node.source_group && /^connection:\d+$/.test(node.source_group)) return node.source_group;
            const sourceUrl = normalizeRepoUrl(node.source_url || '');
            const matchedByUrl = connectionScopes.find((scope) =>
              sourceUrl && (sourceUrl === scope.repoUrl || sourceUrl === scope.resourceId)
            );
            if (matchedByUrl) return matchedByUrl.sourceGroup;
            const haystack = `${node.id || ''} ${node.source_id || ''} ${node.label || ''}`.toLowerCase();
            const matchedByName = connectionScopes.find((scope) => scope.repoName && haystack.includes(scope.repoName));
            if (matchedByName) return matchedByName.sourceGroup;
            const nodeId = String(node.id || '');
            const parts = nodeId.split(':');
            if (parts.length >= 4 && parts[0] === 'git' && !isNaN(Number(parts[1]))) return `connection:${parts[1]}`;
            if (parts[0] === 'git') {
              if (parts[1] === 'commit') {
                const neighbors = adjacency.get(nodeId);
                if (neighbors) for (const n of neighbors) if (n.split(':')[1] === 'file') return `connection:${connNum}`;
              }
              return `connection:${connNum}`;
            }
            return null;
          };
          const nodes = (data.nodes || []).map((n: any) => ({
            id: n.id, label: n.label || n.id, group: n.group || n.type || 'unknown',
            source_id: n.source_id,
            source_url: n.source_url,
            source_group: resolveSourceGroup(n),
            node_confidence: n.node_confidence || 0.5,
            domain: n.domain,
          }));
          graphNodes = nodes;
        }
        const sourceEdges = graphNodes
          .filter((node) => node.source_group && /^connection:\d+$/.test(node.source_group))
          .map((node) => ({
            id: `connection-source:${node.source_group}:${node.id}`,
            source: node.source_group,
            target: node.id,
            label: 'contains',
          }));
        const mergedNodes = Array.from(
          new Map([...connectionNodes, ...graphNodes].map((node) => [node.id, node])).values(),
        );
        setRawNodes(mergedNodes);
        setRawEdges([...connectionEdges, ...sourceEdges, ...graphEdges]);
      } catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        console.error('Knowledge graph load failed', error);
        reportGraphClientMetric(
          cosmosEnabled ? 'cosmos' : 'd3',
          'load_failed',
          performance.now() - startedAt,
        );
        setGraphError(error instanceof Error ? error.message : 'Knowledge graph load failed.');
        setRawNodes([]);
        setRawEdges([]);
      }
      finally { setLoading(false); }
    };
    setLoading(true);
    fetchGraph();
    const handleGraphUpdated = () => fetchGraph();
    window.addEventListener('knowledge-graph-updated', handleGraphUpdated);
    return () => {
      controller.abort();
      window.removeEventListener('knowledge-graph-updated', handleGraphUpdated);
    };
  }, [
    configuredRenderer,
    cosmosEnabled,
    proofConfig.datasetSize,
    proofConfig.enabled,
    refreshKey,
    loadAttempt,
  ]);

  useEffect(() => {
    if (!cosmosEnabled) return;
    const handleReady = (event: Event) => {
      const detail = (event as CustomEvent<{ interactiveMs?: number }>).detail;
      reportGraphClientMetric('cosmos', 'ready', detail?.interactiveMs);
    };
    window.addEventListener('ecms:knowledge-graph-ready', handleReady);
    return () => {
      window.removeEventListener('ecms:knowledge-graph-ready', handleReady);
      reportGraphClientMetric('cosmos', 'unmounted');
    };
  }, [cosmosEnabled]);

  useEffect(() => {
    setSelectedMetadata(null);
    if (!cosmosEnabled || !selectedNode?.id) return;
    const controller = new AbortController();
    const token = localStorage.getItem('auth_token');
    void fetch(`/api/knowledge-graph/v2/nodes/${encodeURIComponent(selectedNode.id)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: controller.signal,
    })
      .then((response) => response.ok ? response.json() : null)
      .then((result) => setSelectedMetadata(result?.node || null))
      .catch(() => undefined);
    return () => controller.abort();
  }, [cosmosEnabled, selectedNode?.id]);

  const selectedEdges = useMemo(() => {
    if (!selectedNode) return [];
    return rawEdges.filter((e) =>
      (typeof e.source === 'string' ? e.source : (e.source as any)?.id) === selectedNode.id ||
      (typeof e.target === 'string' ? e.target : (e.target as any)?.id) === selectedNode.id,
    );
  }, [selectedNode, rawEdges]);

  const categorizedNodes = useMemo(() => {
    return rawNodes.map((n) => ({ ...n, category: n.domain || n.category || categorizeNode(n) }));
  }, [rawNodes]);

  const filteredByCategory = useMemo(() => {
    if (!selectedCategory) return categorizedNodes;
    return categorizedNodes.filter((n) => n.category === selectedCategory);
  }, [categorizedNodes, selectedCategory]);

  const typeStats = useMemo(() => {
    const counts: Record<string, number> = {};
    categorizedNodes.forEach((n) => { const c = n.category || 'other'; counts[c] = (counts[c] || 0) + 1; });
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [categorizedNodes]);

  const categoryNodes = useMemo(() => {
    if (!selectedCategory) return [];
    return categorizedNodes.filter((n) => n.category === selectedCategory).slice(0, 100);
  }, [categorizedNodes, selectedCategory]);

  if (loading) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8fafc' }}>
        <Spin tip="Loading knowledge graph..." />
      </div>
    );
  }

  if (rawNodes.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8fafc' }}>
        {graphError ? (
          <Alert
            type="warning"
            showIcon
            message="Knowledge graph unavailable"
            description={graphError}
            action={<Button onClick={() => setLoadAttempt((value) => value + 1)}>Retry</Button>}
          />
        ) : (
          <Empty description="No knowledge graph data yet" />
        )}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', height, background: '#fff', borderRadius: 8, overflow: 'hidden', border: '1px solid #e2e8f0' }}>

      {/* ─── Left Panel: Node Types ─── */}
      <div style={{ width: 220, borderRight: '1px solid #e2e8f0', background: '#fff', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid #e2e8f0' }}>
          <Text strong style={{ fontSize: 12, color: '#334155', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            <ApartmentOutlined style={{ marginRight: 8, fontSize: 12 }} />Node Types
          </Text>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
          {selectedCategory && (
            <div
              style={{ padding: '7px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}
              onClick={() => setSelectedCategory(null)}
            >
              <CloseOutlined style={{ fontSize: 10, color: '#94a3b8' }} />
              <Text style={{ fontSize: 11, color: '#2563eb' }}>Clear filter</Text>
            </div>
          )}
          {typeStats.map(([type, count]) => (
            <div
              key={type}
              style={{
                display: 'flex', alignItems: 'center', padding: '7px 16px', gap: 10,
                cursor: 'pointer', borderRadius: 4, margin: '0 6px',
                background: selectedCategory === type ? '#eff6ff' : 'transparent',
                border: selectedCategory === type ? '1px solid #bfdbfe' : '1px solid transparent',
              }}
              onClick={() => setSelectedCategory(selectedCategory === type ? null : type)}
            >
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: getCategoryColor(type), flexShrink: 0 }} />
              <Text style={{ fontSize: 12, flex: 1, color: '#334155', fontWeight: selectedCategory === type ? 600 : 400 }}>{type}</Text>
              <Text style={{ fontSize: 11, color: '#94a3b8', fontVariantNumeric: 'tabular-nums' }}>{count.toLocaleString()}</Text>
            </div>
          ))}
        </div>
        <div style={{ padding: '12px 16px', borderTop: '1px solid #e2e8f0' }}>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Text style={{ fontSize: 11, color: '#94a3b8' }}>
              <BranchesOutlined style={{ marginRight: 4 }} />{rawNodes.length.toLocaleString()} nodes
            </Text>
            <Text style={{ fontSize: 11, color: '#94a3b8' }}>
              {rawEdges.length.toLocaleString()} edges
            </Text>
          </Space>
        </div>
      </div>

      {/* ─── Center: D3 Graph ─── */}
      <div
        style={{
          flex: 1,
          position: 'relative',
          overflow: 'hidden',
          backgroundColor: '#f8fafc',
          backgroundImage: 'radial-gradient(#cbd5e1 0.7px, transparent 0.7px)',
          backgroundSize: '18px 18px',
        }}
      >
        {/* Toolbar */}
        <div style={{ position: 'absolute', top: 12, left: 12, right: 12, display: 'flex', alignItems: 'center', gap: 8, zIndex: 10 }}>
          <Input
            placeholder="Search nodes..."
            prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            allowClear
            style={{ width: 280, borderRadius: 8 }}
          />
          <Tooltip title={paused ? 'Resume simulation' : 'Pause simulation'}>
            <Button
              icon={paused ? <CaretRightOutlined /> : <PauseOutlined />}
              onClick={() => setPaused(!paused)}
              style={{ borderRadius: 8 }}
            />
          </Tooltip>
          {cosmosEnabled && (
            <Tooltip title="Fit the complete graph">
              <Button
                aria-label="Fit complete graph"
                icon={<FullscreenOutlined />}
                onClick={() => setFitRequestKey((value) => value + 1)}
                style={{ borderRadius: 8 }}
              />
            </Tooltip>
          )}
          {snapshotNotice && (
            <Tag color="gold" style={{ marginLeft: 8, fontSize: 11 }}>
              {snapshotNotice}
            </Tag>
          )}
          {searchFilter && (
            <Text style={{ fontSize: 11, color: '#94a3b8', marginLeft: 8 }}>
              Filtering: "{searchFilter}"
            </Text>
          )}
          {selectedCategory && (
            <Tag color={getCategoryColor(selectedCategory)} style={{ marginLeft: 8, fontSize: 11 }}>
              {selectedCategory} ({filteredByCategory.length} nodes)
            </Tag>
          )}
        </div>

        {/* Bottom hints */}
        <div style={{
          position: 'absolute', bottom: 12, left: 12, right: 12,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(8px)',
          padding: '8px 16px', borderRadius: 8, border: '1px solid #e2e8f0', zIndex: 10,
        }}>
          <Text style={{ fontSize: 11, color: '#64748b' }}>
            Force simulation {paused ? 'paused' : 'active'}
          </Text>
          <Space size={16}>
            <Text style={{ fontSize: 11, color: '#94a3b8' }}>Zoom: scroll</Text>
            <Text style={{ fontSize: 11, color: '#94a3b8' }}>Pan: drag background</Text>
            <Text style={{ fontSize: 11, color: '#94a3b8' }}>Drag: move nodes</Text>
          </Space>
        </div>

        {cosmosEnabled ? (
          <>
            {proofConfig.benchmark && <GraphBenchmarkBadge />}
            <Suspense
              fallback={
                <div style={{ height: '100%', display: 'grid', placeItems: 'center' }}>
                  <Spin tip="Loading MIT-licensed GPU renderer…" />
                </div>
              }
            >
              <LazyCosmosGraph
                nodes={categorizedNodes}
                edges={rawEdges}
                searchFilter={searchFilter}
                highlightedCategory={selectedCategory}
                paused={paused}
                fitRequestKey={fitRequestKey}
                loadStartedAt={loadStartedAt}
                onSelectNode={setSelectedNode}
              />
            </Suspense>
          </>
        ) : (
          <>
            {proofConfig.benchmark && <GraphBenchmarkBadge />}
            <D3Graph
              nodes={filteredByCategory}
              edges={rawEdges}
              searchFilter={searchFilter}
              paused={paused}
              loadStartedAt={loadStartedAt}
              benchmark={proofConfig.benchmark}
              onSelectNode={setSelectedNode}
            />
          </>
        )}
      </div>

      {/* ─── Right Panel: Node Inspector ─── */}
      <div style={{ width: 280, borderLeft: '1px solid #e2e8f0', background: '#fff', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid #e2e8f0' }}>
          <Text strong style={{ fontSize: 12, color: '#334155', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            <NodeIndexOutlined style={{ marginRight: 8, fontSize: 12 }} />Node Inspector
          </Text>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
          {!selectedNode ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
              <NodeIndexOutlined style={{ fontSize: 36, color: '#cbd5e1', marginBottom: 16 }} />
              <Text style={{ display: 'block', fontSize: 12, color: '#94a3b8' }}>Click a node to inspect</Text>
              <Text style={{ display: 'block', fontSize: 11, color: '#cbd5e1', marginTop: 4 }}>Details and connections will appear here</Text>
            </div>
          ) : (
            <div>
              {/* Node name */}
              <div style={{ marginBottom: 20 }}>
                <Text strong style={{ fontSize: 15, color: '#0f172a', display: 'block', marginBottom: 12, lineHeight: 1.3 }}>
                  {selectedNode.label}
                </Text>

                {/* Type */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                  <Text type="secondary" style={{ fontSize: 11, width: 70 }}>Type</Text>
                  <Tag color={getCategoryColor(selectedNode.category || categorizeNode(selectedNode))} style={{ fontSize: 11, margin: 0 }}>
                    {selectedNode.category || categorizeNode(selectedNode)}
                  </Tag>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                  <Text type="secondary" style={{ fontSize: 11, width: 70 }}>Raw Type</Text>
                  <Tag style={{ fontSize: 11, margin: 0 }}>{selectedNode.group}</Tag>
                </div>

                {/* Source */}
                {selectedNode.source_group && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <Text type="secondary" style={{ fontSize: 11, width: 70 }}>Source</Text>
                    <Text style={{ fontSize: 11 }}>{selectedNode.source_group}</Text>
                  </div>
                )}

                {/* Confidence */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                  <Text type="secondary" style={{ fontSize: 11, width: 70 }}>Confidence</Text>
                  <Progress
                    percent={Math.round(selectedNode.node_confidence * 100)}
                    size="small"
                    strokeColor={selectedNode.node_confidence > 0.7 ? '#52c41a' : selectedNode.node_confidence > 0.4 ? '#faad14' : '#ff4d4f'}
                    style={{ flex: 1, marginBottom: 0 }}
                  />
                </div>

                {/* ID */}
                <div style={{ marginTop: 12, padding: '8px 10px', background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0' }}>
                  <Text style={{ fontSize: 10, color: '#64748b', wordBreak: 'break-all', fontFamily: 'monospace' }}>
                    {selectedNode.id}
                  </Text>
                </div>
                {selectedMetadata && (
                  <div style={{ marginTop: 12 }}>
                    {Object.entries(selectedMetadata)
                      .filter(([key, value]) => (
                        !['id', 'label', 'group'].includes(key)
                        && value !== null
                        && value !== ''
                        && typeof value !== 'object'
                      ))
                      .slice(0, 6)
                      .map(([key, value]) => (
                        <div key={key} style={{ marginBottom: 8 }}>
                          <Text type="secondary" style={{ display: 'block', fontSize: 10 }}>
                            {key.replace(/_/g, ' ')}
                          </Text>
                          <Text style={{ display: 'block', fontSize: 11, wordBreak: 'break-word' }}>
                            {String(value)}
                          </Text>
                        </div>
                      ))}
                  </div>
                )}
              </div>

              {/* Divider */}
              <div style={{ height: 1, background: '#e2e8f0', margin: '16px 0' }} />

              {/* Relationships */}
              <div>
                <Text strong style={{ fontSize: 12, color: '#334155', display: 'block', marginBottom: 12 }}>
                  <BranchesOutlined style={{ marginRight: 6 }} />
                  Connections ({selectedEdges.length})
                </Text>
                {selectedEdges.length === 0 ? (
                  <Text style={{ fontSize: 11, color: '#94a3b8' }}>No connections</Text>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {selectedEdges.slice(0, 25).map((e: any, idx: number) => {
                      const srcId = typeof e.source === 'string' ? e.source : e.source?.id;
                      const tgtId = typeof e.target === 'string' ? e.target : e.target?.id;
                      const otherId = srcId === selectedNode.id ? tgtId : srcId;
                      const otherNode = rawNodes.find((n) => n.id === otherId);
                      const otherCategory = otherNode ? (otherNode.category || categorizeNode(otherNode)) : 'other';
                      return (
                        <div
                          key={idx}
                          style={{
                            padding: '6px 10px',
                            background: '#f8fafc',
                            borderRadius: 6,
                            border: '1px solid #e2e8f0',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                          }}
                        >
                          <div style={{
                            width: 6, height: 6, borderRadius: '50%',
                            background: getCategoryColor(otherCategory),
                            flexShrink: 0,
                          }} />
                          <Tag style={{ fontSize: 9, margin: 0, padding: '0 4px' }}>
                            {e.label}
                          </Tag>
                          <Text style={{ fontSize: 11, color: '#334155', flex: 1 }} ellipsis>
                            {otherNode?.label || otherId}
                          </Text>
                        </div>
                      );
                    })}
                    {selectedEdges.length > 25 && (
                      <Text style={{ fontSize: 10, color: '#94a3b8', textAlign: 'center', padding: '4px 0' }}>
                        +{selectedEdges.length - 25} more connections
                      </Text>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <Drawer
        title={<Space><div style={{ width: 10, height: 10, borderRadius: '50%', background: selectedCategory ? getCategoryColor(selectedCategory) : '#888' }} /><span>{selectedCategory} Files</span><Tag>{categoryNodes.length}</Tag></Space>}
        open={!!selectedCategory && categoryNodes.length > 0}
        onClose={() => setSelectedCategory(null)}
        width={420}
        placement="right"
      >
        <List
          dataSource={categoryNodes}
          renderItem={(node: any) => (
            <List.Item style={{ padding: '8px 0', cursor: 'pointer' }} onClick={() => { setSelectedNode(node); }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%' }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: getCategoryColor(node.category), flexShrink: 0 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <Text style={{ fontSize: 12, display: 'block' }} ellipsis>{node.label}</Text>
                  <Text type="secondary" style={{ fontSize: 10 }}>{node.group}</Text>
                </div>
                <Progress percent={Math.round(node.node_confidence * 100)} size="small" style={{ width: 60, marginBottom: 0 }} />
              </div>
            </List.Item>
          )}
        />
      </Drawer>
    </div>
  );
};

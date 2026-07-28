import React, { useEffect, useMemo, useRef } from 'react';
import { Graph } from '@cosmos.gl/graph';
import type { KnowledgeGraphEdge, KnowledgeGraphNode } from './graphTypes';
import { edgeEndpointId } from './graphTypes';

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

interface CosmosGraphProps {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  searchFilter?: string;
  highlightedCategory?: string | null;
  onSelectNode?: (node: KnowledgeGraphNode | null) => void;
  paused?: boolean;
  fitRequestKey?: number;
  loadStartedAt: number;
}

function hexToRgba(hex: string, alpha = 1): [number, number, number, number] {
  const value = hex.replace('#', '');
  return [
    Number.parseInt(value.slice(0, 2), 16) / 255,
    Number.parseInt(value.slice(2, 4), 16) / 255,
    Number.parseInt(value.slice(4, 6), 16) / 255,
    alpha,
  ];
}

function seededPosition(index: number, count: number): [number, number] {
  const angle = index * 2.399963229728653;
  const radius = Math.sqrt((index + 1) / Math.max(count, 1)) * 1_600;
  return [Math.cos(angle) * radius, Math.sin(angle) * radius];
}

export const CosmosGraph: React.FC<CosmosGraphProps> = ({
  nodes,
  edges,
  searchFilter = '',
  highlightedCategory = null,
  onSelectNode,
  paused = false,
  fitRequestKey = 0,
  loadStartedAt,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  const selectedIndexRef = useRef<number | null>(null);

  const prepared = useMemo(() => {
    const idToIndex = new Map<string, number>();
    nodes.forEach((node, index) => idToIndex.set(node.id, index));

    const positions = new Float32Array(nodes.length * 2);
    const colors = new Float32Array(nodes.length * 4);
    const sizes = new Float32Array(nodes.length);
    const degree = new Uint32Array(nodes.length);
    const validEdges: KnowledgeGraphEdge[] = [];

    edges.forEach((edge) => {
      const source = idToIndex.get(edgeEndpointId(edge.source));
      const target = idToIndex.get(edgeEndpointId(edge.target));
      if (source === undefined || target === undefined) return;
      degree[source] += 1;
      degree[target] += 1;
      validEdges.push(edge);
    });

    const links = new Float32Array(validEdges.length * 2);
    const linkColors = new Float32Array(validEdges.length * 4);
    const linkWidths = new Float32Array(validEdges.length);
    validEdges.forEach((edge, index) => {
      links[index * 2] = idToIndex.get(edgeEndpointId(edge.source))!;
      links[index * 2 + 1] = idToIndex.get(edgeEndpointId(edge.target))!;
      const structural = edge.label === 'contains' || edge.label === 'indexes';
      linkColors.set(
        structural
          ? [0.12, 0.18, 0.29, 0.30]
          : [0.20, 0.27, 0.39, 0.16],
        index * 4,
      );
      linkWidths[index] = structural ? 0.62 : 0.38;
    });

    nodes.forEach((node, index) => {
      positions.set(
        node.x !== undefined && node.y !== undefined
          ? [node.x, node.y]
          : seededPosition(index, nodes.length),
        index * 2,
      );
      colors.set(hexToRgba(CATEGORY_COLORS[node.category || 'other'] || CATEGORY_COLORS.other), index * 4);
      const isRoot = node.id === 'knowledge-source:root' || node.group === 'connection';
      const isSourceHub = node.group === 'repository';
      if (isRoot) {
        sizes[index] = 18;
      } else if (isSourceHub) {
        sizes[index] = 13;
      } else {
        sizes[index] = Math.min(11, 3.1 + Math.sqrt(degree[index]) * 1.05);
      }
    });

    return { idToIndex, positions, colors, sizes, links, linkColors, linkWidths };
  }, [nodes, edges]);

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    const graph = new Graph(containerRef.current, {
      backgroundColor: '#f8fafc',
      enableDrag: true,
      enableSimulation: false,
      enableSimulationDuringZoom: false,
      fitViewOnInit: true,
      fitViewDelay: 350,
      fitViewDuration: 420,
      fitViewPadding: 0.12,
      linkBlending: true,
      linkGreyoutOpacity: 0.08,
      pointGreyoutOpacity: 0.18,
      pixelRatio: Math.min(window.devicePixelRatio || 1, 1.5),
      randomSeed: 'ecms-knowledge-graph-v2',
      showFPSMonitor: false,
      simulationGravity: 0.08,
      simulationCenter: 0.15,
      simulationRepulsion: 0.4,
      simulationLinkSpring: 0.8,
      simulationLinkDistance: 4,
      spaceSize: 4096,
      transitionDuration: 0,
      onPointClick: (index) => {
        selectedIndexRef.current = index;
        const neighboring = graph.getNeighboringPointIndices(index);
        const connectedLinks = graph.getConnectedLinkIndices([index, ...neighboring]);
        graph.setConfigPartial({
          highlightedPointIndices: [index, ...neighboring],
          highlightedLinkIndices: connectedLinks,
          outlinedPointIndices: [index],
        });
        onSelectNode?.(nodes[index] || null);
      },
      onBackgroundClick: () => {
        selectedIndexRef.current = null;
        graph.setConfigPartial({
          highlightedPointIndices: undefined,
          highlightedLinkIndices: undefined,
          outlinedPointIndices: undefined,
        });
        onSelectNode?.(null);
      },
    });
    graphRef.current = graph;
    let disposed = false;

    void graph.ready.then(() => {
      if (disposed) return;
      graph.setPointPositions(prepared.positions, true);
      graph.setPointColors(prepared.colors);
      graph.setPointSizes(prepared.sizes);
      graph.setLinks(prepared.links);
      graph.setLinkColors(prepared.linkColors);
      graph.setLinkWidths(prepared.linkWidths);
      graph.render(0, 0);
      window.dispatchEvent(
        new CustomEvent('ecms:knowledge-graph-ready', {
          detail: {
            renderer: 'cosmos',
            nodes: nodes.length,
            edges: prepared.links.length / 2,
            interactiveMs: Math.round(performance.now() - loadStartedAt),
          },
        }),
      );
    });

    const visibilityHandler = () => {
      if (document.hidden) graph.pause();
      else if (!paused) graph.unpause();
    };
    document.addEventListener('visibilitychange', visibilityHandler);

    return () => {
      disposed = true;
      document.removeEventListener('visibilitychange', visibilityHandler);
      graph.destroy();
      graphRef.current = null;
    };
  }, [nodes, prepared, loadStartedAt]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;
    if (paused) graph.pause();
    else {
      graph.setConfigPartial({ enableSimulation: true });
      graph.start(0.3);
    }
  }, [paused]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph || fitRequestKey === 0) return;
    graph.fitView(420, 0.12, !paused);
  }, [fitRequestKey, paused]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;
    const query = searchFilter.trim().toLowerCase();
    if (!query && !highlightedCategory) {
      if (selectedIndexRef.current === null) {
        graph.setConfigPartial({
          highlightedPointIndices: undefined,
          highlightedLinkIndices: undefined,
          outlinedPointIndices: undefined,
        });
      }
      return;
    }

    const matches: number[] = [];
    for (let index = 0; index < nodes.length; index += 1) {
      const node = nodes[index];
      const matchesSearch = !query
        || node.label.toLowerCase().includes(query)
        || node.group.toLowerCase().includes(query);
      const matchesCategory = !highlightedCategory || node.category === highlightedCategory;
      if (matchesSearch && matchesCategory) {
        matches.push(index);
      }
    }
    graph.setConfigPartial({
      highlightedPointIndices: matches,
      outlinedPointIndices: matches.slice(0, 1_000),
      highlightedLinkIndices: undefined,
    });
    if (matches.length > 0 && matches.length <= 1_000) {
      graph.fitViewByPointIndices(matches, 250, 0.25, !paused);
    }
  }, [highlightedCategory, nodes, paused, searchFilter]);

  return (
    <div
      ref={containerRef}
      data-testid="knowledge-graph-cosmos"
      style={{ width: '100%', height: '100%', minHeight: 600 }}
    />
  );
};

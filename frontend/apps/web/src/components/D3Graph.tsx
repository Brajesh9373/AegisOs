/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

// Color scale — mapped to knowledge categories
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

function getColor(node: any): string {
  const cat = node?.category || 'other';
  return CATEGORY_COLORS[cat] || '#64748B';
}

interface D3GraphNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  group: string;
  source_group: string | null;
  node_confidence: number;
}

interface D3GraphEdge extends d3.SimulationLinkDatum<D3GraphNode> {
  id: string;
  label: string;
}

interface D3GraphProps {
  nodes: D3GraphNode[];
  edges: D3GraphEdge[];
  searchFilter?: string;
  onSelectNode?: (node: D3GraphNode | null) => void;
  paused?: boolean;
  benchmark?: boolean;
  loadStartedAt?: number;
}

export const D3Graph: React.FC<D3GraphProps> = ({
  nodes: rawNodes,
  edges: rawEdges,
  searchFilter = '',
  onSelectNode,
  paused = false,
  benchmark = false,
  loadStartedAt = performance.now(),
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const simRef = useRef<d3.Simulation<D3GraphNode, D3GraphEdge> | null>(null);

  // Build graph
  useEffect(() => {
    if (!containerRef.current) return;
    if (rawNodes.length === 0) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Clear previous
    d3.select(container).selectAll('svg').remove();

    // Filter by search
    const filter = searchFilter.toLowerCase();
    const filteredNodes = filter
      ? rawNodes.filter(
          (n) =>
            n.label?.toLowerCase().includes(filter) ||
            n.group?.toLowerCase().includes(filter),
        )
      : rawNodes;

    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredEdges = rawEdges.filter(
      (e) =>
        nodeIds.has(typeof e.source === 'string' ? e.source : (e.source as any).id) &&
        nodeIds.has(typeof e.target === 'string' ? e.target : (e.target as any).id),
    );

    // Compute degree for sizing
    const degreeMap = new Map<string, number>();
    filteredEdges.forEach((e) => {
      const sid = typeof e.source === 'string' ? e.source : (e.source as any).id;
      const tid = typeof e.target === 'string' ? e.target : (e.target as any).id;
      degreeMap.set(sid, (degreeMap.get(sid) || 0) + 1);
      degreeMap.set(tid, (degreeMap.get(tid) || 0) + 1);
    });
    const maxDeg = Math.max(1, ...degreeMap.values());
    const radiusScale = d3.scaleLinear().domain([0, maxDeg]).range([6, 26]);

    // Create SVG
    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('style', 'max-width: 100%; height: 100%; background: transparent;');

    const g = svg.append('g');

    // Zoom
    let userAdjustedView = false;
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.01, 50])
      .on('zoom', (event) => {
        if (event.sourceEvent) userAdjustedView = true;
        g.attr('transform', event.transform);
      });
    svg.call(zoom);

    // Edges
    const linkGroup = g.append('g').attr('class', 'links');

    // Source boundary ellipses group (rendered behind nodes)
    const boundaryGroup = g.append('g').attr('class', 'boundaries');
    const link = linkGroup
      .selectAll('line')
      .data(filteredEdges)
      .join('line')
      .attr('stroke', '#64748b')
      .attr('stroke-width', (d) => (d.label === 'indexes' || d.label === 'contains' ? 1.1 : 0.8))
      .attr('stroke-opacity', (d) => (d.label === 'indexes' || d.label === 'contains' ? 0.42 : 0.3));

    // Nodes
    const nodeGroup = g.append('g').attr('class', 'nodes');
    const node = nodeGroup
      .selectAll('circle')
      .data(filteredNodes)
      .join('circle')
      .attr('r', (d) => radiusScale(degreeMap.get(d.id) || 0))
      .attr('fill', (d) => getColor(d))
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 1.6)
      .attr('cursor', 'pointer')
      .style('filter', 'drop-shadow(0 1px 1px rgba(15, 23, 42, 0.16))')
      .call(
        d3
          .drag<any, D3GraphNode>()
          .on('start', (event, d) => {
            if (!event.active) sim.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) sim.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      );

    // Labels for large nodes
    const labelGroup = g.append('g').attr('class', 'labels');
    const labels = labelGroup
      .selectAll('text')
      .data(filteredNodes.filter((d) => (degreeMap.get(d.id) || 0) > 3))
      .join('text')
      .text((d) => d.label?.substring(0, 20) || '')
      .attr('font-size', 9)
      .attr('font-weight', 500)
      .attr('fill', '#334155')
      .attr('stroke', '#f8fafc')
      .attr('stroke-width', 3)
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => radiusScale(degreeMap.get(d.id) || 0) + 12)
      .style('paint-order', 'stroke')
      .style('stroke-linejoin', 'round')
      .attr('pointer-events', 'none');

    let selectedNodeId: string | null = null;
    const baseLinkOpacity = (edge: D3GraphEdge) => (
      edge.label === 'indexes' || edge.label === 'contains' ? 0.42 : 0.3
    );
    const endpointId = (endpoint: D3GraphEdge['source']) => (
      typeof endpoint === 'object' ? endpoint.id : String(endpoint)
    );

    const resetFocus = () => {
      selectedNodeId = null;
      node
        .attr('opacity', 1)
        .attr('stroke', '#ffffff')
        .attr('stroke-width', 1.6);
      link
        .attr('stroke', '#64748b')
        .attr('stroke-opacity', baseLinkOpacity)
        .attr('stroke-width', (d) => (d.label === 'indexes' || d.label === 'contains' ? 1.1 : 0.8));
      labels.attr('opacity', 1);
    };

    const focusNode = (selected: D3GraphNode) => {
      selectedNodeId = selected.id;
      const connectedIds = new Set<string>([selected.id]);

      filteredEdges.forEach((edge) => {
        const sourceId = endpointId(edge.source);
        const targetId = endpointId(edge.target);
        if (sourceId === selected.id) connectedIds.add(targetId);
        if (targetId === selected.id) connectedIds.add(sourceId);
      });

      node
        .attr('opacity', (d) => (connectedIds.has(d.id) ? 1 : 0.16))
        .attr('stroke', (d) => (d.id === selected.id ? '#0f172a' : '#ffffff'))
        .attr('stroke-width', (d) => (d.id === selected.id ? 3 : 1.6));
      link
        .attr('stroke', (d) => {
          const sourceId = endpointId(d.source);
          const targetId = endpointId(d.target);
          return sourceId === selected.id || targetId === selected.id ? '#334155' : '#94a3b8';
        })
        .attr('stroke-opacity', (d) => {
          const sourceId = endpointId(d.source);
          const targetId = endpointId(d.target);
          return sourceId === selected.id || targetId === selected.id ? 0.72 : 0.035;
        })
        .attr('stroke-width', (d) => {
          const sourceId = endpointId(d.source);
          const targetId = endpointId(d.target);
          return sourceId === selected.id || targetId === selected.id ? 1.5 : 0.6;
        });
      labels.attr('opacity', (d) => (connectedIds.has(d.id) ? 1 : 0.08));
    };

    node.on('click', (event, d) => {
      event.stopPropagation();
      focusNode(d);
      onSelectNode?.(d);
    });

    // Source cluster force
    function sourceClusterForce(nodesList: D3GraphNode[]) {
      const groups = new Map<string, { x: number; y: number; count: number }>();
      return (alpha: number) => {
        groups.clear();
        nodesList.forEach((n) => {
          const sg = n.source_group;
          if (!sg) return;
          if (!groups.has(sg)) groups.set(sg, { x: 0, y: 0, count: 0 });
          const g2 = groups.get(sg)!;
          g2.x += n.x ?? 0;
          g2.y += n.y ?? 0;
          g2.count++;
        });
        groups.forEach((g2) => {
          g2.x /= g2.count;
          g2.y /= g2.count;
        });
        nodesList.forEach((n) => {
          const sg = n.source_group;
          if (!sg) return;
          const centroid = groups.get(sg);
          if (!centroid) return;
          n.vx = (n.vx ?? 0) + (centroid.x - (n.x ?? 0)) * 0.08 * alpha;
          n.vy = (n.vy ?? 0) + (centroid.y - (n.y ?? 0)) * 0.08 * alpha;
        });
      };
    }

    const sourceGroups = new Map<string, D3GraphNode[]>();
    filteredNodes.forEach((graphNode) => {
      let sourceGroup = graphNode.source_group;
      if (!sourceGroup) {
        const parts = graphNode.id.split(':');
        sourceGroup = parts.length >= 3 ? parts.slice(0, 3).join(':') : null;
      }
      if (!sourceGroup) return;
      const members = sourceGroups.get(sourceGroup) || [];
      members.push(graphNode);
      sourceGroups.set(sourceGroup, members);
    });

    // Force simulation
    const sim = d3
      .forceSimulation(filteredNodes)
      .force('link', d3.forceLink(filteredEdges).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide(30))
      .force('sourceCluster', sourceClusterForce(filteredNodes));

    simRef.current = sim;

    const fitEntireGraph = () => {
      if (userAdjustedView || filteredNodes.length === 0) return;

      let minX = Infinity;
      let maxX = -Infinity;
      let minY = Infinity;
      let maxY = -Infinity;
      filteredNodes.forEach((graphNode) => {
        const nodeRadius = radiusScale(degreeMap.get(graphNode.id) || 0);
        const x = graphNode.x || 0;
        const y = graphNode.y || 0;
        minX = Math.min(minX, x - nodeRadius);
        maxX = Math.max(maxX, x + nodeRadius);
        minY = Math.min(minY, y - nodeRadius);
        maxY = Math.max(maxY, y + nodeRadius);
      });

      const graphWidth = Math.max(1, maxX - minX);
      const graphHeight = Math.max(1, maxY - minY);
      const padding = 72;
      const scale = Math.min(
        0.9,
        Math.max(
          0.01,
          Math.min((width - padding * 2) / graphWidth, (height - padding * 2) / graphHeight),
        ),
      );
      const centerX = (minX + maxX) / 2;
      const centerY = (minY + maxY) / 2;
      const transform = d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(scale)
        .translate(-centerX, -centerY);
      svg.call(zoom.transform, transform);
    };

    // The simulation assigns initial positions synchronously, allowing an immediate
    // whole-graph overview before the layout settles.
    fitEntireGraph();
    if (benchmark) {
      requestAnimationFrame(() => {
        window.dispatchEvent(
          new CustomEvent('ecms:knowledge-graph-ready', {
            detail: {
              renderer: 'd3',
              nodes: filteredNodes.length,
              edges: filteredEdges.length,
              interactiveMs: Math.round(performance.now() - loadStartedAt),
            },
          }),
        );
      });
    }

    let tickCount = 0;
    sim.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y);

      labels.attr('x', (d: any) => d.x).attr('y', (d: any) => d.y);

      // Cluster regions update less often than nodes and links to keep large graphs responsive.
      tickCount += 1;
      if (tickCount === 30) fitEntireGraph();
      if (tickCount === 1 || tickCount % 8 === 0) {
        const boundaries = Array.from(sourceGroups.entries())
          .filter(([, members]) => members.length >= 2)
          .map(([group, members]) => {
            let minX = Infinity;
            let maxX = -Infinity;
            let minY = Infinity;
            let maxY = -Infinity;
            members.forEach((member) => {
              const x = member.x || 0;
              const y = member.y || 0;
              minX = Math.min(minX, x);
              maxX = Math.max(maxX, x);
              minY = Math.min(minY, y);
              maxY = Math.max(maxY, y);
            });
            return {
              group,
              cx: (minX + maxX) / 2,
              cy: (minY + maxY) / 2,
              rx: (maxX - minX) / 2 + 40,
              ry: (maxY - minY) / 2 + 40,
              color: getColor(members[0]),
            };
          });

        boundaryGroup
          .selectAll<SVGEllipseElement, (typeof boundaries)[number]>('ellipse')
          .data(boundaries, (d) => d.group)
          .join('ellipse')
          .attr('cx', (d) => d.cx)
          .attr('cy', (d) => d.cy)
          .attr('rx', (d) => d.rx)
          .attr('ry', (d) => d.ry)
          .attr('fill', (d) => d.color)
          .attr('fill-opacity', 0.045)
          .attr('stroke', (d) => d.color)
          .attr('stroke-opacity', 0.22)
          .attr('stroke-width', 1)
          .attr('stroke-dasharray', '4 6');
      }
    });

    // Click on background to deselect
    svg.on('click', () => {
      if (selectedNodeId) resetFocus();
      onSelectNode?.(null);
    });

    return () => {
      sim.stop();
      d3.select(container).selectAll('svg').remove();
    };
  }, [benchmark, loadStartedAt, rawNodes.length, rawEdges.length, searchFilter]);

  // Pause/resume
  useEffect(() => {
    const sim = simRef.current;
    if (!sim) return;
    if (paused) sim.stop();
    else sim.alpha(0.3).restart();
  }, [paused]);

  return (
    <div
      ref={containerRef}
      data-testid="knowledge-graph-d3"
      style={{ width: '100%', height: '100%', minHeight: 600 }}
    />
  );
};

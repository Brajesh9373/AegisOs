import type { KnowledgeGraphEdge, KnowledgeGraphNode } from './graphTypes';

const CATEGORIES = [
  'backend',
  'frontend',
  'security',
  'documentation',
  'configuration',
  'testing',
  'database',
  'ci/cd',
  'infrastructure',
  'dependencies',
  'code',
  'data',
  'other',
] as const;

export const BENCHMARK_DATASET_SIZES = [100_000, 500_000, 1_000_000] as const;

export function parseBenchmarkDatasetSize(value: string | null): number | null {
  if (!value) return null;
  const parsed = Number(value.replace(/[,_]/g, ''));
  return BENCHMARK_DATASET_SIZES.includes(parsed as (typeof BENCHMARK_DATASET_SIZES)[number])
    ? parsed
    : null;
}

/**
 * Deterministic scale fixture with the same object shape consumed by the legacy graph UI.
 * Two edges per node approximates the current post-merge rendered edge ratio.
 */
export function createSyntheticGraph(nodeCount: number): {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
} {
  const nodes = new Array<KnowledgeGraphNode>(nodeCount);
  const edges = new Array<KnowledgeGraphEdge>(nodeCount * 2);

  for (let index = 0; index < nodeCount; index += 1) {
    const category = CATEGORIES[index % CATEGORIES.length];
    nodes[index] = {
      id: `benchmark:${index}`,
      label: `${category} benchmark node ${index}`,
      group: index % 5 === 0 ? 'file' : 'code',
      category,
      source_group: `connection:${(index % 100) + 1}`,
      node_confidence: 0.5 + (index % 50) / 100,
    };

    edges[index * 2] = {
      id: `benchmark:ring:${index}`,
      source: `benchmark:${index}`,
      target: `benchmark:${(index + 1) % nodeCount}`,
      label: 'related',
    };
    edges[index * 2 + 1] = {
      id: `benchmark:skip:${index}`,
      source: `benchmark:${index}`,
      target: `benchmark:${(index * 31 + 17) % nodeCount}`,
      label: 'contains',
    };
  }

  return { nodes, edges };
}

/// <reference lib="webworker" />

import { tableFromIPC } from 'apache-arrow';
import type { KnowledgeGraphEdge, KnowledgeGraphNode } from './graphTypes';

interface DecodeRequest {
  pointsBuffer: ArrayBuffer;
  linksBuffer: ArrayBuffer;
}

self.onmessage = (event: MessageEvent<DecodeRequest>) => {
  try {
    const points = tableFromIPC(event.data.pointsBuffer);
    const links = tableFromIPC(event.data.linksBuffer);
    const nodes: KnowledgeGraphNode[] = [];
    const nodeIds: string[] = [];

    for (let index = 0; index < points.numRows; index += 1) {
      const row = points.get(index);
      if (!row) continue;
      const id = String(row.id);
      nodeIds[index] = id;
      nodes.push({
        id,
        label: String(row.label),
        group: String(row.group),
        category: String(row.category),
        source_group: row.source_group == null ? null : String(row.source_group),
        node_confidence: Number(row.confidence),
        x: Number(row.x),
        y: Number(row.y),
      });
    }

    const edges: KnowledgeGraphEdge[] = [];
    for (let index = 0; index < links.numRows; index += 1) {
      const row = links.get(index);
      if (!row) continue;
      const source = nodeIds[Number(row.source)];
      const target = nodeIds[Number(row.target)];
      if (!source || !target) continue;
      edges.push({
        id: String(row.id),
        source,
        target,
        label: String(row.label),
      });
    }
    self.postMessage({ nodes, edges });
  } catch (error) {
    self.postMessage({
      error: error instanceof Error ? error.message : 'Snapshot decoding failed',
    });
  }
};

export {};

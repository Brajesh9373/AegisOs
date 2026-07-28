import { describe, it, expect } from 'vitest';
import { BuilderSession } from '../src/index.js';

describe('Builder Engine', () => {
  it('should initialize session and undo/redo', () => {
    const session = new BuilderSession('sess-1');
    expect(session.canvas.nodes.length).toBe(0);

    session.updateCanvas({
      nodes: [{ id: 'n1', type: 'agent', position: { x: 0, y: 0 }, data: {} }],
      edges: [],
      viewport: { x: 0, y: 0, zoom: 1 },
    });
    expect(session.canvas.nodes.length).toBe(1);

    session.undo();
    expect(session.canvas.nodes.length).toBe(0);

    session.redo();
    expect(session.canvas.nodes.length).toBe(1);
  });
});

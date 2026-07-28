import { describe, it, expect } from 'vitest';
import { ExecutionEngine } from '@aegisos/execution-runtime';
import { WorkflowScheduler, WorkflowDefinition, WorkflowState } from '../src/index.js';

describe('Workflow Runtime', () => {
  it('should schedule and execute a basic workflow definition', async () => {
    const engine = new ExecutionEngine();
    const scheduler = new WorkflowScheduler(engine);

    const def: WorkflowDefinition = {
      id: 'test-wf',
      nodes: [
        { id: 'node1', type: 'task', config: {} },
        { id: 'node2', type: 'task', config: {} },
      ],
      edges: [{ source: 'node1', target: 'node2' }],
    };

    const instance = await scheduler.scheduleWorkflow(def);
    expect(instance.getModel().state).toBe(WorkflowState.Completed);
  });
});

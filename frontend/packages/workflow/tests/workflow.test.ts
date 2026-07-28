import { describe, it, expect } from 'vitest';
import { WorkflowRegistry } from '../src/core/registry.js';
import { WorkflowFactory } from '../src/core/factory.js';
import { WorkflowLifecycle, WorkflowLifecycleState } from '../src/core/lifecycle.js';

describe('Workflow Engine', () => {
  it('should initialize registry', () => {
    const registry = new WorkflowRegistry();
    expect(registry).toBeDefined();
  });

  it('should create workflows', () => {
    const factory = new WorkflowFactory();
    const wf = factory.createWorkflow('wf-1', 'Test WF');
    expect(wf.id).toBe('wf-1');
  });

  it('should manage lifecycle', () => {
    const lifecycle = new WorkflowLifecycle();
    expect(lifecycle.state).toBe(WorkflowLifecycleState.Draft);
    lifecycle.publish();
    expect(lifecycle.state).toBe(WorkflowLifecycleState.Published);
  });
});

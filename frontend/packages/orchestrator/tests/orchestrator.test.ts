import { describe, it, expect } from 'vitest';
import { OrchestratorRegistry, ExecutionPlanBuilder, ExecutionPlanner } from '../src/index.js';

describe('Orchestrator Engine', () => {
  it('should initialize registry', () => {
    const registry = new OrchestratorRegistry();
    expect(registry).toBeDefined();
  });

  it('should create execution plans', () => {
    const builder = new ExecutionPlanBuilder();
    const planner = new ExecutionPlanner(builder);

    const plan = planner.plan('test-workflow-id');
    expect(plan).toBeDefined();
    expect(plan.workflowId).toBe('test-workflow-id');
  });
});

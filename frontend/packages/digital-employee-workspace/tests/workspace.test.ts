import { describe, it, expect } from 'vitest';
import {
  WorkspaceService,
  WorkspaceAggregator,
  WorkspaceTimeline,
  WorkspaceContextManager,
} from '../src/index';
import { SecurityEngine } from '@aegisos/security';

describe('WorkspaceService', () => {
  it('should aggregate workspace state when authorized', () => {
    const security = new SecurityEngine();
    const aggregator = new WorkspaceAggregator();
    const timeline = new WorkspaceTimeline();
    const context = new WorkspaceContextManager();
    const service = new WorkspaceService(security, aggregator, timeline, context);

    const identity = { userId: 'de-01', token: 'valid-token', claims: { role: 'DigitalEmployee' } };
    const state = service.getWorkspaceState(identity);

    expect(state.budgetConsumption.limit).toBe(1000);
    expect(state.personalMetrics.productivity).toBe(95);
    expect(state.inbox).toBeDefined();
  });
});

import { describe, it, expect } from 'vitest';
import { ManagerDashboardService, DashboardAggregator } from '../src/index';
import { SecurityEngine } from '@aegisos/security';

describe('ManagerDashboardService', () => {
  it('should aggregate dashboard state when user is authorized', () => {
    const security = new SecurityEngine(); // Automatically returns true in mock
    const aggregator = new DashboardAggregator();
    const service = new ManagerDashboardService(security, aggregator);

    const identity = { userId: 'manager-01', token: 'valid-token', claims: { role: 'Manager' } };
    const state = service.getDashboardState(identity);

    expect(state.budget.limit).toBe(10000);
    expect(state.budget.consumed).toBe(1250);
    expect(state.digitalEmployees).toBeDefined();
  });
});

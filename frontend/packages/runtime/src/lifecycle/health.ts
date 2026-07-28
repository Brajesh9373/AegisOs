import { RuntimeContext } from '../context/runtime';
import { LifecycleManager } from './manager';

export interface HealthStatus {
  status: 'UP' | 'DOWN' | 'DEGRADED';
  checks: Record<string, 'PASS' | 'FAIL'>;
}

export class HealthManager {
  constructor(
    private readonly context: RuntimeContext,
    private readonly lifecycle: LifecycleManager,
  ) {}

  public async checkHealth(): Promise<HealthStatus> {
    const isRunning = this.lifecycle.getState() === 'RUNNING';
    return {
      status: isRunning ? 'UP' : 'DOWN',
      checks: {
        runtime: isRunning ? 'PASS' : 'FAIL',
        di: this.context.resolver ? 'PASS' : 'FAIL',
      },
    };
  }
}

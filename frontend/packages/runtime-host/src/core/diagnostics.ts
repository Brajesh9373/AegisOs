export interface RuntimeMetrics {
  uptimeSeconds: number;
  memoryUsage: number;
  activeRequests: number;
}
export interface RuntimeHealth {
  status: 'healthy' | 'degraded' | 'down';
  components: Record<string, string>;
}

export class DiagnosticsManager {
  private startTime = Date.now();
  private activeCount = 0;

  public log(level: 'info' | 'warn' | 'error', message: string, meta?: unknown): void {
    console.log(
      `[${new Date().toISOString()}] [${level.toUpperCase()}] ${message}`,
      meta ? meta : '',
    );
  }

  public getMetrics(): RuntimeMetrics {
    return {
      uptimeSeconds: Math.floor((Date.now() - this.startTime) / 1000),
      memoryUsage: process.memoryUsage?.()?.heapUsed || 0,
      activeRequests: this.activeCount,
    };
  }

  public checkHealth(): RuntimeHealth {
    return {
      status: 'healthy',
      components: {
        host: 'ok',
      },
    };
  }

  public incrementRequest(): void {
    this.activeCount++;
  }
  public decrementRequest(): void {
    this.activeCount--;
  }
}

import { ILogger, PlatformError } from '@aegisos/shared';

export interface ILifecycleHook {
  onStart?(): Promise<void>;
  onStop?(): Promise<void>;
  onSuspend?(): Promise<void>;
  onResume?(): Promise<void>;
}

export class LifecycleManager {
  private hooks: ILifecycleHook[] = [];
  private state: 'STOPPED' | 'STARTING' | 'RUNNING' | 'SUSPENDED' | 'STOPPING' = 'STOPPED';

  constructor(private readonly logger: ILogger) {}

  public register(hook: ILifecycleHook): void {
    this.hooks.push(hook);
  }

  public async start(): Promise<void> {
    if (this.state !== 'STOPPED')
      throw new PlatformError('Cannot start: already running', 'LIFECYCLE_ERROR');
    this.state = 'STARTING';
    for (const hook of this.hooks) {
      if (hook.onStart) await hook.onStart();
    }
    this.state = 'RUNNING';
    this.logger.info('Runtime started');
  }

  public async stop(): Promise<void> {
    if (this.state === 'STOPPED') return;
    this.state = 'STOPPING';
    for (const hook of [...this.hooks].reverse()) {
      if (hook.onStop) await hook.onStop();
    }
    this.state = 'STOPPED';
    this.logger.info('Runtime stopped');
  }

  public getState() {
    return this.state;
  }
}

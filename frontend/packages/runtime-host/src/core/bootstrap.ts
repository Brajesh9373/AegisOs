import { HostLifecycle, HostState } from './lifecycle.js';
import { DiagnosticsManager } from './diagnostics.js';
import { PluginRegistry, PluginLoader } from './plugin.js';
import { IDService, ClockService, EventBusBootstrap } from './services.js';
import { RuntimeContext } from './context.js';

export class RuntimeBootstrap {
  public lifecycle = new HostLifecycle();
  public diagnostics = new DiagnosticsManager();
  public pluginRegistry = new PluginRegistry();
  public pluginLoader = new PluginLoader(this.pluginRegistry);

  public idService = new IDService();
  public clock = new ClockService();
  public eventBus = new EventBusBootstrap();

  private context: RuntimeContext | null = null;

  public async start(config: { environment: string }): Promise<void> {
    this.diagnostics.log('info', `Starting aegisOS Platform in ${config.environment}`);
    this.lifecycle.transition(HostState.Startup);

    // Bootstrap Pipeline
    this.context = {
      executionId: this.idService.generateId('exec'),
      correlationId: this.idService.generateId('corr'),
    };

    this.diagnostics.log('info', 'Context initialized', this.context);

    // Abstract DI container & Registry setups happen here

    this.lifecycle.transition(HostState.Ready);
    this.lifecycle.transition(HostState.Running);
    this.diagnostics.log('info', 'Platform is Running');
  }

  public async shutdown(): Promise<void> {
    this.diagnostics.log('info', 'Shutting down aegisOS Platform');
    this.lifecycle.transition(HostState.Shutdown);
    this.lifecycle.transition(HostState.Stopped);
  }

  public getContext(): RuntimeContext {
    if (!this.context) throw new Error('Runtime not started');
    return this.context;
  }
}

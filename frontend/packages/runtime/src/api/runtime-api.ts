import { loadConfiguration, ConfigurationRegistry } from '@aegisos/config';
import { unwrap } from '@aegisos/shared';
import { Container } from '../di/container';
import { ServiceRegistry, CapabilityRegistry, ModuleRegistry } from '../di/registry';
import { RuntimeContext } from '../context/runtime';
import { LifecycleManager } from '../lifecycle/manager';
import { HealthManager } from '../lifecycle/health';
import { ErrorBoundary } from '../lifecycle/error-boundary';
import { RuntimeEventBus } from '../events/bus';

export class RuntimeAPI {
  public readonly context: RuntimeContext;
  public readonly lifecycle: LifecycleManager;
  public readonly health: HealthManager;
  public readonly events: RuntimeEventBus;
  public readonly errorBoundary: ErrorBoundary;

  constructor() {
    // 1. Load config
    const configResult = loadConfiguration();
    const config = unwrap(configResult);

    // Set config globally for legacy support, though DI is preferred
    ConfigurationRegistry.set(config);

    // 2. Init DI
    const container = new Container();

    // Placeholder no-op logger, expected to be overridden by host application
    const defaultLogger = {
      info: () => {},
      warn: () => {},
      error: () => {},
      debug: () => {},
    };
    container.registerValue('logger', defaultLogger);

    // 3. Init Registries
    const services = new ServiceRegistry();
    const capabilities = new CapabilityRegistry();
    const modules = new ModuleRegistry();

    // 4. Init Context
    this.context = new RuntimeContext(config, container, services, capabilities, modules);

    // 5. Init Subsystems
    this.lifecycle = new LifecycleManager(defaultLogger);
    this.health = new HealthManager(this.context, this.lifecycle);
    this.errorBoundary = new ErrorBoundary(defaultLogger);
    this.events = new RuntimeEventBus(defaultLogger);

    // Trap uncaught exceptions
    this.errorBoundary.registerProcessHooks();
  }
}

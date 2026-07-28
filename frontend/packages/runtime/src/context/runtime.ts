import { RootConfig } from '@aegisos/config';
import { IResolver } from '../di/container';
import { ServiceRegistry, CapabilityRegistry, ModuleRegistry } from '../di/registry';

/**
 * The immutable root state of the running engine.
 */
export class RuntimeContext {
  constructor(
    public readonly config: RootConfig,
    public readonly resolver: IResolver,
    public readonly services: ServiceRegistry,
    public readonly capabilities: CapabilityRegistry,
    public readonly modules: ModuleRegistry,
  ) {
    Object.freeze(this);
  }
}

import { BuilderRegistry } from '../core/registry.js';
import { BuilderSession } from '../core/session.js';

export class BuilderRegistryAPI {
  constructor(private registry: BuilderRegistry) {}

  public registerSession(session: BuilderSession): void {
    this.registry.register(session);
  }

  public getSession(id: string): BuilderSession {
    return this.registry.get(id);
  }
}

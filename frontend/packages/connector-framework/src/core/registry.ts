import { UniversalConnector } from '@aegisos/contracts';
export class ConnectorRegistry {
  private connectors = new Map<string, UniversalConnector>();
  register(connector: UniversalConnector) {
    this.connectors.set(connector.id, connector);
  }
  get(id: string) {
    return this.connectors.get(id);
  }
  list() {
    return Array.from(this.connectors.values());
  }
}

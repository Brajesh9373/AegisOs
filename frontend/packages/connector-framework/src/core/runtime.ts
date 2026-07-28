import { UniversalConnector } from '@aegisos/contracts';
export class ConnectorRuntime {
  async connect(connectorId: string) {
    return true;
  }
  async synchronize(connectorId: string, modality: string) {
    return true;
  }
}

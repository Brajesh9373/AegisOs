import { DigitalEmployeeIdentity, WorkspaceContext } from '@aegisos/agent';
export class BuilderV3Adapter {
  createEmployee(identity: DigitalEmployeeIdentity) {
    return new WorkspaceContext(identity);
  }
}

import { DigitalEmployeeIdentity } from '../identity/digital-employee';
export class WorkspaceContext {
  public inbox = [];
  public tasks = [];
  public calendar = [];
  public notes = [];
  public approvals = [];
  public reports = [];
  public deliverables = [];
  constructor(public identity: DigitalEmployeeIdentity) {}
}

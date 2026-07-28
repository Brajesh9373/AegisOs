import { DigitalEmployee } from '@aegisos/contracts';
export class DigitalEmployeeIdentity {
  constructor(public config: DigitalEmployee) {}
  getOwner() {
    return this.config.humanOwnerId;
  }
  getManager() {
    return this.config.managerId;
  }
  getDepartment() {
    return this.config.department;
  }
  getOrganization() {
    return this.config.organizationId;
  }
  requiresApproval(riskLevel: number) {
    return riskLevel >= (this.config.approvalAuthorityThreshold || 100);
  }
}

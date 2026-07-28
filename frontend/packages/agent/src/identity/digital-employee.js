export class DigitalEmployeeIdentity {
    config;
    constructor(config) {
        this.config = config;
    }
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
    requiresApproval(riskLevel) {
        return riskLevel >= (this.config.approvalAuthorityThreshold || 100);
    }
}

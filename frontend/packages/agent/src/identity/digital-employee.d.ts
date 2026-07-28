import { DigitalEmployee } from '@aegisos/contracts';
export declare class DigitalEmployeeIdentity {
    config: DigitalEmployee;
    constructor(config: DigitalEmployee);
    getOwner(): string;
    getManager(): string;
    getDepartment(): string;
    getOrganization(): string;
    requiresApproval(riskLevel: number): boolean;
}

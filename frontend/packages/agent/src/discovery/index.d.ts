import { DigitalEmployee } from '@aegisos/contracts';
import { AgentRegistry } from '../core/registry';
export declare class AgentDiscovery {
    private registry;
    constructor(registry: AgentRegistry);
    findByRole(role: string): DigitalEmployee[];
    findByDepartment(department: string): DigitalEmployee[];
    findIdleWorkers(): DigitalEmployee[];
}

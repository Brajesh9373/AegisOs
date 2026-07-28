import { DigitalEmployee } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';
export declare class AgentNotFoundError extends PlatformError {
    constructor(id: string);
}
export declare class AgentRegistry {
    private agents;
    register(agent: DigitalEmployee): void;
    get(id: string): DigitalEmployee;
    getAll(): DigitalEmployee[];
    remove(id: string): void;
}

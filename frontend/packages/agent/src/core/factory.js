import { generateId } from '@aegisos/shared';
export class AgentFactory {
    static createWorker(name, department) {
        return {
            id: generateId(),
            type: 'DigitalEmployee',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            name,
            department,
            role: 'Worker',
            status: 'Idle',
            skills: [],
            tools: [],
            humanOwnerId: 'system',
            managerId: 'system',
            organizationId: 'default',
        };
    }
    static createManager(name, department) {
        return {
            id: generateId(),
            type: 'DigitalEmployee',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            name,
            department,
            role: 'Manager',
            status: 'Idle',
            skills: [],
            tools: [],
            humanOwnerId: 'system',
            managerId: 'system',
            organizationId: 'default',
        };
    }
}

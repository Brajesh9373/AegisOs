import { DigitalEmployee } from '@aegisos/contracts';
import { generateId } from '@aegisos/shared';

export class AgentFactory {
  public static createWorker(name: string, department: string): DigitalEmployee {
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

  public static createManager(name: string, department: string): DigitalEmployee {
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

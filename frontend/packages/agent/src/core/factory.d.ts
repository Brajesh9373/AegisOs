import { DigitalEmployee } from '@aegisos/contracts';
export declare class AgentFactory {
    static createWorker(name: string, department: string): DigitalEmployee;
    static createManager(name: string, department: string): DigitalEmployee;
}

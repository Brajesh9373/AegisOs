import { describe, it, expect } from 'vitest';
import { AgentFactory, AgentRegistry, AgentStateMachine, AgentDiscovery } from '../src';

describe('Agent Engine Foundation', () => {
  it('Factory creates valid agents', () => {
    const worker = AgentFactory.createWorker('Alice', 'Engineering');
    expect(worker.id).toBeDefined();
    expect(worker.role).toBe('Worker');
    expect(worker.status).toBe('Idle');

    const manager = AgentFactory.createManager('Bob', 'HR');
    expect(manager.role).toBe('Manager');
  });

  it('Registry manages agents', () => {
    const registry = new AgentRegistry();
    const worker = AgentFactory.createWorker('Alice', 'Engineering');

    registry.register(worker);
    expect(registry.get(worker.id)).toEqual(worker);
    expect(registry.getAll().length).toBe(1);

    registry.remove(worker.id);
    expect(() => registry.get(worker.id)).toThrowError(/not found/);
  });

  it('State Machine enforces valid transitions', () => {
    const sm = new AgentStateMachine();
    expect(sm.status).toBe('Idle');

    sm.transition('Assigned');
    expect(sm.status).toBe('Assigned');

    expect(() => sm.transition('Completed')).toThrowError(/Invalid state transition/);
  });

  it('Discovery finds agents', () => {
    const registry = new AgentRegistry();
    const discovery = new AgentDiscovery(registry);

    const worker1 = AgentFactory.createWorker('Alice', 'Engineering');
    const worker2 = AgentFactory.createWorker('Charlie', 'Sales');
    const manager = AgentFactory.createManager('Bob', 'Engineering');

    registry.register(worker1);
    registry.register(worker2);
    registry.register(manager);

    expect(discovery.findByRole('Worker').length).toBe(2);
    expect(discovery.findByRole('Manager').length).toBe(1);
    expect(discovery.findByDepartment('Engineering').length).toBe(2);
    expect(discovery.findIdleWorkers().length).toBe(2);
  });
});

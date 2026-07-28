import { AgentPool } from './pool.js';
import { TaskModel, SupervisorPolicy, SharedMemoryLayer, SharedKnowledgeLayer } from './types.js';

export class TeamManager {
  constructor(
    private pool: AgentPool,
    private policy: SupervisorPolicy,
    private memory: SharedMemoryLayer,
    private knowledge: SharedKnowledgeLayer,
  ) {}

  public distributeTask(task: TaskModel): string {
    const available = this.pool.getAvailableAgents();
    if (available.length === 0) {
      throw new Error('No agents available for delegation');
    }

    // Abstract Round-Robin or Skill-Based delegation
    const assignedAgentId = available[0];
    task.assignedTo = assignedAgentId;
    task.status = 'in_progress';

    // Distribute via shared memory pointers to retain stateless bindings
    this.memory.set(`task_${task.taskId}`, task);
    return assignedAgentId;
  }

  public escalate(taskId: string, error: unknown): void {
    const task = this.memory.get(`task_${taskId}`) as TaskModel;
    if (task) {
      task.status = 'failed';
      // Store escalation log for supervisor
      this.memory.set(`escalation_${taskId}`, { error, timestamp: Date.now() });
    }
  }

  public resolveConflict(agentA: string, agentB: string): void {
    if (this.policy.autoResolveConflicts) {
      // Abstract conflict resolution protocol mapping
      this.memory.set(`conflict_${agentA}_${agentB}`, 'resolved');
    }
  }
}

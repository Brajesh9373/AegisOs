import { describe, it, expect } from 'vitest';
import { AgentRuntime } from '@aegisos/agent-runtime';
import { TeamRuntime, TeamState, TaskModel } from '../src/index.js';

describe('Multi-Agent Runtime', () => {
  it('should manage team collaboration and delegation successfully', () => {
    const agentRuntime = new AgentRuntime();
    const team = new TeamRuntime(agentRuntime);

    expect(team.getState()).toBe(TeamState.Forming);

    team.addMember('agent-alpha');
    team.addMember('agent-beta');

    team.startCollaboration();
    expect(team.getState()).toBe(TeamState.Collaborating);

    const task: TaskModel = {
      taskId: 'task-001',
      payload: { action: 'review' },
      status: 'pending',
    };
    const assignee = team.delegate(task);

    expect(assignee).toBe('agent-alpha');
    expect(team.metrics.tasksDistributed).toBe(1);

    team.complete();
    expect(team.getState()).toBe(TeamState.Completed);
  });
});

import { describe, it, expect } from 'vitest';
import { AgentRuntime, AgentState } from '../src/index.js';

describe('Agent Runtime', () => {
  it('should transition states correctly during skill execution', async () => {
    const runtime = new AgentRuntime();
    const session = runtime.createSession('agent-test-1');

    expect(session.getContext().state).toBe(AgentState.Idle);

    // Test the state transitions synchronously internally
    session.updateState(AgentState.Thinking);
    expect(session.getContext().state).toBe(AgentState.Thinking);

    await runtime.invokeSkill(session.id, 'skill-1');

    // After skill execution it reverts back to thinking natively in the mocked executor
    expect(session.getContext().state).toBe(AgentState.Thinking);
  });
});

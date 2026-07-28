import { describe, it, expect } from 'vitest';
import {
  ExecutionEngine,
  StepExecutor,
  SequentialExecutor,
  ExecutionState,
  ExecutionContext,
} from '../src/index.js';

describe('Execution Runtime', () => {
  it('should execute a valid sequential pipeline to completion', async () => {
    const engine = new ExecutionEngine();

    let executedSteps = 0;
    class MockStep extends StepExecutor {
      public async execute(_ctx: ExecutionContext): Promise<void> {
        executedSteps++;
      }
    }

    const executor = new SequentialExecutor([new MockStep(), new MockStep()]);
    const session = await engine.executePlan(executor);

    expect(executedSteps).toBe(2);
    expect(session.context.state).toBe(ExecutionState.Completed);
  });

  it('should handle timeouts effectively', async () => {
    const engine = new ExecutionEngine();

    class SlowStep extends StepExecutor {
      public async execute(_ctx: ExecutionContext): Promise<void> {
        return new Promise((resolve) => setTimeout(resolve, 100));
      }
    }

    const session = await engine.executePlan(new SlowStep(), { timeoutMs: 10 });
    expect(session.context.state).toBe(ExecutionState.Failed);
  });
});

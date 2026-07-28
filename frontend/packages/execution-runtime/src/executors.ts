import { ExecutionContext } from './types.js';

export interface Executor {
  execute(context: ExecutionContext): Promise<void>;
}

export class StepExecutor implements Executor {
  public async execute(_context: ExecutionContext): Promise<void> {
    // Abstract execution step - delegates down to plugins/providers externally
  }
}

export class SequentialExecutor implements Executor {
  constructor(private steps: Executor[]) {}
  public async execute(context: ExecutionContext): Promise<void> {
    for (const step of this.steps) {
      await step.execute(context);
    }
  }
}

export class ParallelExecutor implements Executor {
  constructor(private steps: Executor[]) {}
  public async execute(context: ExecutionContext): Promise<void> {
    await Promise.all(this.steps.map((s) => s.execute(context)));
  }
}

export class ConditionalExecutor implements Executor {
  constructor(
    private condition: (ctx: ExecutionContext) => boolean,
    private onTrue: Executor,
    private onFalse: Executor,
  ) {}
  public async execute(context: ExecutionContext): Promise<void> {
    if (this.condition(context)) {
      await this.onTrue.execute(context);
    } else {
      await this.onFalse.execute(context);
    }
  }
}

export class RetryExecutor implements Executor {
  constructor(
    private step: Executor,
    private maxRetries: number,
  ) {}
  public async execute(context: ExecutionContext): Promise<void> {
    let attempts = 0;
    while (attempts < this.maxRetries) {
      try {
        await this.step.execute(context);
        return;
      } catch (e) {
        attempts++;
        if (attempts >= this.maxRetries) throw e;
      }
    }
  }
}

export class CompensationExecutor implements Executor {
  constructor(
    private forward: Executor,
    private compensate: Executor,
  ) {}
  public async execute(context: ExecutionContext): Promise<void> {
    try {
      await this.forward.execute(context);
    } catch (e) {
      await this.compensate.execute(context);
      throw e;
    }
  }
}

export class RollbackExecutor implements Executor {
  constructor(
    private step: Executor,
    private rollback: Executor,
  ) {}
  public async execute(context: ExecutionContext): Promise<void> {
    try {
      await this.step.execute(context);
    } catch (e) {
      await this.rollback.execute(context);
      throw e;
    }
  }
}

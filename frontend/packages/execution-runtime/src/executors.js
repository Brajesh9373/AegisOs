export class StepExecutor {
    async execute(_context) {
        // Abstract execution step - delegates down to plugins/providers externally
    }
}
export class SequentialExecutor {
    steps;
    constructor(steps) {
        this.steps = steps;
    }
    async execute(context) {
        for (const step of this.steps) {
            await step.execute(context);
        }
    }
}
export class ParallelExecutor {
    steps;
    constructor(steps) {
        this.steps = steps;
    }
    async execute(context) {
        await Promise.all(this.steps.map((s) => s.execute(context)));
    }
}
export class ConditionalExecutor {
    condition;
    onTrue;
    onFalse;
    constructor(condition, onTrue, onFalse) {
        this.condition = condition;
        this.onTrue = onTrue;
        this.onFalse = onFalse;
    }
    async execute(context) {
        if (this.condition(context)) {
            await this.onTrue.execute(context);
        }
        else {
            await this.onFalse.execute(context);
        }
    }
}
export class RetryExecutor {
    step;
    maxRetries;
    constructor(step, maxRetries) {
        this.step = step;
        this.maxRetries = maxRetries;
    }
    async execute(context) {
        let attempts = 0;
        while (attempts < this.maxRetries) {
            try {
                await this.step.execute(context);
                return;
            }
            catch (e) {
                attempts++;
                if (attempts >= this.maxRetries)
                    throw e;
            }
        }
    }
}
export class CompensationExecutor {
    forward;
    compensate;
    constructor(forward, compensate) {
        this.forward = forward;
        this.compensate = compensate;
    }
    async execute(context) {
        try {
            await this.forward.execute(context);
        }
        catch (e) {
            await this.compensate.execute(context);
            throw e;
        }
    }
}
export class RollbackExecutor {
    step;
    rollback;
    constructor(step, rollback) {
        this.step = step;
        this.rollback = rollback;
    }
    async execute(context) {
        try {
            await this.step.execute(context);
        }
        catch (e) {
            await this.rollback.execute(context);
            throw e;
        }
    }
}

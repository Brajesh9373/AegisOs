import { Executor, ExecutionContext } from '@aegisos/execution-runtime';
import { NodeDefinition, EdgeDefinition, WorkflowMetricsContract } from './types.js';

export class NodeExecutor implements Executor {
  constructor(
    private node: NodeDefinition,
    private metrics?: WorkflowMetricsContract,
  ) {}

  public async execute(context: ExecutionContext): Promise<void> {
    const start = Date.now();
    try {
      if (this.node.type === 'human-approval') {
        // Human Approval Wait State
        context.variables.set('WAITING_APPROVAL', true);
        return; // Execution halts, expecting external signal to resume
      }

      // Node execution abstraction mapped cleanly to Execution Runtime
      context.variables.set(`node_${this.node.id}_completed`, true);

      if (this.metrics) {
        this.metrics.recordNodeExecution(this.node.id, Date.now() - start, true);
      }
    } catch (e) {
      if (this.metrics) {
        this.metrics.recordNodeExecution(this.node.id, Date.now() - start, false);
      }
      throw e;
    }
  }
}

export class EdgeTraversalExecutor implements Executor {
  constructor(private edges: EdgeDefinition[]) {}

  public async execute(context: ExecutionContext): Promise<void> {
    for (const edge of this.edges) {
      if (edge.condition) {
        // Conditional Evaluation logic mapped natively without business rules
        const conditionMet = context.variables.get(edge.condition) === true;
        if (!conditionMet) continue;
      }
      context.variables.set(`traversed_${edge.source}_to_${edge.target}`, true);
    }
  }
}

import {
  ExecutionEngine,
  SequentialExecutor,
  ParallelExecutor,
  ExecutionState,
  CompensationExecutor,
} from '@aegisos/execution-runtime';
import { WorkflowDefinition, WorkflowPersistenceContract, WorkflowState } from './types.js';
import { WorkflowInstance } from './instance.js';
import { NodeExecutor, EdgeTraversalExecutor } from './executors.js';

export class WorkflowScheduler {
  constructor(
    private engine: ExecutionEngine,
    private persistence?: WorkflowPersistenceContract,
  ) {}

  public async scheduleWorkflow(definition: WorkflowDefinition): Promise<WorkflowInstance> {
    const instance = new WorkflowInstance(definition.id);
    instance.updateState(WorkflowState.Running);

    if (this.persistence) {
      await this.persistence.saveInstance(instance.getModel());
    }

    // Build Execution Graph leveraging ExecutionRuntime
    // This supports Parallel Branch Execution and Compensation Handling intrinsically
    const nodeExecutors = definition.nodes.map((node) => new NodeExecutor(node));
    const edgesExecutor = new EdgeTraversalExecutor(definition.edges);

    // Abstract parallel pipeline mapping
    const executionPlan = new SequentialExecutor([
      new ParallelExecutor(nodeExecutors),
      edgesExecutor,
    ]);

    const compensator = new CompensationExecutor(
      executionPlan,
      new SequentialExecutor([]), // Clean up dummy step for abstract Rollback
    );

    const session = await this.engine.executePlan(compensator);

    if (session.context.state === ExecutionState.Completed) {
      instance.updateState(WorkflowState.Completed);
    } else if (session.context.state === ExecutionState.Failed) {
      instance.updateState(WorkflowState.Failed);
    }

    if (this.persistence) {
      await this.persistence.saveInstance(instance.getModel());
    }

    return instance;
  }
}

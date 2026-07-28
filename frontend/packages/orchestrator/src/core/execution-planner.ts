export interface ExecutionPlanNode {
  id: string;
  action: string;
  resolvedAgentId?: string;
  resolvedSkillId?: string;
  resolvedToolId?: string;
  resolvedMemoryId?: string;
  resolvedKnowledgeId?: string;
  dependencies: string[];
}

export interface ExecutionPlan {
  id: string;
  workflowId: string;
  nodes: ExecutionPlanNode[];
}

export class ExecutionPlanBuilder {
  private nodes: ExecutionPlanNode[] = [];

  public addNode(node: ExecutionPlanNode): this {
    this.nodes.push(node);
    return this;
  }

  public build(workflowId: string): ExecutionPlan {
    return {
      id: crypto.randomUUID(),
      workflowId,
      nodes: this.nodes,
    };
  }
}

export class ExecutionPlanner {
  constructor(private builder: ExecutionPlanBuilder) {}

  public plan(workflowId: string): ExecutionPlan {
    // Abstract plan resolution
    return this.builder.build(workflowId);
  }
}

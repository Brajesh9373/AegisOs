export enum WorkflowLifecycleState {
  Draft = 'draft',
  Published = 'published',
  Deprecated = 'deprecated',
  Archived = 'archived',
}

export class WorkflowLifecycle {
  public state: WorkflowLifecycleState = WorkflowLifecycleState.Draft;

  public publish(): void {
    this.state = WorkflowLifecycleState.Published;
  }

  public deprecate(): void {
    this.state = WorkflowLifecycleState.Deprecated;
  }

  public archive(): void {
    this.state = WorkflowLifecycleState.Archived;
  }
}

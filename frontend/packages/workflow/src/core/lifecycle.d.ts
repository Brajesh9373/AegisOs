export declare enum WorkflowLifecycleState {
    Draft = "draft",
    Published = "published",
    Deprecated = "deprecated",
    Archived = "archived"
}
export declare class WorkflowLifecycle {
    state: WorkflowLifecycleState;
    publish(): void;
    deprecate(): void;
    archive(): void;
}

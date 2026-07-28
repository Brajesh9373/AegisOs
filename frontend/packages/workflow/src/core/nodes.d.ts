export declare enum WorkflowNodeType {
    Step = "step",
    Sequential = "sequential",
    Conditional = "conditional",
    Parallel = "parallel",
    Switch = "switch",
    Loop = "loop",
    Approval = "approval",
    HumanTask = "human-task",
    WaitState = "wait-state",
    EventTrigger = "event-trigger",
    ScheduleTrigger = "schedule-trigger"
}
export interface WorkflowNode {
    id: string;
    type: WorkflowNodeType;
    name: string;
    config: Record<string, unknown>;
}

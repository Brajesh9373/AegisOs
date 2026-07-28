export var WorkflowNodeType;
(function (WorkflowNodeType) {
    WorkflowNodeType["Step"] = "step";
    WorkflowNodeType["Sequential"] = "sequential";
    WorkflowNodeType["Conditional"] = "conditional";
    WorkflowNodeType["Parallel"] = "parallel";
    WorkflowNodeType["Switch"] = "switch";
    WorkflowNodeType["Loop"] = "loop";
    WorkflowNodeType["Approval"] = "approval";
    WorkflowNodeType["HumanTask"] = "human-task";
    WorkflowNodeType["WaitState"] = "wait-state";
    WorkflowNodeType["EventTrigger"] = "event-trigger";
    WorkflowNodeType["ScheduleTrigger"] = "schedule-trigger";
})(WorkflowNodeType || (WorkflowNodeType = {}));

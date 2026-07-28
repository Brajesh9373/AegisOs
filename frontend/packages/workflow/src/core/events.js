export var WorkflowEventType;
(function (WorkflowEventType) {
    WorkflowEventType["Started"] = "workflow.started";
    WorkflowEventType["Completed"] = "workflow.completed";
    WorkflowEventType["Failed"] = "workflow.failed";
    WorkflowEventType["NodeEntered"] = "workflow.node.entered";
    WorkflowEventType["NodeExited"] = "workflow.node.exited";
})(WorkflowEventType || (WorkflowEventType = {}));

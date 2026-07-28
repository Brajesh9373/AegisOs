export var WorkflowLifecycleState;
(function (WorkflowLifecycleState) {
    WorkflowLifecycleState["Draft"] = "draft";
    WorkflowLifecycleState["Published"] = "published";
    WorkflowLifecycleState["Deprecated"] = "deprecated";
    WorkflowLifecycleState["Archived"] = "archived";
})(WorkflowLifecycleState || (WorkflowLifecycleState = {}));
export class WorkflowLifecycle {
    state = WorkflowLifecycleState.Draft;
    publish() {
        this.state = WorkflowLifecycleState.Published;
    }
    deprecate() {
        this.state = WorkflowLifecycleState.Deprecated;
    }
    archive() {
        this.state = WorkflowLifecycleState.Archived;
    }
}

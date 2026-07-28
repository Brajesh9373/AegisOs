export var ExecutionState;
(function (ExecutionState) {
    ExecutionState["Created"] = "created";
    ExecutionState["Scheduled"] = "scheduled";
    ExecutionState["Running"] = "running";
    ExecutionState["Waiting"] = "waiting";
    ExecutionState["Retrying"] = "retrying";
    ExecutionState["Paused"] = "paused";
    ExecutionState["Cancelled"] = "cancelled";
    ExecutionState["Failed"] = "failed";
    ExecutionState["Completed"] = "completed";
})(ExecutionState || (ExecutionState = {}));

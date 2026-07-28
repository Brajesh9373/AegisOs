import { AgentStateMachine } from '../core/state';
export class AgentHealth {
    isHealthy = true;
    lastCheck = new Date();
    errors = [];
    reportError(error) {
        this.isHealthy = false;
        this.errors.push(error);
    }
    markHealthy() {
        this.isHealthy = true;
        this.errors = [];
        this.lastCheck = new Date();
    }
}
export class AgentMetrics {
    tasksCompleted = 0;
    tasksFailed = 0;
    activeTimeMs = 0;
    recordTaskCompletion() {
        this.tasksCompleted++;
    }
    recordTaskFailure() {
        this.tasksFailed++;
    }
}
export class AgentContext {
    id;
    stateMachine;
    health;
    metrics;
    constructor(id) {
        this.id = id;
        this.stateMachine = new AgentStateMachine();
        this.health = new AgentHealth();
        this.metrics = new AgentMetrics();
    }
    get status() {
        return this.stateMachine.status;
    }
}

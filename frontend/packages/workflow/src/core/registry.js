import { PlatformError } from '@aegisos/shared';
export class WorkflowNotFoundError extends PlatformError {
    constructor(id) {
        super(`Workflow with ID ${id} not found`);
    }
}
export class WorkflowRegistry {
    items = new Map();
    register(item) {
        this.items.set(item.id, item);
    }
    get(id) {
        const item = this.items.get(id);
        if (!item) {
            throw new WorkflowNotFoundError(id);
        }
        return item;
    }
    getAll() {
        return Array.from(this.items.values());
    }
    remove(id) {
        this.items.delete(id);
    }
}

export class WorkflowFactory {
    createWorkflow(id, name) {
        return {
            id,
            name,
            version: '1.0.0',
            description: 'Auto-generated workflow',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };
    }
}

export class WorkflowVersioning {
    getNextVersion(currentVersion, type) {
        const parts = currentVersion.split('.').map(Number);
        if (type === 'major')
            return `${parts[0] + 1}.0.0`;
        if (type === 'minor')
            return `${parts[0]}.${parts[1] + 1}.0`;
        return `${parts[0]}.${parts[1]}.${parts[2] + 1}`;
    }
}

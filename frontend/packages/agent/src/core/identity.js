import { generateId } from '@aegisos/shared';
export class AgentIdentity {
    id;
    name;
    role;
    constructor(name, role) {
        this.id = generateId();
        this.name = name;
        this.role = role;
    }
}

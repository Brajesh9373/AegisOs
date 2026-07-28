import { generateId } from '@aegisos/shared';

export class AgentIdentity {
  public readonly id: string;
  public readonly name: string;
  public readonly role: string;

  constructor(name: string, role: string) {
    this.id = generateId();
    this.name = name;
    this.role = role;
  }
}

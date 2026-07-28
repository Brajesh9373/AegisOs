export class AgentResolver {
  public resolveAgent(roleReference: string): string {
    return `resolved-agent-for-${roleReference}`;
  }
}

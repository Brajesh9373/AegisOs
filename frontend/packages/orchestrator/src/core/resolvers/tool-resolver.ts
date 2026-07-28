export class ToolResolver {
  public resolveTool(toolReference: string): string {
    return `resolved-tool-for-${toolReference}`;
  }
}

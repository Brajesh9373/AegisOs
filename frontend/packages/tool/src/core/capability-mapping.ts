export class ToolCapabilityMapping {
  private mappings = new Map<string, string[]>();

  public mapToolToCapability(toolId: string, capabilityId: string): void {
    const caps = this.mappings.get(toolId) || [];
    if (!caps.includes(capabilityId)) {
      caps.push(capabilityId);
      this.mappings.set(toolId, caps);
    }
  }

  public getCapabilitiesForTool(toolId: string): string[] {
    return this.mappings.get(toolId) || [];
  }
}

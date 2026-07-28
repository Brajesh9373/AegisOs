export class ToolVersionManager {
  private versions = new Map<string, Set<string>>();

  public registerVersion(name: string, version: string): void {
    if (!this.versions.has(name)) {
      this.versions.set(name, new Set());
    }
    this.versions.get(name)!.add(version);
  }

  public getVersions(name: string): string[] {
    const versions = this.versions.get(name);
    return versions ? Array.from(versions) : [];
  }
}

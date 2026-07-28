export class SkillVersionManager {
  // Mapping of skill name to versions (e.g., 'data-extractor' -> ['1.0.0', '1.1.0'])
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

  public hasVersion(name: string, version: string): boolean {
    const versions = this.versions.get(name);
    return versions ? versions.has(version) : false;
  }
}

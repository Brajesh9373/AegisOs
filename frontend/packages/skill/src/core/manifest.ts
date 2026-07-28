export interface ISkillManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  tags: string[];
  dependencies: string[];
  permissions: string[];
}

export class SkillManifestParser {
  public static parse(raw: unknown): ISkillManifest {
    // In a full implementation, Zod would validate this manifest schema.
    const manifest = raw as ISkillManifest;
    if (!manifest.name || !manifest.version) {
      throw new Error('Invalid manifest: missing name or version');
    }
    return manifest;
  }
}

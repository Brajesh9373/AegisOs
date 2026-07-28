export interface IKnowledgeManifest {
  name: string;
  version: string;
  description: string;
  sourceType: string;
}

export class KnowledgeManifestParser {
  public static parse(raw: unknown): IKnowledgeManifest {
    const manifest = raw as IKnowledgeManifest;
    if (!manifest.name || !manifest.version) {
      throw new Error('Invalid knowledge manifest: missing name or version');
    }
    return manifest;
  }
}

export interface IToolManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  protocols: string[];
}

export class ToolManifestParser {
  public static parse(raw: unknown): IToolManifest {
    const manifest = raw as IToolManifest;
    if (!manifest.name || !manifest.version) {
      throw new Error('Invalid manifest: missing name or version');
    }
    return manifest;
  }
}

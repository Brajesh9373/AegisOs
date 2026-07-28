export interface IMemoryManifest {
  name: string;
  version: string;
  description: string;
  sourceType: string;
}

export class MemoryManifestParser {
  public static parse(raw: unknown): IMemoryManifest {
    const manifest = raw as IMemoryManifest;
    if (!manifest.name || !manifest.version) {
      throw new Error('Invalid memory manifest: missing name or version');
    }
    return manifest;
  }
}

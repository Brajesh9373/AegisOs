export interface ImplementationVersion {
  major: number;
  minor: number;
  patch: number;
  label?: string;
}

export class ImplementationVersioning {
  public parse(version: string): ImplementationVersion {
    const parts = version.split('.');
    return {
      major: parseInt(parts[0] || '1', 10),
      minor: parseInt(parts[1] || '0', 10),
      patch: parseInt(parts[2] || '0', 10),
    };
  }
}

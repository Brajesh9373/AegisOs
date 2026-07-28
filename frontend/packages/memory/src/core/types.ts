export enum MemoryType {
  Working = 'working',
  Session = 'session',
  Episodic = 'episodic',
  Semantic = 'semantic',
  LongTerm = 'long_term',
}

export interface IMemoryTypes {
  getType(): MemoryType;
  isEphemeral(): boolean;
}

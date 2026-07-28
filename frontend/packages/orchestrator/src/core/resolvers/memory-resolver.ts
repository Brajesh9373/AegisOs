export class MemoryResolver {
  public resolveMemory(memoryReference: string): string {
    return `resolved-memory-for-${memoryReference}`;
  }
}

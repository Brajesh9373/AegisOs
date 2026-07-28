export class MemoryPermissionRegistry {
  private permissions = new Map<string, string[]>();

  public grantPermission(memoryId: string, permission: string): void {
    const perms = this.permissions.get(memoryId) || [];
    if (!perms.includes(permission)) {
      perms.push(permission);
      this.permissions.set(memoryId, perms);
    }
  }

  public hasPermission(memoryId: string, permission: string): boolean {
    const perms = this.permissions.get(memoryId) || [];
    return perms.includes(permission);
  }
}

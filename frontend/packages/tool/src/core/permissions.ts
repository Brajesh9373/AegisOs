export class ToolPermissionRegistry {
  private permissions = new Map<string, string[]>();

  public grantPermission(toolId: string, permission: string): void {
    const perms = this.permissions.get(toolId) || [];
    if (!perms.includes(permission)) {
      perms.push(permission);
      this.permissions.set(toolId, perms);
    }
  }

  public hasPermission(toolId: string, permission: string): boolean {
    const perms = this.permissions.get(toolId) || [];
    return perms.includes(permission);
  }
}

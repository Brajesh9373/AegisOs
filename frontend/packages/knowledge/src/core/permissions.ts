export class KnowledgePermissionRegistry {
  private permissions = new Map<string, string[]>();

  public grantPermission(knowledgeId: string, permission: string): void {
    const perms = this.permissions.get(knowledgeId) || [];
    if (!perms.includes(permission)) {
      perms.push(permission);
      this.permissions.set(knowledgeId, perms);
    }
  }

  public hasPermission(knowledgeId: string, permission: string): boolean {
    const perms = this.permissions.get(knowledgeId) || [];
    return perms.includes(permission);
  }
}

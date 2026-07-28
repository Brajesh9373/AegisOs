export class SkillPermissionRegistry {
  private permissions = new Map<string, string[]>();

  public grantPermission(skillId: string, permission: string): void {
    const perms = this.permissions.get(skillId) || [];
    if (!perms.includes(permission)) {
      perms.push(permission);
      this.permissions.set(skillId, perms);
    }
  }

  public hasPermission(skillId: string, permission: string): boolean {
    const perms = this.permissions.get(skillId) || [];
    return perms.includes(permission);
  }

  public getPermissions(skillId: string): string[] {
    return this.permissions.get(skillId) || [];
  }
}

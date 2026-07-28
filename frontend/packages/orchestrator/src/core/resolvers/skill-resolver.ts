export class SkillResolver {
  public resolveSkill(capabilityReference: string): string {
    return `resolved-skill-for-${capabilityReference}`;
  }
}

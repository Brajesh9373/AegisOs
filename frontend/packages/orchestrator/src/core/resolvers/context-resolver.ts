export class ContextResolver {
  public resolveContext(contextReference: string): Record<string, unknown> {
    console.debug(contextReference);
    return {};
  }
}

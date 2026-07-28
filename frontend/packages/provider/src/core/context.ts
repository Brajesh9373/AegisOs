export interface ProviderContext {
  providerId: string;
  variables: Record<string, unknown>;
  state: string;
}

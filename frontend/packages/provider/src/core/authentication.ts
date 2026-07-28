export interface ProviderAuthenticationContract {
  authType: 'apiKey' | 'oauth2' | 'basic' | 'none';
  requiredScopes?: string[];
}

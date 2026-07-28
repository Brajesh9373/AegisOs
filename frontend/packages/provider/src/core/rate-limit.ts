export interface ProviderRateLimitContract {
  requestsPerMinute?: number;
  tokensPerMinute?: number;
  concurrentRequests?: number;
}

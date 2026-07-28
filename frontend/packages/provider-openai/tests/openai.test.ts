import { describe, it, expect } from 'vitest';
import { OpenAIProvider } from '../src/index.js';
import { ProviderLifecycleState } from '@aegisos/provider';

describe('OpenAI Provider', () => {
  it('should initialize with correct category and state', () => {
    const provider = new OpenAIProvider();
    expect(provider.id).toBe('provider-openai');
    expect(provider.state).toBe(ProviderLifecycleState.Registered);
  });

  it('should fail initialization without API key', async () => {
    const provider = new OpenAIProvider();
    await expect(provider.initialize({ options: {} })).rejects.toThrow('OpenAI apiKey is required');
    expect(provider.state).toBe(ProviderLifecycleState.Failed);
  });
});

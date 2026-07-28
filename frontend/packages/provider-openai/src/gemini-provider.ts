import {
  ProviderBase,
  ProviderCategory,
  ProviderCapabilities,
  ProviderConfigurationModel,
  ProviderLifecycleState,
  ProviderHealthContract,
} from '@aegisos/provider';

export class GeminiProvider implements ProviderBase {
  public id: string = 'provider-gemini';
  public name: string = 'Gemini';
  public version: string = '1.0.0';
  public description: string = 'Google Gemini runtime execution provider';
  public category: ProviderCategory = ProviderCategory.AI;
  public state: ProviderLifecycleState = ProviderLifecycleState.Registered;
  public createdAt: string = new Date().toISOString();
  public updatedAt: string = new Date().toISOString();

  private apiKey: string | null = null;
  private config: ProviderConfigurationModel | null = null;

  public capabilities: ProviderCapabilities = {
    supportedFeatures: ['completion', 'chat', 'streaming'],
    supportedActions: ['execute_prompt'],
  };

  public async initialize(config: ProviderConfigurationModel): Promise<void> {
    this.config = config;
    const apiKey = config.options?.apiKey as string;

    if (!apiKey) {
      this.state = ProviderLifecycleState.Failed;
      throw new Error('Gemini apiKey is required');
    }

    this.apiKey = apiKey;
    this.state = ProviderLifecycleState.Initialized;
  }

  public async healthCheck(): Promise<ProviderHealthContract> {
    if (!this.apiKey) {
      return { status: 'down', lastChecked: new Date().toISOString(), latencyMs: 0 };
    }
    try {
      const start = Date.now();
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models?key=${this.apiKey}`,
      );
      if (!res.ok) throw new Error('Health check failed');
      return {
        status: 'healthy',
        lastChecked: new Date().toISOString(),
        latencyMs: Date.now() - start,
      };
    } catch {
      return { status: 'down', lastChecked: new Date().toISOString(), latencyMs: 0 };
    }
  }

  public async executeChat(prompt: string, model: string = 'gemini-1.5-pro'): Promise<string> {
    if (this.state !== ProviderLifecycleState.Initialized || !this.apiKey) {
      throw new Error('Provider not initialized');
    }

    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${this.apiKey}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Gemini API Error: ${response.statusText}`);
      }

      const data = await response.json();
      return data.candidates?.[0]?.content?.parts?.[0]?.text || '';
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      throw new Error(`Gemini execution failed: ${msg}`);
    }
  }

  public async executeChatStream(
    prompt: string,
    _model: string = 'gemini-1.5-pro',
  ): Promise<AsyncIterable<string>> {
    throw new Error('Streaming not yet implemented for Gemini provider via REST');
  }
}

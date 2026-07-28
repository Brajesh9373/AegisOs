import {
  ProviderBase,
  ProviderCategory,
  ProviderCapabilities,
  ProviderConfigurationModel,
  ProviderLifecycleState,
  ProviderHealthContract,
} from '@aegisos/provider';
import OpenAI from 'openai';

// --- Error Mapping ---
export class OpenAIErrorMapper {
  static map(error: unknown): Error {
    if (error instanceof OpenAI.APIError) {
      if (error.status === 401) return new Error('OpenAI Authentication Failed');
      if (error.status === 429) return new Error('OpenAI Rate Limit Exceeded');
      return new Error(`OpenAI API Error: ${error.message}`);
    }
    if (error instanceof Error) {
      return new Error(error.message);
    }
    return new Error('Unknown OpenAI Error');
  }
}

// --- Cost Calculator ---
export class OpenAICostCalculator {
  static calculate(model: string, promptTokens: number, completionTokens: number): number {
    if (model === 'gpt-4-turbo') return (promptTokens * 0.01 + completionTokens * 0.03) / 1000;
    if (model === 'gpt-3.5-turbo')
      return (promptTokens * 0.0005 + completionTokens * 0.0015) / 1000;
    return 0;
  }
}

export class OpenAIProvider implements ProviderBase {
  public id: string = 'provider-openai';
  public name: string = 'OpenAI';
  public version: string = '1.0.0';
  public description: string = 'OpenAI API runtime execution provider';
  public category: ProviderCategory = ProviderCategory.AI;
  public state: ProviderLifecycleState = ProviderLifecycleState.Registered;
  public createdAt: string = new Date().toISOString();
  public updatedAt: string = new Date().toISOString();

  private client: OpenAI | null = null;
  private config: ProviderConfigurationModel | null = null;

  public capabilities: ProviderCapabilities = {
    supportedFeatures: ['completion', 'chat', 'embeddings', 'streaming'],
    supportedActions: ['execute_prompt', 'generate_embeddings'],
  };

  public async initialize(config: ProviderConfigurationModel): Promise<void> {
    this.config = config;
    const apiKey = config.options?.apiKey as string;

    if (!apiKey) {
      this.state = ProviderLifecycleState.Failed;
      throw new Error('OpenAI apiKey is required');
    }

    this.client = new OpenAI({
      apiKey,
      maxRetries: (config.options?.maxRetries as number) || 3, // Retry Policy
    });
    this.state = ProviderLifecycleState.Initialized;
  }

  public async healthCheck(): Promise<ProviderHealthContract> {
    if (!this.client) {
      return { status: 'down', lastChecked: new Date().toISOString(), latencyMs: 0 };
    }
    try {
      const start = Date.now();
      await this.client.models.list();
      return {
        status: 'healthy',
        lastChecked: new Date().toISOString(),
        latencyMs: Date.now() - start,
      };
    } catch {
      return { status: 'down', lastChecked: new Date().toISOString(), latencyMs: 0 };
    }
  }

  public async executeChat(prompt: string, model: string = 'gpt-4-turbo'): Promise<string> {
    if (this.state !== ProviderLifecycleState.Initialized || !this.client) {
      throw new Error('Provider not initialized');
    }

    try {
      const response = await this.client.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
      });
      // Cost calculation could log here based on response.usage
      return response.choices[0]?.message?.content || '';
    } catch (e) {
      throw OpenAIErrorMapper.map(e);
    }
  }

  public async executeChatStream(
    prompt: string,
    model: string = 'gpt-4-turbo',
  ): Promise<AsyncIterable<string>> {
    if (!this.client) throw new Error('Not initialized');

    const stream = await this.client.chat.completions.create({
      model,
      messages: [{ role: 'user', content: prompt }],
      stream: true,
    });

    async function* parseStream() {
      for await (const chunk of stream) {
        yield chunk.choices[0]?.delta?.content || '';
      }
    }
    return parseStream();
  }
}

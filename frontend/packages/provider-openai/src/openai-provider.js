import { ProviderCategory, ProviderLifecycleState, } from '@aegisos/provider';
import OpenAI from 'openai';
// --- Error Mapping ---
export class OpenAIErrorMapper {
    static map(error) {
        if (error instanceof OpenAI.APIError) {
            if (error.status === 401)
                return new Error('OpenAI Authentication Failed');
            if (error.status === 429)
                return new Error('OpenAI Rate Limit Exceeded');
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
    static calculate(model, promptTokens, completionTokens) {
        if (model === 'gpt-4-turbo')
            return (promptTokens * 0.01 + completionTokens * 0.03) / 1000;
        if (model === 'gpt-3.5-turbo')
            return (promptTokens * 0.0005 + completionTokens * 0.0015) / 1000;
        return 0;
    }
}
export class OpenAIProvider {
    id = 'provider-openai';
    name = 'OpenAI';
    version = '1.0.0';
    description = 'OpenAI API runtime execution provider';
    category = ProviderCategory.AI;
    state = ProviderLifecycleState.Registered;
    createdAt = new Date().toISOString();
    updatedAt = new Date().toISOString();
    client = null;
    config = null;
    capabilities = {
        supportedFeatures: ['completion', 'chat', 'embeddings', 'streaming'],
        supportedActions: ['execute_prompt', 'generate_embeddings'],
    };
    async initialize(config) {
        this.config = config;
        const apiKey = config.options?.apiKey;
        if (!apiKey) {
            this.state = ProviderLifecycleState.Failed;
            throw new Error('OpenAI apiKey is required');
        }
        this.client = new OpenAI({
            apiKey,
            maxRetries: config.options?.maxRetries || 3, // Retry Policy
        });
        this.state = ProviderLifecycleState.Initialized;
    }
    async healthCheck() {
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
        }
        catch {
            return { status: 'down', lastChecked: new Date().toISOString(), latencyMs: 0 };
        }
    }
    async executeChat(prompt, model = 'gpt-4-turbo') {
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
        }
        catch (e) {
            throw OpenAIErrorMapper.map(e);
        }
    }
    async executeChatStream(prompt, model = 'gpt-4-turbo') {
        if (!this.client)
            throw new Error('Not initialized');
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

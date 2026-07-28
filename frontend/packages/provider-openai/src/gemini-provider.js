import { ProviderCategory, ProviderLifecycleState, } from '@aegisos/provider';
export class GeminiProvider {
    id = 'provider-gemini';
    name = 'Gemini';
    version = '1.0.0';
    description = 'Google Gemini runtime execution provider';
    category = ProviderCategory.AI;
    state = ProviderLifecycleState.Registered;
    createdAt = new Date().toISOString();
    updatedAt = new Date().toISOString();
    apiKey = null;
    config = null;
    capabilities = {
        supportedFeatures: ['completion', 'chat', 'streaming'],
        supportedActions: ['execute_prompt'],
    };
    async initialize(config) {
        this.config = config;
        const apiKey = config.options?.apiKey;
        if (!apiKey) {
            this.state = ProviderLifecycleState.Failed;
            throw new Error('Gemini apiKey is required');
        }
        this.apiKey = apiKey;
        this.state = ProviderLifecycleState.Initialized;
    }
    async healthCheck() {
        if (!this.apiKey) {
            return { status: 'down', lastChecked: new Date().toISOString(), latencyMs: 0 };
        }
        try {
            const start = Date.now();
            const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${this.apiKey}`);
            if (!res.ok)
                throw new Error('Health check failed');
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
    async executeChat(prompt, model = 'gemini-1.5-pro') {
        if (this.state !== ProviderLifecycleState.Initialized || !this.apiKey) {
            throw new Error('Provider not initialized');
        }
        try {
            const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${this.apiKey}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [{ parts: [{ text: prompt }] }],
                }),
            });
            if (!response.ok) {
                throw new Error(`Gemini API Error: ${response.statusText}`);
            }
            const data = await response.json();
            return data.candidates?.[0]?.content?.parts?.[0]?.text || '';
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            throw new Error(`Gemini execution failed: ${msg}`);
        }
    }
    async executeChatStream(prompt, _model = 'gemini-1.5-pro') {
        throw new Error('Streaming not yet implemented for Gemini provider via REST');
    }
}

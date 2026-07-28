import { ProviderBase, ProviderCategory, ProviderCapabilities, ProviderConfigurationModel, ProviderLifecycleState, ProviderHealthContract } from '@aegisos/provider';
export declare class GeminiProvider implements ProviderBase {
    id: string;
    name: string;
    version: string;
    description: string;
    category: ProviderCategory;
    state: ProviderLifecycleState;
    createdAt: string;
    updatedAt: string;
    private apiKey;
    private config;
    capabilities: ProviderCapabilities;
    initialize(config: ProviderConfigurationModel): Promise<void>;
    healthCheck(): Promise<ProviderHealthContract>;
    executeChat(prompt: string, model?: string): Promise<string>;
    executeChatStream(prompt: string, _model?: string): Promise<AsyncIterable<string>>;
}

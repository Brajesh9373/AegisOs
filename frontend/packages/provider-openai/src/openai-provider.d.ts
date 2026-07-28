import { ProviderBase, ProviderCategory, ProviderCapabilities, ProviderConfigurationModel, ProviderLifecycleState, ProviderHealthContract } from '@aegisos/provider';
export declare class OpenAIErrorMapper {
    static map(error: unknown): Error;
}
export declare class OpenAICostCalculator {
    static calculate(model: string, promptTokens: number, completionTokens: number): number;
}
export declare class OpenAIProvider implements ProviderBase {
    id: string;
    name: string;
    version: string;
    description: string;
    category: ProviderCategory;
    state: ProviderLifecycleState;
    createdAt: string;
    updatedAt: string;
    private client;
    private config;
    capabilities: ProviderCapabilities;
    initialize(config: ProviderConfigurationModel): Promise<void>;
    healthCheck(): Promise<ProviderHealthContract>;
    executeChat(prompt: string, model?: string): Promise<string>;
    executeChatStream(prompt: string, model?: string): Promise<AsyncIterable<string>>;
}

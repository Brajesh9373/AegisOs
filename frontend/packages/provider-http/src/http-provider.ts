import {
  ProviderBase,
  ProviderCategory,
  ProviderCapabilities,
  ProviderConfigurationModel,
  ProviderLifecycleState,
  ProviderHealthContract,
} from '@aegisos/provider';

export interface HttpProviderOptions {
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
  defaultHeaders?: Record<string, string>;
  circuitBreakerThreshold?: number;
}

export interface HttpRequest {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  url: string;
  headers?: Record<string, string>;
  body?: unknown;
  multipart?: boolean;
}

export class HttpProvider implements ProviderBase {
  public id: string = 'provider-http';
  public name: string = 'HTTP Client';
  public version: string = '1.0.0';
  public description: string = 'Generic HTTP Client execution provider';
  public category: ProviderCategory = ProviderCategory.Communication;
  public state: ProviderLifecycleState = ProviderLifecycleState.Registered;
  public createdAt: string = new Date().toISOString();
  public updatedAt: string = new Date().toISOString();

  private options: HttpProviderOptions = {};
  private failureCount = 0;
  private circuitOpen = false;

  public capabilities: ProviderCapabilities = {
    supportedFeatures: [
      'get',
      'post',
      'put',
      'patch',
      'delete',
      'multipart',
      'streaming',
      'authentication',
      'retry',
      'timeout',
      'circuit-breaker',
    ],
    supportedActions: ['execute_request'],
  };

  public async initialize(config: ProviderConfigurationModel): Promise<void> {
    this.options = {
      baseUrl: config.options?.baseUrl as string | undefined,
      timeout: (config.options?.timeout as number) || 10000,
      maxRetries: (config.options?.maxRetries as number) || 3,
      circuitBreakerThreshold: (config.options?.circuitBreakerThreshold as number) || 5,
      defaultHeaders: config.options?.defaultHeaders as Record<string, string> | undefined,
    };
    this.state = ProviderLifecycleState.Initialized;
  }

  public async healthCheck(): Promise<ProviderHealthContract> {
    if (this.circuitOpen) {
      return { status: 'down', lastChecked: new Date().toISOString(), latencyMs: 0 };
    }
    return { status: 'healthy', lastChecked: new Date().toISOString(), latencyMs: 1 };
  }

  private async fetchWithRetry(url: string, init: RequestInit, retries: number): Promise<Response> {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), this.options.timeout);

      const response = await fetch(url, { ...init, signal: controller.signal });
      clearTimeout(id);

      if (!response.ok) {
        if (response.status === 429 && retries > 0) {
          // Rate limit simple backoff
          await new Promise((r) => setTimeout(r, 1000));
          return this.fetchWithRetry(url, init, retries - 1);
        }
        throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
      }
      return response;
    } catch (e: unknown) {
      if (retries > 0) {
        return this.fetchWithRetry(url, init, retries - 1);
      }
      throw e;
    }
  }

  public async executeRequest(req: HttpRequest): Promise<unknown> {
    if (this.state !== ProviderLifecycleState.Initialized) {
      throw new Error('HTTP Provider not initialized');
    }
    if (this.circuitOpen) {
      throw new Error('Circuit Breaker is OPEN');
    }

    const fullUrl = this.options.baseUrl ? `${this.options.baseUrl}${req.url}` : req.url;

    let bodyData: unknown = req.body;
    const headers = { ...this.options.defaultHeaders, ...req.headers };

    if (req.body && !req.multipart && typeof req.body === 'object') {
      bodyData = JSON.stringify(req.body);
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }

    try {
      const response = await this.fetchWithRetry(
        fullUrl,
        {
          method: req.method,
          headers,
          body: ['GET', 'HEAD'].includes(req.method) ? undefined : (bodyData as BodyInit),
        },
        this.options.maxRetries || 0,
      );

      this.failureCount = 0;

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      return await response.text();
    } catch (e: unknown) {
      this.failureCount++;
      if (this.failureCount >= (this.options.circuitBreakerThreshold || 5)) {
        this.circuitOpen = true;
      }
      throw e;
    }
  }

  public async executeStream(req: HttpRequest): Promise<ReadableStream<Uint8Array>> {
    if (this.circuitOpen) throw new Error('Circuit Breaker is OPEN');

    const fullUrl = this.options.baseUrl ? `${this.options.baseUrl}${req.url}` : req.url;
    const response = await fetch(fullUrl, {
      method: req.method,
      headers: { ...this.options.defaultHeaders, ...req.headers },
      body: req.body ? JSON.stringify(req.body) : undefined,
    });

    if (!response.body) throw new Error('No readable stream available');
    return response.body;
  }
}

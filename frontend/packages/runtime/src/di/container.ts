import { PlatformError } from '@aegisos/shared';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export type Token<_T> = symbol | string;

export class DependencyInjectionError extends PlatformError {
  constructor(message: string) {
    super(message, 'DI_ERROR', false);
  }
}

export interface IResolver {
  resolve<T>(token: Token<T>): T;
}

export class Container implements IResolver {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private readonly services = new Map<Token<any>, any>();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private readonly factories = new Map<Token<any>, (resolver: IResolver) => any>();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private readonly instances = new Map<Token<any>, any>();

  public registerValue<T>(token: Token<T>, value: T): void {
    if (this.services.has(token) || this.factories.has(token)) {
      throw new DependencyInjectionError(`Token ${String(token)} is already registered`);
    }
    this.services.set(token, value);
  }

  public registerFactory<T>(
    token: Token<T>,
    factory: (resolver: IResolver) => T,
    singleton = true,
  ): void {
    if (this.services.has(token) || this.factories.has(token)) {
      throw new DependencyInjectionError(`Token ${String(token)} is already registered`);
    }
    this.factories.set(token, (resolver) => {
      if (singleton) {
        if (!this.instances.has(token)) {
          this.instances.set(token, factory(resolver));
        }
        return this.instances.get(token);
      }
      return factory(resolver);
    });
  }

  public resolve<T>(token: Token<T>): T {
    if (this.services.has(token)) {
      return this.services.get(token) as T;
    }
    if (this.factories.has(token)) {
      return this.factories.get(token)!(this);
    }
    throw new DependencyInjectionError(`No provider found for token ${String(token)}`);
  }

  public clear(): void {
    this.services.clear();
    this.factories.clear();
    this.instances.clear();
  }
}

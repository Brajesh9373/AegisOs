export class IDService {
  public generateId(prefix: string): string {
    return `${prefix}_${Math.random().toString(36).substring(2, 9)}`;
  }
}

export class ClockService {
  public now(): Date {
    return new Date();
  }
}

export class EventBusBootstrap {
  private listeners: Map<string, Array<(payload: unknown) => void>> = new Map();

  public subscribe(topic: string, handler: (payload: unknown) => void): void {
    if (!this.listeners.has(topic)) this.listeners.set(topic, []);
    this.listeners.get(topic)!.push(handler);
  }

  public publish(topic: string, payload: unknown): void {
    const handlers = this.listeners.get(topic) || [];
    handlers.forEach((h) => h(payload));
  }
}

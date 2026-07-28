export interface PlatformEvent {
  id: string;
  type: string;
  payload: any;
  timestamp: Date;
}

export type EventHandler = (event: PlatformEvent) => void | Promise<void>;

export class EventBus {
  private static instance: EventBus;
  private subscribers: Map<string, EventHandler[]> = new Map();

  private constructor() {}

  public static getInstance(): EventBus {
    if (!EventBus.instance) {
      EventBus.instance = new EventBus();
    }
    return EventBus.instance;
  }

  public subscribe(eventType: string, handler: EventHandler): void {
    const handlers = this.subscribers.get(eventType) || [];
    handlers.push(handler);
    this.subscribers.set(eventType, handlers);
  }

  public unsubscribe(eventType: string, handler: EventHandler): void {
    const handlers = this.subscribers.get(eventType) || [];
    const index = handlers.indexOf(handler);
    if (index > -1) {
      handlers.splice(index, 1);
    }
    this.subscribers.set(eventType, handlers);
  }

  public async publish(type: string, payload: any): Promise<void> {
    const event: PlatformEvent = {
      id: crypto.randomUUID(),
      type,
      payload,
      timestamp: new Date()
    };
    
    console.log(`[EventBus] Published: ${type}`);
    
    const handlers = this.subscribers.get(type) || [];
    // Also notify wildcards
    const wildcards = this.subscribers.get('*') || [];
    
    const allHandlers = [...handlers, ...wildcards];
    
    // Execute all handlers concurrently without blocking the publisher
    Promise.allSettled(allHandlers.map(handler => handler(event))).catch(err => {
      console.error('[EventBus] Error executing handlers:', err);
    });
  }
}

export const eventBus = EventBus.getInstance();

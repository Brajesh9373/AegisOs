export class EventBus {
    static instance;
    subscribers = new Map();
    constructor() { }
    static getInstance() {
        if (!EventBus.instance) {
            EventBus.instance = new EventBus();
        }
        return EventBus.instance;
    }
    subscribe(eventType, handler) {
        const handlers = this.subscribers.get(eventType) || [];
        handlers.push(handler);
        this.subscribers.set(eventType, handlers);
    }
    unsubscribe(eventType, handler) {
        const handlers = this.subscribers.get(eventType) || [];
        const index = handlers.indexOf(handler);
        if (index > -1) {
            handlers.splice(index, 1);
        }
        this.subscribers.set(eventType, handlers);
    }
    async publish(type, payload) {
        const event = {
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

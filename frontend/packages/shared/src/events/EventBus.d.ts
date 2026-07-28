export interface PlatformEvent {
    id: string;
    type: string;
    payload: any;
    timestamp: Date;
}
export type EventHandler = (event: PlatformEvent) => void | Promise<void>;
export declare class EventBus {
    private static instance;
    private subscribers;
    private constructor();
    static getInstance(): EventBus;
    subscribe(eventType: string, handler: EventHandler): void;
    unsubscribe(eventType: string, handler: EventHandler): void;
    publish(type: string, payload: any): Promise<void>;
}
export declare const eventBus: EventBus;

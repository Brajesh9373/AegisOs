import { DomainEvent } from '@aegisos/contracts';
import { ILogger } from '@aegisos/shared';

export type EventHandler = (event: DomainEvent) => Promise<void>;

export class RuntimeEventBus {
  private handlers = new Map<string, EventHandler[]>();

  constructor(private readonly logger: ILogger) {}

  public subscribe(eventType: string, handler: EventHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }

  public async publish(event: DomainEvent): Promise<void> {
    const handlers = this.handlers.get(event.eventType) || [];
    this.logger.debug(`Publishing event ${event.eventType}`, { eventId: event.eventId });

    // Dispatch concurrently but catch rejections
    await Promise.allSettled(
      handlers.map((h) =>
        h(event).catch((err) => {
          this.logger.error(`Event handler failed for ${event.eventType}`, { error: String(err) });
        }),
      ),
    );
  }
}

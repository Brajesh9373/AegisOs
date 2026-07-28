import { z } from 'zod';

export const DomainEventSchema = z.object({
  eventId: z.string().uuid(),
  eventType: z.string(),
  timestamp: z.string().datetime(),
  correlationId: z.string().uuid().optional(),
  payload: z.record(z.string(), z.unknown()),
});
export type DomainEvent = z.infer<typeof DomainEventSchema>;

export const CommandSchema = z.object({
  commandId: z.string().uuid(),
  commandType: z.string(),
  targetId: z.string().uuid(),
  payload: z.record(z.string(), z.unknown()),
});
export type Command = z.infer<typeof CommandSchema>;

export const ResponseSchema = z.object({
  success: z.boolean(),
  data: z.record(z.string(), z.unknown()).optional(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .optional(),
});
export type Response = z.infer<typeof ResponseSchema>;

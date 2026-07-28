import { z } from 'zod';

export const BaseEntitySchema = z.object({
  id: z.string().uuid().describe('Unique identifier for the entity'),
  createdAt: z.string().datetime().describe('ISO 8601 timestamp of creation'),
  updatedAt: z.string().datetime().describe('ISO 8601 timestamp of last modification'),
});

export type BaseEntity = z.infer<typeof BaseEntitySchema>;

export const MetadataSchema = z
  .record(z.string(), z.unknown())
  .describe('Flexible key-value metadata store');
export type Metadata = z.infer<typeof MetadataSchema>;

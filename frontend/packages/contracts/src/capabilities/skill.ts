import { z } from 'zod';
import { BaseEntitySchema } from '../core/base';

export const JsonSchemaDefinition = z
  .record(z.string(), z.unknown())
  .describe('JSON Schema definition');

export const ToolSchema = BaseEntitySchema.extend({
  name: z.string(),
  version: z.string(),
  description: z.string(),
  inputSchema: JsonSchemaDefinition,
  outputSchema: JsonSchemaDefinition,
  timeoutMs: z.number().int().positive(),
  isIdempotent: z.boolean(),
  approvalRequired: z.boolean().default(false),
});
export type Tool = z.infer<typeof ToolSchema>;

export const SkillSchema = BaseEntitySchema.extend({
  name: z.string(),
  version: z.string(),
  description: z.string(),
  requiredTools: z.array(z.string().uuid()),
  inputSchema: JsonSchemaDefinition,
  outputSchema: JsonSchemaDefinition,
  rollbackStrategy: z.string().optional(),
});
export type Skill = z.infer<typeof SkillSchema>;

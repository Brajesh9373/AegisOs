import { z } from 'zod';
import { BaseEntitySchema } from '../core/base';

export const TraceabilityLinkSchema = BaseEntitySchema.extend({
  correlationId: z.string().uuid(),
  step: z.enum([
    'Requirement',
    'BusinessGoal',
    'Implementation',
    'Workflow',
    'Task',
    'Action',
    'DigitalEmployee',
    'Skill',
    'Tool',
    'Connector',
    'KnowledgeVersion',
    'MemorySnapshot',
    'Evidence',
    'Deliverable',
  ]),
  payloadHash: z.string(),
  timestamp: z.string().datetime(),
});
export type TraceabilityLink = z.infer<typeof TraceabilityLinkSchema>;

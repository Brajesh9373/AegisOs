/**
 * Main export barrel for the @aegisos/types package.
 * Exports pure TypeScript utilities and heavily re-exports core contracts as types.
 */

// Core Utility Types
export * from './utility';

// Monadic Execution Types
export * from './monad';

// We do NOT export implementations or zod schemas from here.
// These are purely type-level aliases for the contracts.
import type {
  AgentRole,
  AgentStatus,
  DigitalEmployee,
  DigitalManager,
  DigitalTeam,
} from '@aegisos/contracts';

import type { ExecutionStatus, Workflow, Task, Action } from '@aegisos/contracts';

import type { Skill, Tool, MemoryAsset, MemoryEpisode } from '@aegisos/contracts';

import type { DomainEvent, Command, Response } from '@aegisos/contracts';

export type {
  AgentRole,
  AgentStatus,
  DigitalEmployee,
  DigitalManager,
  DigitalTeam,
  ExecutionStatus,
  Workflow,
  Task,
  Action,
  Skill,
  Tool,
  MemoryAsset,
  MemoryEpisode,
  DomainEvent,
  Command,
  Response,
};

import { describe, it, expect } from 'vitest';
import {
  KnowledgeStudioService,
  KnowledgeAggregator,
  KnowledgeGraphExplorer,
  KnowledgeLineageService,
  KnowledgeReviewService,
} from '../src/index';
import { SecurityEngine } from '@aegisos/security';

describe('KnowledgeStudioService', () => {
  it('should aggregate studio state when authorized', () => {
    const security = new SecurityEngine();
    const aggregator = new KnowledgeAggregator();
    const explorer = new KnowledgeGraphExplorer();
    const lineage = new KnowledgeLineageService();
    const review = new KnowledgeReviewService();
    const service = new KnowledgeStudioService(security, aggregator, explorer, lineage, review);

    const identity = { userId: 'ka-01', token: 'valid-token', claims: { role: 'KnowledgeAdmin' } };
    const state = service.getStudioState(identity);

    expect(state.knowledgeSources).toBeDefined();
    expect(state.pendingReviews).toBeDefined();
  });
});

export interface EscalationTask {
  id: string;
  sourceContext: string;
  confidenceScore: number;
  aiConfidenceScore?: number;
  status: 'PENDING' | 'IN_PROGRESS' | 'RESOLVED' | 'REJECTED';
  assignedTo?: string;
  resolution?: string;
  createdAt: string;
  updatedAt: string;
}

export interface EscalationResult {
  taskId: string;
  success: boolean;
  knowledgeCandidate?: string;
}

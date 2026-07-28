import { LedgerEntry } from '@aegisos/contracts';
export declare class AuditLedger {
    private ledger;
    record(entry: Omit<LedgerEntry, 'id' | 'previousRecordHash'>): void;
    getLedger(): {
        id: string;
        createdAt: string;
        updatedAt: string;
        who: string;
        when: string;
        why: string;
        inputPayloadHash: string;
        outputPayloadHash: string;
        evidenceSignature: string;
        durationMs: number;
        previousRecordHash: string;
        knowledgeVersionHash?: string | undefined;
        memorySnapshotId?: string | undefined;
        approvalSignature?: string | undefined;
        costTokens?: number | undefined;
    }[];
}

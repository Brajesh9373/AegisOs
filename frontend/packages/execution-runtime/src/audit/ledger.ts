import { LedgerEntry } from '@aegisos/contracts';
export class AuditLedger {
  private ledger: LedgerEntry[] = [];
  record(entry: Omit<LedgerEntry, 'id' | 'previousRecordHash'>) {
    const previousHash =
      this.ledger.length > 0 ? this.ledger[this.ledger.length - 1].inputPayloadHash : 'genesis';
    const fullEntry: LedgerEntry = {
      ...entry,
      id: 'audit-' + Date.now(),
      previousRecordHash: previousHash,
    };
    this.ledger.push(fullEntry);
  }
  getLedger() {
    return this.ledger;
  }
}

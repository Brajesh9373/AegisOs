export class AuditLedger {
    ledger = [];
    record(entry) {
        const previousHash = this.ledger.length > 0 ? this.ledger[this.ledger.length - 1].inputPayloadHash : 'genesis';
        const fullEntry = {
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

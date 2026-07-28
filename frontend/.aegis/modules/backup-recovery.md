# AegisAI Backup & Disaster Recovery Architecture Specification

This document defines the definitive, permanent Backup and Disaster Recovery Architecture for AegisAI. It establishes the rules, cadences, encryption standards, and restoration guarantees required to protect the platform's data against catastrophic failure, ransomware, or operator error.

## 1. Backup Philosophy
A backup that hasn't been tested is merely a theory. In an enterprise system where the Audit Ledger is the single source of legal truth, data loss is a critical failure. Backups must be frequent, immutable, encrypted, and physically isolated from the primary environment.

## 2. Recovery Philosophy
Recovery speed (RTO - Recovery Time Objective) and data freshness (RPO - Recovery Point Objective) dictate the architecture. The platform must be able to failover to a secondary region or restore from a snapshot with deterministic reliability and zero manual schema hacking.

## 3. Objectives
The Backup Architecture must:
* Guarantee zero data loss for the immutable Audit Ledger.
* Provide Point-In-Time Recovery (PITR) for all relational data.
* Ensure backups are protected against tampering or deletion by compromised administrators.
* Automate the verification of backup integrity.

## 4. Backup Strategy
The strategy utilizes a multi-tiered approach: continuous WAL (Write-Ahead Logging) archiving for the primary database, daily full volume snapshots, and hourly incremental syncs for object storage (Knowledge, attachments).

## 5. Recovery Strategy
Recovery playbooks are entirely automated via IaC (Infrastructure as Code) scripts. A restoration provisions a clean database instance, applies the latest full snapshot, and rolls forward the WAL logs to the exact second of failure.

## 6. Snapshot Strategy
Full environment snapshots (Database + Object Storage state) are taken every 24 hours. These are stored in a WORM (Write Once, Read Many) compliant storage bucket.

## 7. Incremental Backups
To minimize RPO, PostgreSQL WAL files are streamed continuously to secure object storage. This allows recovery up to the exact moment a crash occurred.

## 8. Full Backups
A full logical dump (`pg_dump`) is executed weekly to protect against block-level corruption that might be replicated in volume snapshots.

## 9. Restore Process
1. Administrator triggers the `RestoreEnvironment` runbook.
2. The infrastructure orchestration pulls the last known good snapshot.
3. WAL logs are replayed.
4. Data integrity checks run automatically.
5. The API containers boot and connect to the restored data plane.

## 10. Recovery Verification
A successful backup is verified by automatically restoring it into an ephemeral, isolated testing namespace, running a suite of synthetic API tests, and tearing down the namespace. If the tests fail, the backup is marked as invalid, and an urgent `SecurityAlert` is fired.

## 11. Point In Time Recovery
Administrators can restore the database to an exact timestamp (e.g., "Restore to 2026-06-30 14:02:15 UTC"). This is critical for recovering from an accidental mass-deletion (e.g., dropping a Department).

## 12. Configuration Backup
Because AegisAI settings are stored as versioned JSON in the database, they are inherently protected by the DB backup strategy.

## 13. License Backup
License payloads and root encryption keys must be backed up securely in a cold-storage vault (e.g., AWS Secrets Manager or a physical hardware security module for air-gapped deployments).

## 14. Agent Backup
Agent configurations, Prompts, and attached Skill manifests are fully captured in the standard database backup.

## 15. Knowledge Backup
The actual vector embeddings and the raw source files (PDFs, docs) residing in Object Storage are versioned and replicated cross-region. 

## 16. Memory Backup
Agent episodic memory is backed up synchronously with the relational database to prevent "split-brain" scenarios where an Agent remembers a Task that no longer exists in the restored DB.

## 17. Audit Backup
The Audit Ledger is the most critical asset. It is backed up using continuous replication to a physically separate, hyper-secure storage account where even the root AWS/Cloud admin cannot delete the files before a 7-year retention policy expires.

## 18. Encryption
All backups must be encrypted at rest using a dedicated, isolated KMS key (e.g., AES-256). The backup encryption key must never reside on the same server as the primary database.

## 19. Integrity Verification
Every backup artifact (snapshot, WAL file, logical dump) must have an SHA-256 checksum calculated and stored independently. Before restoration, the checksum must be verified to detect silent corruption or tampering.

## 20. Retention
Backups follow a Grandfather-Father-Son (GFS) retention schedule. 
* Daily backups kept for 30 days.
* Weekly backups kept for 12 weeks.
* Monthly backups kept for 7 years (Audit compliance).

## 21. Disaster Recovery
For High Availability (HA) deployments, asynchronous replication is maintained to a secondary geographic region (e.g., `us-east-1` to `us-west-2`). In a total region loss, DNS is swung to the secondary region.

## 22. Business Continuity
During a DR failover, the system may run in a degraded state (e.g., background asynchronous integrations paused) until the primary region is restored, but core Agent logic and Audit logging must remain active.

## 23. Testing Strategy
A full Disaster Recovery drill must be executed and formally signed off by the Operations team at least once per quarter.

## 24. Monitoring
The Backup Engine exposes metrics. If a scheduled backup fails, or if WAL streaming lags by more than 5 minutes, a Critical alert is dispatched.

## 25. Audit
The act of taking a backup, restoring a backup, or modifying the backup schedule is an ultra-high-privilege action that is permanently logged in the Audit Ledger.

## 26. Future Expansion
The architecture supports the future addition of decentralized backup storage (e.g., IPFS/Filecoin) for extreme cryptographic durability.

## 27. Permanent Constraints
* Data loss is unacceptable; architecture must support sub-minute RPO.
* Automated backup verification is mandatory.
* Quarterly recovery testing is mandatory.
* All backups must be heavily encrypted.
* The Audit ledger's backup must be physically immutable (WORM).

---

## Never Do

* **Never** store backup artifacts on the same physical volume, server, or SAN as the primary database.
* **Never** rely on a backup that hasn't been mathematically verified (checksummed) and functionally verified (restored in an ephemeral environment).
* **Never** delete old backups manually; retention must be enforced by automated, immutable lifecycle policies at the storage layer.
* **Never** allow the API or Task Engine to mutate the database schema if the pre-migration backup snapshot fails.
* **Never** use the same encryption key for live production data and cold-storage backups.

---

## Backup & Recovery Constitution
The permanent Backup & Recovery principles of AegisAI:
1. **The Principle of Pessimism**: Assume the database will corrupt, the datacenter will burn, and the admin will make a mistake. Build the net before walking the tightrope.
2. **The Principle of Proof**: A backup does not exist until you have restored from it successfully.
3. **The Principle of Immutability**: A backup is history, and history cannot be rewritten. A compromised system must never have the physical permission to delete its own backups.

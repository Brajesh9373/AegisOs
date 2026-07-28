"""Golden exemplar — the Microsoft-approved reference output.

This is the exact FINALIZED_REQUIREMENTS object from the approved frontend mock
(NewProject.tsx, the Adrenaline->Frappe HR migration scenario). It is embedded in
the finalize prompt as the calibration example the model imitates: the structure,
depth, and tone of every field is anchored to what was approved. Content changes
per project; this shape does not.
"""

from __future__ import annotations

# The approved finalized requirements — the golden output shape.
GOLDEN_FINALIZED = {
    "projectName": "Adrenaline to Frappe HR Migration",
    "objective": "Migrate HR system from Adrenaline to self-hosted Frappe HR on GCP with real-time MySQL sync and mobile rollout for 2000+ field employees",
    "functionalReqs": [
        "Migrate 3 years of master data (employee records, designations, locations)",
        "Migrate transactional data (attendance, leave history, payroll summaries)",
        "Real-time bidirectional sync between Frappe HR and MySQL master database",
        "Update GCP Pub/Sub pipeline to route HR data through Frappe HR",
        "Deploy Frappe HR mobile app for field employees (2000+ users)",
        "Webhook integration from Frappe HR to in-house Mongo monitoring tool",
    ],
    "techStack": ["Frappe HR", "MySQL", "GCP Pub/Sub", "MongoDB", "Frappe Mobile App", "Python", "Node.js"],
    "skills": ["Frappe/ERPNext", "Database Migration", "GCP", "Real-time Sync", "Mobile Deployment", "Data Pipeline"],
    "connectors": ["GCP Pub/Sub", "MySQL", "MongoDB", "Frappe HR API", "Webhooks"],
    "governance": [
        {"label": "Data Privacy", "detail": "All employee PII must be encrypted at rest (AES-256) and in transit (TLS 1.3). GDPR-compliant data handling for employee records."},
        {"label": "Access Control", "detail": "RBAC enforced — only HR Admins can modify migration mappings. Audit trail for all data access and configuration changes."},
        {"label": "Approval Workflow", "detail": "Each migration phase requires sign-off from Engineering Lead, HR Director, and CTO before proceeding to next phase."},
        {"label": "Compliance", "detail": "SOC2 Type II controls applied. Employee data retention policies enforced. Right-to-deletion requests handled during migration."},
        {"label": "Change Management", "detail": "All schema changes require RFC document. Migration scripts peer-reviewed by 2 engineers before execution."},
    ],
    "guardrails": [
        {"label": "Data Validation", "detail": "Pre-migration checksums on all 450 tables. Post-migration row count + sample data verification. Automated field mapping validation."},
        {"label": "Rollback Procedure", "detail": "Point-in-time recovery snapshots before each phase. If migration fails validation, automatic rollback to last known good state within 15 minutes."},
        {"label": "Sync Safety", "detail": "MySQL sync uses idempotent writes. Conflict resolution: Frappe HR wins on HR fields, MySQL wins on transaction fields. Dead-letter queue for failed syncs."},
        {"label": "Rate Limiting", "detail": "Migration batch size capped at 1000 records/sec. GCP Pub/Sub flow control enabled. API rate limits enforced on Frappe HR endpoints."},
        {"label": "Monitoring Alerts", "detail": "PagerDuty alerts for: sync lag > 5s, migration failure rate > 1%, data validation mismatches, Frappe HR health check failures."},
        {"label": "Cutover Safety", "detail": "Adrenaline runs in read-only mode for 7 days post-cutover. Dual-write period ensures no data loss. Emergency rollback plan documented."},
    ],
    "infrastructure": [
        {"label": "Compute", "detail": "Frappe HR: GKE Autopilot cluster (2-6 nodes, e2-standard-4). Migration workers: Cloud Run jobs (2 vCPU, 4GB RAM, max 10 instances)."},
        {"label": "Database", "detail": "Frappe HR DB: Cloud SQL PostgreSQL (db-custom-4-16384, HA). MySQL master: existing Cloud SQL instance. Read replicas for migration validation."},
        {"label": "Networking", "detail": "VPC peering between Frappe HR and existing MySQL. Private Service Connect for Cloud SQL. Internal load balancer for Frappe HR API."},
        {"label": "Storage", "detail": "GCS bucket for migration artifacts and backups. Cloud Storage for Frappe HR file attachments. Lifecycle policy: 90-day retention for migration logs."},
        {"label": "Messaging", "detail": "GCP Pub/Sub: 3 topics (hr-events, sync-status, migration-progress). Dead-letter topics with 7-day retention. Kafka for legacy pipeline bridge."},
        {"label": "Monitoring", "detail": "Cloud Monitoring dashboards for sync latency, migration progress, error rates. Cloud Logging for audit trail. Grafana for custom Frappe HR metrics."},
    ],
    "risks": [
        "Data loss during migration if field mappings between Adrenaline and Frappe are incorrect",
        "Frappe HR mobile app may not support all custom Adrenaline workflows",
        "Real-time sync complexity with 450+ MySQL tables",
        "Phased rollout requires maintaining both systems in parallel",
    ],
    "phases": [
        {"name": "Phase 1 — Engineering Dept", "duration": "Month 1", "description": "Migrate Engineering department data, set up Frappe HR instance, configure MySQL sync"},
        {"name": "Phase 2 — Field Operations", "duration": "Month 2", "description": "Migrate field operations data, deploy mobile app, update Pub/Sub pipeline"},
        {"name": "Phase 3 — Full Cutover", "duration": "Month 3", "description": "Complete migration, decommission Adrenaline, enable webhooks to Mongo tool"},
    ],
}

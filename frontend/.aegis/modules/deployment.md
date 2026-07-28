# AegisAI Deployment Architecture Specification

This document defines the definitive, permanent Deployment Architecture for AegisAI. It establishes the rules, strategies, and operational constraints for hosting, scaling, and maintaining the platform in customer-owned environments.

## 1. Deployment Philosophy
AegisAI is a self-hosted, enterprise-grade platform. The deployment architecture is designed to be agnostic to the underlying infrastructure, provided the environment meets baseline containerization and storage requirements. Predictability, fault tolerance, and data sovereignty are paramount.

## 2. Self Hosted Architecture
The platform is shipped entirely as a suite of OCI-compliant container images (Docker). AegisAI does not provide SaaS hosting for the core platform. The customer runs the containers in their own VPC, on their own metal, or in their chosen cloud provider.

## 3. Single Node Deployment
Designed for PoCs, small teams, or development. All services (API, Task Engine, Database, Message Broker, Redis) run on a single host via `docker-compose`.

## 4. Multi Node Deployment
Designed for standard production. Application logic (stateless) is separated from data persistence (stateful). Traffic is routed via a load balancer.

## 5. HA Deployment
High Availability deployment. Multiple stateless application replicas operate across multiple availability zones. Databases and message brokers run in clustered, replicated configurations to eliminate single points of failure.

## 6. Docker Strategy
Every component of AegisAI must be fully containerized. Base images must be minimal (e.g., Alpine or Distroless) and free of known CVEs. Containers must run as non-root users.

## 7. Kubernetes Strategy
Kubernetes (K8s) is the recommended orchestrator for Enterprise and HA deployments. AegisAI provides official Helm charts that define Deployments, StatefulSets, Services, Ingress, and NetworkPolicies.

## 8. Storage Strategy
* **Relational Data**: PostgreSQL is the permanent standard for structured transactional data.
* **Vector Data**: pgvector or a dedicated Milvus/Qdrant instance for semantic embeddings.
* **Blob/File Storage**: S3-compatible object storage (AWS S3, MinIO for on-prem) for attachments, Knowledge artifacts, and logs.

## 9. Database Strategy
The database schema is managed exclusively by the core application via automated, transactional migrations. External DB mutation is strictly prohibited.

## 10. Backup Strategy
Automated, encrypted backups of PostgreSQL and Object Storage must occur daily (at minimum). Point-In-Time-Recovery (PITR) via WAL archiving is strongly recommended for HA deployments.

## 11. Restore Strategy
Disaster recovery playbooks must be tested quarterly. Restoring from a backup must not require manual schema interventions.

## 12. Upgrade Strategy
Upgrades are performed via immutable image tag updates. Database migrations run automatically during the pre-boot phase of the new API container. If multiple API containers exist (HA), migrations must employ locking to prevent race conditions.

## 13. Rollback Strategy
Since database migrations are often one-way, rollback requires restoring the database from the pre-upgrade snapshot and reverting the container image tags. *Always backup before upgrading.*

## 14. Configuration Management
Configuration strictly follows the 12-Factor App methodology. All configuration is injected via Environment Variables or mounted ConfigMaps. Configuration is never baked into the container image.

## 15. Secrets Management
Secrets (API keys, DB passwords, private keys) must be injected securely at runtime via Kubernetes Secrets, HashiCorp Vault, or AWS KMS/Secrets Manager.

## 16. Environment Management
Deployment supports logical isolation (e.g., Dev, Staging, Prod) through standard CI/CD pipelines and isolated Kubernetes namespaces or discrete AWS accounts.

## 17. Monitoring
The platform exposes `/metrics` endpoints in Prometheus format. Application performance, queue depths, and LLM latency must be continuously monitored.

## 18. Logging
Containers output structured JSON logs to `stdout`/`stderr`. Logs are aggregated by the customer's centralized logging stack (e.g., ELK, Datadog, Splunk).

## 19. Health Checks
All services expose `/health/liveness` (is the process running?) and `/health/readiness` (can it connect to the DB and serve traffic?) endpoints for orchestrator routing.

## 20. Scaling
Application containers (API, Task Engine workers) scale horizontally. Scaling is triggered by CPU utilization or queue depth metrics (e.g., KEDA in Kubernetes).

## 21. Disaster Recovery
HA deployments must span multiple physical failure domains (Zones). For absolute mission-critical deployments, active-passive cross-region replication is supported at the storage layer.

## 22. Business Continuity
The platform supports graceful degradation. If an external AI provider goes down, the Task Engine queues the work and the UI alerts the user, but the core system does not crash.

## 23. Air Gapped Deployment
AegisAI can run entirely disconnected from the internet. Container images, model weights, and license files are transferred via secure media to the isolated environment.

## 24. Offline Deployment
Similar to Air Gapped, this requires localized LLMs (e.g., via Ollama/vLLM) running on internal GPU nodes, as external APIs (OpenAI/Anthropic) are unreachable.

## 25. License Server Integration
For online deployments, the platform pings `license.aegisai.com` to validate entitlements. For offline deployments, a signed physical key file is mounted into the container.

## 26. Future Expansion
The architecture supports the future addition of multi-cluster federation for global enterprises requiring data residency compliance across multiple continents.

## 27. Permanent Constraints
* All application services must be 100% stateless.
* Configuration must live strictly outside of code.
* Upgrades must never result in data loss.
* Backups must be taken immediately before any schema migration.

---

## Enterprise Deployment Examples

**Standard Cloud Native (AWS EKS):**
* **Compute**: EKS Cluster across 3 AZs.
* **Database**: Amazon Aurora PostgreSQL (Multi-AZ).
* **Storage**: Amazon S3.
* **Cache/Broker**: Amazon ElastiCache (Redis).
* **Ingress**: AWS ALB routing to Nginx Ingress.
* **Secrets**: AWS Secrets Manager mapped to K8s External Secrets.

**Strict Air-Gapped On-Premises:**
* **Compute**: VMWare Tanzu or Rancher on bare metal in a SCIF.
* **Database**: Clustered PostgreSQL with Patroni.
* **Storage**: MinIO cluster.
* **Cache/Broker**: Clustered Redis.
* **AI Provider**: Internal vLLM farm running Llama-3 on Nvidia H100s.
* **License**: Offline `.key` file uploaded via administrator portal.

---

## Never Do

* **Never** store state (files, session data, local SQLite databases) inside an application container's writable layer. Containers must be disposable.
* **Never** bake secrets, passwords, or customer-specific configurations into a Docker image.
* **Never** run a schema migration against a production database without taking a snapshot immediately prior.
* **Never** expose the PostgreSQL database, Redis instance, or internal Event Bus directly to the public internet.
* **Never** run application containers as the `root` user.
* **Never** allow the API or Task Engine to boot if the configured License payload is invalid or missing.

---

## Deployment Constitution
The permanent Deployment principles of AegisAI:
1. **Infrastructure Agnosticism**: AegisAI dictates the architecture, but the customer chooses the metal. The platform must run as smoothly on bare metal as it does in AWS.
2. **Immutability**: A deployed artifact is never changed. To change behavior, change the configuration or deploy a new versioned artifact.
3. **Data Sovereignty**: The deployment architecture exists to keep the customer's data within their absolute control. We provide the engine; they own the garage.

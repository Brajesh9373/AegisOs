# AegisAI Docker & Container Architecture Specification

This document defines how the AegisAI platform is containerized, networked, and deployed. It establishes the physical execution boundaries that guarantee the system remains portable, scalable, and secure across any environment—from a developer's laptop to an air-gapped enterprise cluster.

---

## 1. Container Philosophy
Containers are the atomic unit of deployment. They must be treated as ephemeral, disposable computing instances. A container can be killed at any moment; the system must survive. State is never trusted to a container's internal filesystem.

## 2. Deployment Objectives
*   Provide a single, unified deployment mechanism (Docker/OCI) across all environments.
*   Ensure the platform can run 100% offline (air-gapped) without external internet dependencies.
*   Enforce absolute network isolation between the public web and internal databases.
*   Allow horizontal scaling of heavy background workers independently of the API.

## 3. Container Architecture
AegisAI employs a microservice-inspired container architecture, despite operating from a monorepo. The system is split by *runtime responsibility*, not by domain logic.

## 4. Monorepo Container Strategy
A single Docker image (the "AegisCore" image) is built from the Node.js backend monorepo. The specific role the container plays (API, Worker, or Scheduler) is dictated purely by the `CMD` override and environment variables passed at runtime. This drastically reduces build times and registry storage.

## 5. Application Containers
Stateless execution environments running the compiled TypeScript application code. They depend entirely on external volumes or services for persistence.

## 6. API Container
*   **Responsibility:** Serves synchronous HTTP REST requests from the Frontend and external integrations.
*   **Network:** Receives traffic from the Reverse Proxy. Communicates with Database, Redis, and Object Storage.
*   **Scaling:** Horizontally scaled based on HTTP request volume.

## 7. Web Container
*   **Responsibility:** Serves the Next.js React frontend (Server-Side Rendering).
*   **Network:** Receives traffic from the Reverse Proxy. Communicates with the API Container (server-to-server).
*   **Scaling:** Horizontally scaled based on user traffic.

## 8. Worker Container
*   **Responsibility:** Executes asynchronous background jobs (AI Task orchestration, Vector Embedding).
*   **Network:** No inbound HTTP traffic. Long-polls Redis/RabbitMQ. Communicates with Database and external LLM Providers.
*   **Scaling:** Heavily horizontally scaled. Auto-scales based on queue depth.

## 9. Scheduler Container
*   **Responsibility:** Triggers cron-based jobs (e.g., hourly database backups, daily quota resets).
*   **Network:** Communicates with Redis/RabbitMQ.
*   **Scaling:** **Strictly Single-Instance**. Running multiple schedulers causes duplicate cron executions.

## 10. Database Container
*   **Responsibility:** PostgreSQL instance running `pgvector`.
*   **Network:** Strictly internal. Only accessible by API and Worker containers.
*   **Storage:** Binds to `pg_data` persistent volume.

## 11. Redis Container
*   **Responsibility:** In-memory caching, session storage, and BullMQ job queues.
*   **Network:** Strictly internal.
*   **Storage:** Binds to `redis_data` for AOF (Append Only File) persistence.

## 12. Reverse Proxy Container
*   **Responsibility:** NGINX or Traefik. Handles TLS termination, routes `/api` to the API container, and `/` to the Web container.
*   **Network:** The *only* container exposing ports (80/443) to the host machine.

## 13. Monitoring Containers
Prometheus (Metrics scraping) and Grafana (Dashboards). Run on an isolated internal network segment.

## 14. Logging Containers
Promtail/FluentD (Log collection) and Loki/Elasticsearch (Log aggregation). Taps into the Docker daemon's `json-file` logging driver.

## 15. Object Storage Strategy
In cloud environments, AWS S3 is used. For self-hosted/air-gapped deployments, a MinIO container is deployed to provide an S3-compatible API backed by a persistent volume.

---

## Networking & Security

## 16. Internal Networking
Containers are joined to an isolated bridge network (e.g., `aegis_backend`). Containers reference each other via internal DNS (e.g., `postgres:5432`).

## 17. External Networking
All external traffic is funneled through the Reverse Proxy. Internal containers do not map ports to the host (`-p 3000:3000` is forbidden for backend services in production).

## 18. DNS Strategy
Docker's internal DNS resolver is used for service-to-service discovery.

## 19. Service Discovery
Services are discovering via static hostnames defined in the deployment manifest (Compose/Kubernetes).

## 20. Environment Configuration
Configuration is passed exclusively via environment variables (`.env` files or Kubernetes ConfigMaps).

## 21. Secrets Management
Passwords, API Keys, and JWT Secrets must not be stored in environment variables visible to `docker inspect`. They must be mounted into the container's memory space using Docker Secrets or a Kubernetes Secrets controller.

---

## Storage & Resources

## 22. Persistent Volumes
Stateful containers (Database, Redis, MinIO) must use named Docker Volumes or Kubernetes PersistentVolumeClaims (PVCs). Host-path binds (`-v /opt/data:/var/lib/postgresql/data`) are discouraged in production due to permission edge cases.

## 23. Backup Volumes
A dedicated volume mapped to the Database container for storing daily `pg_dump` archives.

## 24. Shared Volumes
If Workers need to share temporary files before uploading to Object Storage, a shared `tmp` volume is mounted across all Worker instances.

## 25. Resource Allocation
Every container must have explicit CPU and Memory limits defined to prevent a runaway AI Worker from starving the Database container.

## 26. CPU Strategy
Workers performing heavy OCR or local embedding generation are pinned to specific CPU cores or given high CPU shares.

## 27. Memory Strategy
Node.js containers are configured with `--max-old-space-size` matching their container memory limit to prevent OOM Kills. Database containers are allocated 50% of total host RAM.

---

## Scaling & Lifecycle

## 28. Horizontal Scaling
Workers and Web containers scale simply by spinning up more instances.

## 29. Vertical Scaling
The Database container is scaled vertically (adding more RAM/CPU to the host node) before attempting complex replication.

## 30. High Availability
Requires Kubernetes or Docker Swarm. Services are spread across multiple physical Availability Zones.

## 31. Rolling Updates
Deployment manifests must specify update policies (e.g., `start-first`, `max-surge: 1`) to ensure zero-downtime upgrades.

## 32. Health Checks
Every container has a mandatory `HEALTHCHECK` directive. The API container exposes `/api/v1/health`. If it fails, the orchestrator restarts it.

## 33. Startup Order
Orchestrators must respect dependency order using `depends_on: condition: service_healthy`.
Order: Database/Redis -> Migrations (Ephemeral Container) -> API -> Workers/Web.

## 34. Restart Policy
Production containers use `restart: always` or `unless-stopped`.

## 35. Crash Recovery
Stateless containers recover instantly on restart. BullMQ ensures interrupted jobs are retried by surviving Workers.

---

## Image Management & Deployment

## 36. Image Versioning
Images are tagged with semantic versions (e.g., `v1.2.4`) and the git commit hash (`sha-a1b2c3d`).

## 37. Image Tagging
The `latest` tag is forbidden in production manifests to ensure deterministic rollbacks.

## 38. Registry Strategy
Images are stored in an enterprise private registry (e.g., GitHub Container Registry, AWS ECR).

## 39. Multi Architecture Images
Build pipelines produce `linux/amd64` and `linux/arm64` images to support Intel and Apple Silicon/AWS Graviton deployments.

## 40. Air-Gapped Deployment
For highly secure environments, all images and dependencies are packed into a single `.tar` archive, physically transferred via USB, and loaded using `docker load`.

## 41. Offline Deployment
The platform must function without contacting the public internet, relying on local embedding models and local MinIO storage.

## 42. Enterprise Deployment
Deployed via Helm charts to an existing corporate Kubernetes cluster.

## 43. Development Environment
Deployed via `docker-compose.dev.yml`, mapping local source code into the containers for hot-reloading.

## 44. Staging Environment
A precise mirror of production, scaled down to 1 instance per service.

## 45. Production Environment
Multi-node, horizontally scaled, tightly monitored.

## 46. Upgrade Strategy
Database migrations are run via a standalone, ephemeral container *before* the new API/Worker images are rolled out.

## 47. Rollback Strategy
Revert the deployment manifest to the previous Image Tag. Note: Database rollbacks require manual DBA intervention via PITR.

## 48. Disaster Recovery
If the cluster burns down, spinning up a new cluster using the persistent volume backups (S3 `pgBackRest`) guarantees recovery within RTO limits.

## 49. Security Best Practices
*   Containers run as non-root users (`USER node`).
*   Read-only root filesystems where possible.
*   No shell access (`docker exec`) permitted in production without Audit logging.

## 50. Future Expansion
Support for dynamic provisioning of isolated sandboxes (Firecracker MicroVMs) for executing untrusted Python code generated by the AI.

## 51. Permanent Constraints
*   One responsibility per container.
*   Stateless application containers.
*   Persistent data outside containers.
*   Images are immutable.
*   Secrets never baked into images.
*   Environment driven configuration.
*   Health checks mandatory.
*   No direct database exposure.
*   Internal communication only.
*   Secure by default.
*   Self-hosted first.

---

## Deployment Examples

### Local Development
Developer runs `docker compose up`. Hot-reloading enabled. Postgres and Redis run locally. Web UI runs on `localhost:3000`.

### Small Business
Single powerful VM (e.g., 8-core, 32GB RAM). Runs `docker-compose.prod.yml`. Reverse proxy handles SSL. MinIO handles file storage locally.

### Enterprise Production
Deployed to AWS EKS (Kubernetes). Application containers run on stateless spot instances. Postgres is outsourced to AWS RDS. Redis is outsourced to ElastiCache. Object storage is AWS S3.

### High Availability
Multi-region Kubernetes deployment. Active-Active API gateways. Active-Passive cross-region database replication.

---

## Container Dependency Diagram
```text
[Reverse Proxy]
      │
      ├─► [Web Container] (Next.js)
      │
      └─► [API Container] (NestJS) ──────┐
               │                         │
               ▼                         ▼
        [Redis Container]        [Postgres Container]
               ▲                         ▲
               │                         │
        [Worker Container] ──────────────┘
        [Scheduler Container]
```

## Network Diagram
```text
Public Internet (0.0.0.0)
       │
      443
       ▼
[ Reverse Proxy ] (Only container attached to Host Network Bridge)
       │
   (Isolated Internal Network: aegis_net)
       │
       ├─► [Web]
       ├─► [API]
       │    │
       │    ├─► [Postgres] (No external IP)
       │    ├─► [Redis]    (No external IP)
       │    └─► [MinIO]    (No external IP)
       │
       └─► [Workers] (Outbound internet access to LLM APIs only)
```

## Deployment Topology
*   **Edge:** Reverse Proxy
*   **Presentation Tier:** Web Containers
*   **Logic Tier:** API & Worker Containers
*   **Data Tier:** Postgres, Redis, MinIO

## Scaling Topology
*   **Web/API/Workers:** Scale Out (Add more instances based on CPU/Queue metrics).
*   **Scheduler:** Do Not Scale (Must remain 1 instance).
*   **Database/Redis:** Scale Up (Add more RAM/CPU).

## Recovery Strategy
1.  Host failure detected.
2.  Orchestrator schedules containers on a healthy node.
3.  Containers pull configuration from environment.
4.  Database container re-attaches to network-attached persistent storage.
5.  System resumes processing.

---

## Docker Architecture Constitution
The permanent Container principles of AegisAI:
1. **The Principle of Ephemerality**: Any container must be able to be instantly destroyed without warning and without data loss. The platform lives in the volumes, not the containers.
2. **The Principle of Isolation**: A compromised Web or API container must never grant lateral access to the Host OS or the raw Database files.
3. **The Principle of Portability**: The exact same Docker image tested on the developer's laptop is the exact same binary hash deployed to the production enterprise cluster. Build once, deploy anywhere.

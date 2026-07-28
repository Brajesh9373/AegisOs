# Knowledge Graph V2 operations

## Architecture

FalkorDB remains the source of truth. Successful graph mutations enqueue a
coalesced Redis Streams job. The dedicated `knowledge-snapshot-worker` writes
immutable Apache Arrow point/link files to MinIO/S3 and atomically activates
their PostgreSQL metadata. FastAPI streams those immutable files; the browser
lazy-loads Arrow and Cosmos.gl only when the Knowledge tab uses V2.

## Deployment

1. Set unique production secrets for `POSTGRES_PASSWORD`,
   `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, and
   `GRAFANA_ADMIN_PASSWORD`. Set an explicit `ECMS_CORS_ALLOW_ORIGINS`.
2. Check out the exact Git commit or release tag to deploy. Application images
   are built from that local revision with `docker compose ... up -d --build`.
   Set every `*_IMAGE` variable required by `docker-compose.prod.yml` to an
   image reference pinned by digest; production Compose intentionally rejects
   unconfigured dependency images and does not use `latest`.
3. Deploy the backend image containing migration `0039`.
4. Configure the backend and snapshot worker with the same:
   `ECMS_DATABASE_URL`, `ECMS_REDIS_URL`, `ECMS_FALKORDB_URL`,
   `ECMS_S3_ENDPOINT_URL`, `ECMS_S3_BUCKET`, `ECMS_S3_ACCESS_KEY`, and
   `ECMS_S3_SECRET_KEY`.
   `ECMS_S3_PUBLIC_ENDPOINT_URL` must be a browser-reachable, TLS-protected
   S3 or CDN origin that preserves signed query strings. The local stack uses
   an Nginx immutable-object cache; production should use the organization's
   managed CDN/object endpoint.
5. Run the `minio-init` one-shot service.
6. Start `backend` and `knowledge-snapshot-worker`.
7. Keep `ECMS_KNOWLEDGE_GRAPH_RENDERER=d3` for the initial production rollout.
8. As an administrator, call `POST /api/knowledge-graph/v2/rebuild`.
9. Confirm `GET /api/knowledge-graph/v2/status` reports a current version,
   healthy artifacts, and at least one active worker.
10. Set `ECMS_KNOWLEDGE_GRAPH_RENDERER=cosmos` and restart only the backend when
   the organization is approved for V2.

The initial Cosmos cohort is controlled by
`ECMS_KNOWLEDGE_GRAPH_COSMOS_ROLES` and defaults to administrator roles. Expand
the comma-separated role list in stages; use `*` only after the observation
window succeeds.

## Rollback

Set `ECMS_KNOWLEDGE_GRAPH_RENDERER=d3` and restart the backend. The existing
`/legacy-graph/data` route and D3 renderer remain intact, so rollback requires
no snapshot deletion, data migration, frontend rebuild, or FalkorDB change.

If a snapshot build fails, do not delete the current record or current objects.
The service retains and serves the last ready snapshot while exposing the newer
failed/building state in the manifest.

## Health and incident checks

- `/health`: API process health.
- `/api/knowledge-graph/v2/status`: queue pending count, active worker
  heartbeats, current version, counts, and MinIO object-size validation.
- `/api/knowledge-graph/v2/manifest`: client-visible ready/building/stale state.
- Worker logs: one completion or bounded failure sequence per organization.
- Redis stream: `ecms:knowledge-graph:snapshot-jobs`.

For Redis or MinIO outages, leave the last ready PostgreSQL pointer unchanged,
restore the dependency, and trigger one administrator rebuild. Do not purge the
stream: consumer-group recovery claims abandoned messages after the idle
threshold.

## Capacity and retention

The measured supported client target is 100,000 nodes / 200,000 edges on the
agreed hardware profile. The current 17,637-node snapshot became interactive in
2.36 seconds through the rebuilt production frontend. See
`knowledge-graph-v2-benchmark.md` for the benchmark method and GPU caveats.
The API publishes this limit in the manifest. The browser rejects snapshots
above the declared ceiling before downloading their artifacts, preventing an
unqualified dataset from exhausting browser or GPU memory. Raising the two
`ECMS_KNOWLEDGE_GRAPH_MAX_CLIENT_*` limits requires a new hardware benchmark.

## Qualification evidence (2026-07-28)

- Current 17,637-node / 31,283-edge snapshot: 2.36 seconds to interactive on
  the agreed hardware.
- Cold-cache delivery: 100 concurrent viewers, 200 64-KiB artifact requests,
  zero errors, p50 197 ms, p95 628 ms, p99 716 ms, 274 requests/second.
- Browser automation passed Cosmos load, rapid search updates, route-unmount
  GPU cleanup, and WebGL2-to-D3 fallback.
- Redis outage: `/health` and the last-ready manifest both remained HTTP 200;
  Redis and the worker recovered after restart.
- Active worker termination: the worker was killed while holding the build
  lock; the replacement claimed the abandoned job and activated a new ready
  snapshot.
- FalkorDB interruption and invalid artifact paths are covered by automated
  last-known-good and integrity tests.

Snapshot objects are immutable. Retain the current version and the most recent
failed build metadata for diagnosis. A scheduled retention operation may remove
older non-current objects only after confirming their database records are not
current; retention must never run against an unresolved prefix or bucket root.

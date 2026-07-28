const token = process.env.ECMS_E2E_TOKEN;
const baseUrl = process.env.ECMS_WEB_URL || 'http://localhost:3000';
const concurrency = Number(process.env.ECMS_LOAD_CONCURRENCY || 100);
const requestsPerWorker = Number(process.env.ECMS_LOAD_REQUESTS_PER_WORKER || 10);
if (!token) throw new Error('ECMS_E2E_TOKEN is required');

const headers = { Authorization: `Bearer ${token}` };
const manifestResponse = await fetch(`${baseUrl}/api/knowledge-graph/v2/manifest`, {
  headers,
});
if (!manifestResponse.ok) throw new Error(`Manifest failed: ${manifestResponse.status}`);
const manifest = await manifestResponse.json();
if (!manifest.snapshot) throw new Error('No ready snapshot');

const urls = [
  manifest.snapshot.points_url,
  manifest.snapshot.links_url,
];
const latencies = [];
let errors = 0;
let bytes = 0;
const failureDetails = [];

async function worker(workerIndex) {
  for (let index = 0; index < requestsPerWorker; index += 1) {
    const path = urls[(workerIndex + index) % urls.length];
    const started = performance.now();
    try {
      const target = new URL(path, baseUrl).toString();
      const sameOrigin = new URL(target).origin === new URL(baseUrl).origin;
      const signedArtifact = new URL(target).searchParams.has('X-Amz-Signature');
      const response = await fetch(target, {
        headers: {
          ...(sameOrigin && !signedArtifact ? headers : {}),
          Range: 'bytes=0-65535',
        },
      });
      const buffer = await response.arrayBuffer();
      latencies.push(performance.now() - started);
      bytes += buffer.byteLength;
      if (response.status !== 206 || buffer.byteLength === 0) {
        errors += 1;
        failureDetails.push({
          status: response.status,
          bytes: buffer.byteLength,
          body: new TextDecoder().decode(buffer).slice(0, 500),
          path,
        });
      }
    } catch (error) {
      latencies.push(performance.now() - started);
      errors += 1;
      failureDetails.push({
        error: error instanceof Error ? error.message : String(error),
        path,
      });
    }
  }
}

const started = performance.now();
await Promise.all(Array.from({ length: concurrency }, (_, index) => worker(index)));
const durationMs = performance.now() - started;
latencies.sort((left, right) => left - right);
const percentile = (value) => latencies[Math.min(
  latencies.length - 1,
  Math.floor(latencies.length * value),
)];
const total = concurrency * requestsPerWorker;
const result = {
  concurrency,
  totalRequests: total,
  errors,
  failureDetails: failureDetails.slice(0, 10),
  errorRate: errors / total,
  p50Ms: Math.round(percentile(0.5)),
  p95Ms: Math.round(percentile(0.95)),
  p99Ms: Math.round(percentile(0.99)),
  durationMs: Math.round(durationMs),
  throughputRequestsPerSecond: Math.round(total / (durationMs / 1000)),
  bytes,
  snapshotVersion: manifest.snapshot.version,
};
process.stdout.write(`${JSON.stringify(result)}\n`);
if (errors > 0) process.exitCode = 1;

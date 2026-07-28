# Knowledge Graph V2 — Phase 0 Benchmark

The validation renderer is deliberately available only when the frontend is opened through
`localhost` or `127.0.0.1`. The normal Administration Knowledge tab continues to use D3.

## Run the current D3 baseline

1. Open `http://localhost:3000/administration?knowledgeBenchmark=1`.
2. Open the **Knowledge** tab.
3. Do not interact for five seconds while the blue benchmark badge samples frames.
4. Download the JSON result from the badge.

## Run the WebGL proof against current data

1. Open `http://localhost:3000/administration?knowledgeRenderer=cosmos`.
2. Open the **Knowledge** tab.
3. Wait for the five-second sample and download its JSON.
4. Verify search, node selection, connected-node highlighting, pan, zoom, fit, pause, and reset-by-background-click.

## Run scale fixtures

Append one of the supported deterministic fixture sizes:

- `&knowledgeDataset=100000`
- `&knowledgeDataset=500000`
- `&knowledgeDataset=1000000`

Example:

`http://localhost:3000/administration?knowledgeRenderer=cosmos&knowledgeDataset=100000`

Run the fixtures in ascending order. Close and reopen the tab between runs so browser memory
release can be checked. Stop if the browser or GPU becomes unstable; a failed target is a valid
capacity result and should not be retried repeatedly on the same hardware.

## Captured fields

- Renderer and dataset node/edge counts
- Time until the renderer reports interactive
- Average animation-frame rate over five seconds
- Percentage of frames slower than 33.34 ms
- Current document element count
- JavaScript heap use when the browser exposes the non-standard memory API
- Browser user-agent and timestamp

The latest result is also exposed as `window.__ECMS_GRAPH_BENCHMARK__` for local automation.

## Gate

Do not begin snapshot-platform implementation until the current dataset is interactive within
five seconds and sustains at least 30 FPS on the agreed production client hardware. The
100k/500k/1M results establish the supported capacity; they are not assumed to pass.


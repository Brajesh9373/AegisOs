# How Nodes Are Created in the K-Graph

## The chain: 1 file → many nodes

### Step 1 — Git Provider creates 1 UKO per file

The Git provider walks the repository and emits a `UniversalKnowledgeObject` (UKO) for every matched file:

```
git:file:catchment:geography_app/api/village.py    (type=FILE)
```

Each UKO carries: the file content, metadata (source, timestamps, authors), and an empty relationships list at this stage.

### Step 2 — Pipeline Orchestrator runs `process_uko()`

The orchestrator runs four stages on every UKO. Each stage produces **derived UKOs** that become separate nodes:

| Stage | Engine | What it does | Example artifacts |
|-------|--------|-------------|-------------------|
| **Structural** | AST parser (Python), Markdown parser, JSON parser, SQL parser | Parses source code, extracts every function, class, import, heading, table, column | `function:get_village_details`, `import:fuzzywuzzy`, `class:VillageSchema` |
| **Semantic** | Keyword matcher (`DEFAULT_ONTOLOGY`) | Checks content against a keyword ontology (Authentication, Payment, REST API, Customer, etc.) | `concept:rest-api`, `concept:customer`, `concept:notification` |
| **Temporal** | Change tracker | Creates event nodes from `raw_data["events"]` (commits, status changes) | `event:commit`, `event:file-change` |
| **Identity** | Resolver (not yet wired in raw mode) | Cross-system entity deduplication (same person across Git/Jira/Slack) | Merged person node |

### Step 3 — Each artifact becomes an Episode → becomes a graph node

Every extracted UKO (original + derived) gets converted to an `EpisodePayload` via `uko_to_episode()` and stored in FalkorDB as a labelled `:Episode` node.

**Relationships are also written as edges:**

```
file ──[contained_in]── function
file ──[contained_in]── import
concept ──[extracted_from]── file
function ──[calls]── function_name
commit ──[modified]── file_path
event ──[changed]── target_entity
```

## Concrete example

One Python file `village.py` containing:

```python
import requests
from flask import jsonify

def get_village_details(id):
    return requests.get(f"/api/village/{id}")

class VillageService:
    def fetch_all(self):
        pass
```

Produces **these nodes**:

| Node ID | Type | Name |
|---------|------|------|
| `git:file:catchment:village.py` | FILE | `village.py` |
| `…:function:get_village_details:4` | FUNCTION | `get_village_details` |
| `…:class:VillageService:7` | CLASS | `VillageService` |
| `…:function:fetch_all:8` | FUNCTION | `fetch_all` |
| `…:import:requests:1` | IMPORT | `requests` |
| `…:import:flask.jsonify:2` | IMPORT | `flask.jsonify` |
| `concept:rest-api` (if keyword matched) | CONCEPT | `REST API` |

One file → **7+ nodes**.

Across 173 files → **8,535 nodes**.

## Why so many?

The system stores **evidence-layer** nodes — every real artifact found in the source. Each import statement, each function definition, each class is an independent node with edges linking it to its parent file and to other artifacts it interacts with.

The **knowledge-layer** (deduplication, identity resolution, concept merging) runs later. For example, if `import:requests` appears in 50 files, all 50 point to the same concept node rather than creating 50 duplicate entities. This layer requires identity resolution which currently needs an LLM to be fully operational.

## Node types in the graph

| Group | UKO Type | Source |
|-------|----------|--------|
| `episode` | FILE | Git file UKO |
| `commit` | COMMIT | Git commit history |
| `Function` | FUNCTION | Python AST parser |
| `Class` | CLASS | Python AST parser |
| `import` | IMPORT | Python AST parser |
| `Concept` | CONCEPT | Semantic keyword matcher or concept mapper |
| `Table` | TABLE | SQL parser or MySQL provider |
| `Column` | COLUMN | SQL parser or MySQL provider |
| `Document` | DOCUMENT | Markdown parser |
| `Ticket` | TICKET | Jira provider |
| `event` | EVENT | Temporal change tracker |

## Edge relationships

| Relationship | From | To | Meaning |
|-------------|------|----|---------|
| `contained_in` | function / class / import | file | Structural extraction: artifact lives in this file |
| `extracted_from` | concept | file / function | Semantic extraction: concept was derived from this artifact |
| `calls` | function | function / import | AST analysis: this function calls that function |
| `modified` | commit | file | Git history: this commit touched this file |
| `changed` | event | any entity | Temporal: this event affected this entity |

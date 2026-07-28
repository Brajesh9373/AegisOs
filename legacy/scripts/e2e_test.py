"""End-to-end test for knowledge graph reliability layers."""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0


def req(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


# 1. Health
print("\n--- 1. Health ---")
status, body = req("GET", "/health")
check("service healthy", status == 200 and body.get("status") == "ok", str(body))

status, body = req("GET", "/health/graph")
check("graph healthy", status == 200 and body.get("status") == "healthy", str(body))

# 2. Provider catalog
print("\n--- 2. Provider Catalog ---")
status, body = req("GET", "/providers")
check("providers list", status == 200 and len(body) == 5, f"got {len(body) if isinstance(body, list) else 'not list'}")

# 3. Manual UKO ingest (source + structural extraction)
print("\n--- 3. UKO Ingest (Structural Extraction) ---")
uko = {
    "type": "file",
    "name": "test_service.py",
    "content": 'class PaymentService:\n    def process_payment(self, token):\n        """Authenticate and charge."""\n        return token\n',
    "metadata": {
        "source": "git",
        "source_id": "e2e/test_service.py",
        "created_at": "2026-07-08T00:00:00+00:00",
        "modified_at": "2026-07-08T00:00:00+00:00",
    },
}
status, body = req("POST", "/ingest/uko", {"uko": uko, "persist": True})
check("ingest HTTP 200", status == 200, f"status={status}")
check("structural episodes returned", body.get("episode_count", 0) >= 2, f"got {body.get('episode_count', 0)} episodes")
check("write_success_count > 0", body.get("write_success_count", 0) > 0, f"success={body.get('write_success_count')}")
check("write_failure_count == 0", body.get("write_failure_count", 0) == 0, f"failures={body.get('write_failure_count')}")

# 4. Provenance on edges
print("\n--- 4. Provenance on Graph Data ---")
status, body = req("GET", "/graph/data?limit=50&min_confidence=0.0")
check("graph data loaded", status == 200 and body.get("node_count", 0) > 0, f"nodes={body.get('node_count')}")
edges_with_provenance = [e for e in body.get("edges", []) if e.get("extraction_method")]
check("edges have extraction_method", len(edges_with_provenance) > 0, f"found {len(edges_with_provenance)} edges with method")
if edges_with_provenance:
    print(f"    Sample edge: {edges_with_provenance[0].get('label')} extracted via {edges_with_provenance[0].get('extraction_method')} confidence={edges_with_provenance[0].get('confidence')}")

# 5. Confidence filtering
print("\n--- 5. Confidence Filtering ---")
status_no_filter, body_no_filter = req("GET", "/graph/data?limit=100")
status_filtered, body_filtered = req("GET", "/graph/data?limit=100&min_confidence=0.50")
total_edges = body_no_filter.get("edge_count", 0)
filtered_edges = body_filtered.get("edge_count", 0)
check("confidence filter reduces edges", filtered_edges <= total_edges, f"{total_edges} -> {filtered_edges}")

edges_high_conf = [e for e in body_no_filter.get("edges", []) if e.get("confidence") and e.get("confidence") >= 0.90]
if edges_high_conf:
    check("high-confidence edges exist (deterministic)", True)
    print(f"    High-confidence sample: {edges_high_conf[0].get('label')} conf={edges_high_conf[0].get('confidence')}")
else:
    check("high-confidence edges exist (deterministic)", False, "no edges with confidence >= 0.90")

# 6. Consistency Check
print("\n--- 6. Consistency Check ---")
status, body = req("GET", "/graph/consistency")
check("consistency endpoint", status == 200, f"status={status}")
check("total_nodes reported", body.get("total_nodes", 0) > 0, f"total={body.get('total_nodes')}")
print(f"    Orphans: {body.get('orphan_count', '?')}, Phantoms: {body.get('phantom_target_count', '?')}, Type mismatches: {body.get('type_mismatch_count', '?')}")

# 7. Provider sync with write stats
print("\n--- 7. Provider Sync (error propagation) ---")
status, body = req("POST", "/providers/mysql/sync", {
    "host": "nonexistent",
    "port": 3306,
    "user": "root",
    "password": "wrong",
    "database": "test",
    "connect_timeout": 2,
    "persist": False,
})
check("bad provider returns 400/500", status in (400, 500), f"status={status}")

# 8. Memory / GBrain
print("\n--- 8. Memory (GBrain) ---")
status, body = req("POST", "/memory/notes", {"topic": "e2e_test_note", "content": "Testing knowledge graph reliability end-to-end."})
check("memory write", status == 200, f"status={status}")

status, body = req("GET", "/memory/notes?q=reliability")
check("memory read", status == 200, f"status={status}")

# 9. Query (agent)
print("\n--- 9. Agent Query ---")
status, body = req("POST", "/query", {"question": "What payment services exist?", "session_id": "e2e-test"})
check("agent query", status == 200 and "answer" in body, f"status={status}")
print(f"    Answer: {body.get('answer', 'N/A')[:120]}")

# 10. Consistency repair
print("\n--- 10. Consistency Repair ---")
status, body = req("POST", "/graph/consistency/repair")
check("repair endpoint", status == 200, str(body))

# Summary
print(f"\n{'='*50}")
print(f"  Results: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")
print(f"{'='*50}")
sys.exit(0 if FAIL == 0 else 1)

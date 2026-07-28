import json, urllib.request, urllib.error, sys

BASE = "http://localhost:8000"

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

workspace = "navadhan-loan-platform"

print("=== 1. Create workspace ===")
s, b = req("POST", "/workspaces", {"workspace_id": workspace, "name": "Navadhan Loan Platform"})
print(f"  {s} {b}")

print("\n=== 2. Ingest Git repo (simulated) into workspace ===")
s, b = req("POST", "/ingest/uko", {
    "uko": {
        "type": "file",
        "name": "loan_service.py",
        "content": "class LoanService:\n    def calculate_emi(self, principal, rate, tenure):\n        return principal * rate / tenure\n",
        "metadata": {
            "source": "git",
            "source_id": f"{workspace}/loan_service.py",
            "created_at": "2026-07-08T00:00:00+00:00",
            "modified_at": "2026-07-08T00:00:00+00:00",
        },
    },
    "persist": True,
})
print(f"  Git ingest: {b.get('episode_count')} episodes, {b.get('write_success_count')} success")
git_names = b.get("episode_names", [])

print("\n=== 3. Ingest MySQL schema into SAME workspace ===")
s, b = req("POST", "/ingest/uko", {
    "uko": {
        "type": "table",
        "name": "loan_db",
        "content": "CREATE TABLE loans (\n  id INT PRIMARY KEY,\n  customer_id INT,\n  principal DECIMAL,\n  rate DECIMAL\n);\nCREATE TABLE accounts (\n  id INT PRIMARY KEY,\n  name VARCHAR(100)\n);",
        "metadata": {
            "source": "mysql",
            "source_id": f"{workspace}/schema",
            "created_at": "2026-07-08T00:00:00+00:00",
            "modified_at": "2026-07-08T00:00:00+00:00",
        },
    },
    "persist": True,
})
print(f"  MySQL ingest: {b.get('episode_count')} episodes, {b.get('write_success_count')} success")
mysql_names = b.get("episode_names", [])

print("\n=== 4. Verify workspace graph shows BOTH providers ===")
s, b = req("GET", f"/workspaces/{workspace}/graph")
print(f"  Nodes: {b['node_count']}, Edges: {b['edge_count']}")
types = {}
for n in b["nodes"]:
    t = n.get("type", "?")
    types[t] = types.get(t, 0) + 1
print(f"  Types: {types}")

edges = b["edges"]
ws_edges = [e for e in edges if e.get("label") == "part_of_workspace"]
print(f"  'part_of_workspace' edges: {len(ws_edges)}")

print("\n=== 5. Check main graph for cross-linking ===")
s, b = req("GET", f"/graph/data?limit=50")
print(f"  Main graph: {b['node_count']} nodes, {b['edge_count']} edges")
# Show sample edges with provenance
for e in b["edges"][:5]:
    print(f"  {e['label']:20s} conf={e.get('confidence','?')} method={e.get('extraction_method','?')}")

print("\n=== DONE ===")

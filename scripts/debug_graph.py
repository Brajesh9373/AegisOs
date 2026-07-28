import falkordb, sys
from legacy_ecms.config import get_settings

s = get_settings()
db = falkordb.FalkorDB(host=s.falkordb_host, port=s.falkordb_port)
g = db.select_graph(s.falkordb_database)

# Count edges
r = g.query("MATCH (u:UKO)-[r:RELATES]->(t:UKO) RETURN count(r)")
print(f"FalkorDB UKO-RELATES-UKO edges: {r.result_set[0][0]}")

# Fetch all and count
r2 = g.query("MATCH (u:UKO)-[r:RELATES]->(t:UKO) RETURN u.id, r.label, t.id")
rows = r2.result_set
print(f"Returned edge rows: {len(rows)}")

# Count nodes
r3 = g.query("MATCH (u:UKO) RETURN count(u)")
print(f"FalkorDB UKO nodes: {r3.result_set[0][0]}")
